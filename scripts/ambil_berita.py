"""Mengambil berita sepak bola terbaru dari RSS beberapa media dan menyimpannya
ke site/data/berita.json. Dijalankan otomatis oleh GitHub Actions setiap 3 jam.

Hanya memakai pustaka bawaan Python, jadi tidak perlu `pip install` apa pun.
"""
import html
import json
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

BERKAS = Path(__file__).resolve().parent.parent / "site" / "data" / "berita.json"
SIMPAN_HARI = 3      # berita lebih tua dari ini dibuang
MAKS_BERITA = 500    # batas jumlah berita di berkas
PANJANG_RINGKASAN = 220
UA = "Mozilla/5.0 (compatible; BalbalanBot/1.0; +https://github.com/bligobligo000-sudo/balbalan)"

# "link" (opsional) = pola alamat berita yang diterima. Dipakai untuk sumber yang
# RSS-nya bercampur olahraga lain, supaya yang masuk hanya berita sepak bola.
# CNN Indonesia sengaja tidak dipakai: RSS-nya menolak akses dari server GitHub (HTTP 403).
SUMBER = [
    {"nama": "detikSport", "url": "https://sport.detik.com/sepakbola/rss"},
    {"nama": "Liputan6", "url": "https://feed.liputan6.com/rss/bola"},
    {"nama": "VIVA", "url": "https://www.viva.co.id/get/bola", "link": r"viva\.co\.id/bola/"},
    {"nama": "iNews", "url": "https://www.inews.id/feed/sport", "link": r"/sport/soccer/"},
    {"nama": "SINDOnews", "url": "https://sports.sindonews.com/rss", "link": r"/read/\d+/11/"},
]

# Judul yang mengandung kata-kata ini dianggap bukan berita sepak bola.
BUKAN_BOLA = re.compile(
    r"\b(motogp|moto ?[23]|f1|formula ?[1e]|superbike|wsbk|pembalap|balapan|sirkuit|grand prix|"
    r"mandalika|aprilia|ducati|ktm|marquez|bagnaia|bezzecchi|bulu ?tangkis|badminton|bwf|"
    r"denmark open|all england|voli|proliga|tenis|basket|nba|ibl|golf|tinju|ufc|mma|renang|"
    r"atletik|catur|e-?sports?)\b",
    re.I,
)

# Kategori untuk tombol saring di website. Satu berita boleh masuk beberapa kategori.
KATEGORI = {
    "Timnas": r"timnas(?! (portugal|argentina|brasil|brazil|inggris|prancis|spanyol|jerman|italia|belanda|"
              r"belgia|jepang|korea|vietnam|thailand|malaysia|china|tiongkok|arab|australia|yordania|irak|"
              r"iran|filipina|singapura|myanmar|kamboja|laos|uzbekistan|qatar|amerika|meksiko|maroko|kroasia|"
              r"norwegia|swedia|denmark|polandia|turki|uruguay|kolombia|bahrain|kuwait|oman|india))|"
              r"garuda|pssi|skuad merah putih",
    "Liga Indonesia": r"liga indonesia|super league|liga 1|liga 2|persib|persija|persebaya|arema|psm|psis|psim|"
                      r"persik|persis solo|persita|persela|bali united|borneo|dewa united|madura united|"
                      r"malut united|semen padang|barito|bhayangkara|psbs|pss|jakmania|bobotoh|bonek|aremania",
    "Liga Inggris": r"liga inggris|premier league|man(chester)? (city|united|utd)|(?-i:MU)|setan merah|"
                    r"liverpool|arsenal|chelsea|tottenham|spurs|newcastle|aston villa|everton|west ham|"
                    r"brighton|crystal palace|fulham|brentford|wolves|bournemouth|nottingham forest",
    "Liga Spanyol": r"liga spanyol|la ?liga|real madrid|barcelona|barca|blaugrana|los blancos|atletico|"
                    r"sevilla|villarreal|real sociedad|real betis|girona|athletic bilbao|valencia",
    "Liga Italia": r"liga italia|serie a|juventus|juve|inter|milan|napoli|roma|lazio|atalanta|"
                   r"fiorentina|como|bologna|torino|cagliari|sassuolo|genoa|udinese|parma",
    "Liga Jerman": r"liga jerman|bundesliga|bayern|dortmund|leverkusen|leipzig|stuttgart|frankfurt|"
                   r"gladbach|monchengladbach",
    "Liga Champions": r"liga champions(?! asia)|ucl|liga europa|liga konferensi|uefa",
}
KATEGORI = {nama: re.compile(rf"\b({pola})\b", re.I) for nama, pola in KATEGORI.items()}

MEDIA = "{http://search.yahoo.com/mrss/}"
CONTENT = "{http://purl.org/rss/1.0/modules/content/}encoded"


def unduh(url):
    for percobaan in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001 - coba lagi untuk semua jenis gangguan jaringan
            if percobaan == 2:
                raise
            print(f"  gagal ({e}), coba lagi...")
            time.sleep(3)


def baca_xml(data):
    try:
        return ET.fromstring(data)
    except ET.ParseError:
        # Beberapa RSS memuat "&" telanjang yang membuat XML tidak sah.
        teks = data.decode("utf-8", "replace").lstrip("﻿ \r\n\t")
        teks = re.sub(r"&(?!#?\w+;)", "&amp;", teks)
        return ET.fromstring(teks.encode("utf-8"))


def bersihkan(teks):
    teks = re.sub(r"<[^>]+>", " ", teks or "")
    teks = html.unescape(html.unescape(teks.replace("-amp;", "&")))
    return re.sub(r"\s+", " ", teks).strip()


def potong(teks, n):
    if len(teks) <= n:
        return teks
    return teks[:n].rsplit(" ", 1)[0].rstrip(",.;:-") + "…"


def cari_gambar(item):
    kandidat = []
    for tag in (MEDIA + "content", MEDIA + "thumbnail"):
        for el in item.iter(tag):
            if el.get("medium", "image") == "image" and "video" not in el.get("type", ""):
                kandidat.append(el.get("url"))
    enc = item.find("enclosure")
    if enc is not None and enc.get("type", "image").startswith("image"):
        kandidat.append(enc.get("url"))
    kandidat.append(item.findtext("imglink"))
    for sumber in (item.findtext("description"), item.findtext(CONTENT)):
        m = re.search(r"<img[^>]+src=[\"']([^\"']+)", sumber or "")
        if m:
            kandidat.append(html.unescape(m.group(1)))
    for url in kandidat:
        if url and url.startswith("http"):
            url = url.strip().replace("http://", "https://", 1)
            # detik memberi gambar kecil (w=360); minta versi yang lebih tajam.
            return re.sub(r"([?&])w=360\b", r"\g<1>w=640", url)
    return None


def kategori_untuk(judul, ringkasan):
    teks = f"{judul} {ringkasan}"
    return [nama for nama, pola in KATEGORI.items() if pola.search(teks)]


def ambil_sumber(sumber, sekarang):
    akar = baca_xml(unduh(sumber["url"]))
    pola_link = re.compile(sumber["link"]) if "link" in sumber else None
    hasil = []
    for item in akar.iter("item"):
        judul = bersihkan(item.findtext("title"))
        link = (item.findtext("link") or "").strip()
        if not judul or not link.startswith("http"):
            continue
        if pola_link and not pola_link.search(link):
            continue
        if BUKAN_BOLA.search(judul):
            continue
        try:
            waktu = parsedate_to_datetime(item.findtext("pubDate")).astimezone(timezone.utc)
        except (TypeError, ValueError):
            waktu = sekarang
        hasil.append({
            "judul": judul,
            "link": link,
            "sumber": sumber["nama"],
            "waktu": min(waktu, sekarang).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "ringkasan": potong(bersihkan(item.findtext("description")), PANJANG_RINGKASAN),
            "gambar": cari_gambar(item),
        })
    return hasil


def kunci(link):
    return re.sub(r"[?#].*$", "", link).rstrip("/").lower()


def main():
    sekarang = datetime.now(timezone.utc).replace(microsecond=0)
    lama = []
    if BERKAS.exists():
        lama = json.loads(BERKAS.read_text(encoding="utf-8")).get("berita", [])

    gabungan = {kunci(b["link"]): b for b in lama}
    laporan = []
    for sumber in SUMBER:
        print(f"Mengambil {sumber['nama']}...")
        try:
            daftar = ambil_sumber(sumber, sekarang)
        except Exception as e:  # noqa: BLE001 - satu sumber gagal tidak boleh menghentikan yang lain
            print(f"  GAGAL: {e}")
            laporan.append({"nama": sumber["nama"], "ok": False, "jumlah": 0})
            continue
        print(f"  {len(daftar)} berita bola")
        laporan.append({"nama": sumber["nama"], "ok": True, "jumlah": len(daftar)})
        for b in daftar:
            gabungan[kunci(b["link"])] = b

    if not any(s["ok"] for s in laporan):
        sys.exit("Semua sumber gagal diambil; berkas lama tidak diubah.")

    batas = (sekarang - timedelta(days=SIMPAN_HARI)).strftime("%Y-%m-%dT%H:%M:%SZ")
    berita, judul_terlihat = [], set()
    for b in sorted(gabungan.values(), key=lambda b: b["waktu"], reverse=True):
        if b["waktu"] < batas or b["judul"].lower() in judul_terlihat:
            continue
        judul_terlihat.add(b["judul"].lower())
        b["kategori"] = kategori_untuk(b["judul"], b["ringkasan"])
        berita.append(b)
    berita = berita[:MAKS_BERITA]

    BERKAS.parent.mkdir(parents=True, exist_ok=True)
    BERKAS.write_text(json.dumps({
        "diperbarui": sekarang.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sumber": laporan,
        "berita": berita,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Tersimpan {len(berita)} berita ke {BERKAS}")


if __name__ == "__main__":
    main()
