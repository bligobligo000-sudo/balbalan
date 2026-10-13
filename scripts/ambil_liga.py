"""Mengambil jadwal, hasil pertandingan, dan klasemen, lalu menyimpannya ke
site/data/liga.json. Dijalankan otomatis oleh GitHub Actions setiap 3 jam.

Sumber data:
- Liga Indonesia: situs resmi liga, ileague.id (halaman jadwal & klasemen).
- Liga Inggris, Spanyol, Italia, Jerman, dan Liga Champions: football-data.org
  (gratis, perlu token di rahasia GitHub FOOTBALL_DATA_TOKEN). Tanpa token,
  bagian ini dilewati dan data lama dipertahankan.

Kalau satu sumber gagal, data lama kompetisi itu tetap dipakai.
"""
import html
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

BERKAS = Path(__file__).resolve().parent.parent / "site" / "data" / "liga.json"
UA = "Mozilla/5.0 (compatible; BalbalanBot/1.0; +https://github.com/bligobligo000-sudo/balbalan)"
WIB = timezone(timedelta(hours=7))
HARI_LALU = 45      # hasil pertandingan yang disimpan
HARI_DEPAN = 30     # jadwal yang disimpan

# Ganti nama ini setiap musim baru (lihat alamat halaman jadwal di ileague.id).
ILEAGUE_MUSIM = "BRI_SUPER_LEAGUE_2026-27"
ILEAGUE = "https://ileague.id"

KOMPETISI_EROPA = [
    # (kode football-data, slug, nama tampilan)
    ("PL", "liga-inggris", "Liga Inggris"),
    ("PD", "liga-spanyol", "Liga Spanyol"),
    ("SA", "liga-italia", "Liga Italia"),
    ("BL1", "liga-jerman", "Liga Jerman"),
    ("CL", "liga-champions", "Liga Champions"),
]

# Huruf kapital yang dipertahankan saat merapikan nama klub Indonesia.
KAPITAL = {"FC", "PSIM", "PSM", "PSS", "PSIS", "PSBS", "PSPS", "PSMS"}


def unduh(url, header=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(header or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def slug(teks):
    teks = unicodedata.normalize("NFKD", teks).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", teks.lower()).strip("-")


def iso(t):
    return t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def teks_bersih(potongan):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", potongan))).strip()


# ---------- Liga Indonesia (ileague.id) ----------

def nama_indonesia(nama_kapital):
    kata = []
    for k in nama_kapital.split():
        kata.append(k if k in KAPITAL else k.capitalize())
    nama = " ".join(kata)
    return re.sub(r" FC$", "", nama)  # "Bali United FC" -> "Bali United"


def tim_indonesia(semua_tim, nama_kapital, logo=None):
    # Klasemen menandai pengurangan poin di belakang nama, mis. "JAVA UNITED FC (-2)".
    nama = nama_indonesia(re.sub(r"\s*\(\s*-?\d+\s*\)\s*$", "", nama_kapital))
    tid = f"idn-{slug(nama)}"
    tim = semua_tim.setdefault(tid, {"nama": nama, "pendek": nama, "logo": None, "negara": "Indonesia"})
    if logo and not tim["logo"]:
        tim["logo"] = logo
    return tid


def laga_ileague(halaman, semua_tim):
    """Baca semua baris pertandingan dari satu halaman jadwal ileague.id."""
    hasil = []
    for m in re.finditer(r'<a\s+class="table-row"\s+href="([^"]*/result/detail/[^"]+)"\s*>(.*?)</table>', halaman, re.S):
        alamat, isi = m.group(1), m.group(2)
        tanggal = re.search(r"/(\d{4}-\d{2}-\d{2})/", alamat)
        sel = [c for c in re.findall(r"<td[^>]*>(.*?)</td>", isi, re.S)]
        logo = re.findall(r'<img src="([^"]+)"', isi)
        if not tanggal or len(sel) < 5:
            continue
        kandang = tim_indonesia(semua_tim, teks_bersih(sel[0]), logo[0] if logo else None)
        tamu = tim_indonesia(semua_tim, teks_bersih(sel[4]), logo[1] if len(logo) > 1 else None)
        lencana = teks_bersih(sel[2])
        stadion = teks_bersih(sel[5]) if len(sel) > 5 else ""
        jam = re.fullmatch(r"(\d{2}):(\d{2})", lencana)
        skor = re.search(r"(\d+)\s*:\s*(\d+)", lencana)
        waktu = datetime.strptime(tanggal.group(1), "%Y-%m-%d").replace(tzinfo=WIB)
        if jam:
            status, nilai = "jadwal", None
            waktu = waktu.replace(hour=int(jam.group(1)), minute=int(jam.group(2)))
        elif skor and lencana.upper().startswith("FT"):
            status, nilai = "selesai", [int(skor.group(1)), int(skor.group(2))]
        elif skor:
            status, nilai = "berlangsung", [int(skor.group(1)), int(skor.group(2))]
        else:
            status, nilai = "ditunda" if re.search(r"postpon|tunda|batal", lencana, re.I) else "jadwal", None
        hasil.append({
            "id": f"idn-{tanggal.group(1)}-{kandang}-{tamu}", "waktu": iso(waktu), "jam_pasti": bool(jam),
            "status": status, "kandang": kandang, "tamu": tamu, "skor": nilai, "stadion": stadion,
        })
    return hasil


def klasemen_ileague(halaman, semua_tim):
    baris = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", halaman, re.S):
        sel = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        if len(sel) < 10 or not teks_bersih(sel[0]).isdigit():
            continue
        logo = re.search(r'<img src="([^"]+)"', sel[1])
        nama = teks_bersih(sel[1])
        tid = tim_indonesia(semua_tim, nama, logo.group(1) if logo else None)
        potong = re.search(r"\(\s*-(\d+)\s*\)", nama)
        angka = [int(teks_bersih(c)) for c in sel[2:10]]
        bentuk = {"Win": "M", "Draw": "S", "Lose": "K"}
        form = [bentuk[x] for x in re.findall(r"<b>(Win|Draw|Lose)</b>", sel[10] if len(sel) > 10 else "")]
        baris.append({
            "posisi": int(teks_bersih(sel[0])), "tim": tid, "main": angka[0], "menang": angka[1], "seri": angka[2],
            "kalah": angka[3], "gm": angka[4], "gk": angka[5], "sg": angka[6], "poin": angka[7],
            "form": form[:5][::-1],  # dari yang terlama ke terbaru
            "potong_poin": int(potong.group(1)) if potong else 0,
        })
    return baris


def ambil_indonesia(semua_tim):
    dasar = f"{ILEAGUE}/fixtures/index/{ILEAGUE_MUSIM}"
    utama = unduh(f"{dasar}?lang=en").decode("utf-8", "replace")
    laga = laga_ileague(utama, semua_tim)
    pekan = sorted({int(n) for n in re.findall(rf"fixtures/index/{re.escape(ILEAGUE_MUSIM)}/(\d+)", utama)})
    if len(pekan) == 3:
        sekarang = pekan[1]  # halaman utama = pekan berjalan, diapit tautan pekan sebelum & sesudahnya
        for p in [*range(sekarang - 5, sekarang), sekarang + 1, sekarang + 2]:
            if p < 0:
                continue
            time.sleep(2)
            try:
                laga += laga_ileague(unduh(f"{dasar}/{p}?lang=en").decode("utf-8", "replace"), semua_tim)
            except Exception as e:  # noqa: BLE001 - pekan lain tetap dipakai
                print(f"  pekan {p} gagal: {e}")
    time.sleep(2)
    tabel = klasemen_ileague(unduh(f"{ILEAGUE}/table/index/{ILEAGUE_MUSIM}?lang=en").decode("utf-8", "replace"), semua_tim)
    if not laga or not tabel:
        raise RuntimeError(f"data kosong (laga={len(laga)}, klasemen={len(tabel)}); mungkin tampilan ileague.id berubah")
    unik = {m["id"]: m for m in laga}
    musim = ILEAGUE_MUSIM.split("_")[-1].replace("-", "/")
    return {"slug": "liga-indonesia", "nama": "Liga Indonesia", "nama_resmi": f"BRI Super League {musim}",
            "sumber": "I.League (ileague.id)", "sumber_url": f"{ILEAGUE}/table/index/{ILEAGUE_MUSIM}",
            "klasemen": tabel, "laga": list(unik.values())}


# ---------- Liga Eropa (football-data.org) ----------

def tim_eropa(semua_tim, t):
    tid = f"fd-{t['id']}"
    if tid not in semua_tim:
        semua_tim[tid] = {"nama": t.get("name") or t.get("shortName") or "?", "pendek": t.get("shortName") or t.get("name"),
                          "logo": t.get("crest"), "negara": None}
    return tid


def ambil_eropa(kode, slug_liga, nama, token, semua_tim):
    header = {"X-Auth-Token": token}
    dasar = "https://api.football-data.org/v4/competitions"
    data_tabel = json.loads(unduh(f"{dasar}/{kode}/standings", header))
    time.sleep(7)  # batas gratis: 10 permintaan per menit
    hari_ini = datetime.now(timezone.utc).date()
    rentang = f"dateFrom={hari_ini - timedelta(days=HARI_LALU)}&dateTo={hari_ini + timedelta(days=HARI_DEPAN)}"
    try:
        data_laga = json.loads(unduh(f"{dasar}/{kode}/matches?{rentang}", header))
    except urllib.error.HTTPError as e:
        if e.code != 400:
            raise
        data_laga = json.loads(unduh(f"{dasar}/{kode}/matches", header))  # rentang tanggal ditolak: ambil semua
    time.sleep(7)

    tabel = []
    total = [s for s in data_tabel.get("standings", []) if s.get("type") == "TOTAL"]
    for s in total:
        for r in s["table"]:
            bentuk = {"W": "M", "D": "S", "L": "K"}
            form = [bentuk[x] for x in (r.get("form") or "").replace(" ", "").split(",") if x in bentuk]
            tabel.append({
                "posisi": r["position"], "tim": tim_eropa(semua_tim, r["team"]), "main": r["playedGames"],
                "menang": r["won"], "seri": r["draw"], "kalah": r["lost"], "gm": r["goalsFor"],
                "gk": r["goalsAgainst"], "sg": r["goalDifference"], "poin": r["points"], "form": form[-5:],
                "grup": s.get("group"),
            })

    status_map = {"FINISHED": "selesai", "IN_PLAY": "berlangsung", "PAUSED": "berlangsung", "LIVE": "berlangsung",
                  "POSTPONED": "ditunda", "SUSPENDED": "ditunda", "CANCELLED": "batal"}
    laga = []
    for m in data_laga.get("matches", []):
        if not m["homeTeam"].get("id") or not m["awayTeam"].get("id"):
            continue  # lawan belum ditentukan (babak gugur)
        ft = (m.get("score") or {}).get("fullTime") or {}
        status = status_map.get(m["status"], "jadwal")
        laga.append({
            "id": f"fd-{m['id']}", "waktu": m["utcDate"], "jam_pasti": m["status"] != "SCHEDULED",
            "status": status, "kandang": tim_eropa(semua_tim, m["homeTeam"]), "tamu": tim_eropa(semua_tim, m["awayTeam"]),
            "skor": [ft["home"], ft["away"]] if ft.get("home") is not None else None,
            "stadion": m.get("venue") or "", "pekan": m.get("matchday"),
        })
    musim = data_tabel.get("season", {})
    tahun = f"{musim.get('startDate', '')[:4]}/{musim.get('endDate', '')[2:4]}" if musim.get("startDate") else ""
    return {"slug": slug_liga, "nama": nama, "nama_resmi": f"{data_tabel['competition']['name']} {tahun}".strip(),
            "sumber": "football-data.org", "sumber_url": "https://www.football-data.org",
            "klasemen": tabel, "laga": laga}


# ---------- Utama ----------

def rapikan(kompetisi, sekarang):
    """Simpan hanya laga dalam rentang yang dipakai website, urut waktu."""
    awal, akhir = iso(sekarang - timedelta(days=HARI_LALU)), iso(sekarang + timedelta(days=HARI_DEPAN))
    kompetisi["laga"] = sorted((m for m in kompetisi["laga"] if awal <= m["waktu"] <= akhir), key=lambda m: m["waktu"])
    return kompetisi


def main():
    sekarang = datetime.now(timezone.utc).replace(microsecond=0)
    lama = json.loads(BERKAS.read_text(encoding="utf-8")) if BERKAS.exists() else {"kompetisi": [], "tim": {}}
    kompetisi_lama = {k["slug"]: k for k in lama.get("kompetisi", [])}
    semua_tim = dict(lama.get("tim", {}))
    hasil, laporan = {}, []

    print("Mengambil Liga Indonesia (ileague.id)...")
    try:
        hasil["liga-indonesia"] = ambil_indonesia(semua_tim)
        k = hasil["liga-indonesia"]
        laporan.append(("Liga Indonesia", True))
        print(f"  {len(k['laga'])} laga, {len(k['klasemen'])} tim di klasemen")
    except Exception as e:  # noqa: BLE001
        print(f"  GAGAL: {e}")
        laporan.append(("Liga Indonesia", False))

    token = os.environ.get("FOOTBALL_DATA_TOKEN", "").strip()
    if not token:
        print("Liga Eropa dilewati: token FOOTBALL_DATA_TOKEN belum diisi.")
    for kode, slug_liga, nama in KOMPETISI_EROPA if token else []:
        print(f"Mengambil {nama} (football-data.org)...")
        try:
            hasil[slug_liga] = ambil_eropa(kode, slug_liga, nama, token, semua_tim)
            k = hasil[slug_liga]
            laporan.append((nama, True))
            print(f"  {len(k['laga'])} laga, {len(k['klasemen'])} baris klasemen")
        except Exception as e:  # noqa: BLE001
            print(f"  GAGAL: {e}")
            laporan.append((nama, False))

    if not hasil and not kompetisi_lama:
        sys.exit("Belum ada data liga sama sekali.")

    urutan = ["liga-indonesia"] + [s for _, s, _ in KOMPETISI_EROPA]
    kompetisi = []
    for s in urutan:
        k = hasil.get(s) or kompetisi_lama.get(s)
        if k:
            kompetisi.append(rapikan(k, sekarang))
    dipakai = {m[x] for k in kompetisi for m in k["laga"] for x in ("kandang", "tamu")} | {r["tim"] for k in kompetisi for r in k["klasemen"]}
    BERKAS.parent.mkdir(parents=True, exist_ok=True)
    BERKAS.write_text(json.dumps({
        "diperbarui": iso(sekarang),
        "kompetisi": kompetisi,
        "tim": {tid: semua_tim[tid] for tid in sorted(dipakai) if tid in semua_tim},
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Tersimpan {len(kompetisi)} kompetisi ke {BERKAS}")


if __name__ == "__main__":
    main()
