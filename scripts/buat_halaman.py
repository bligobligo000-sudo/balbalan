"""Membuat satu halaman baca (site/baca/<id>.html) untuk setiap berita di
site/data/berita.json, lengkap dengan berita terkait. Dijalankan oleh GitHub
Actions sebelum website dipasang, jadi folder site/baca tidak perlu disimpan di git.

Halaman baca hanya berisi judul, ringkasan dan foto dari media, plus tombol ke
artikel aslinya. Isi artikel lengkap tetap dibaca di situs media.
"""
import json
import math
import re
import shutil
from collections import Counter
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path
from urllib.parse import quote

AKAR = Path(__file__).resolve().parent.parent / "site"
ALAMAT = "https://bligobligo000-sudo.github.io/balbalan/"
WIB = timezone(timedelta(hours=7))
HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli",
         "Agustus", "September", "Oktober", "November", "Desember"]
JUMLAH_TERKAIT = 6
JUMLAH_TERBARU = 6

# Kata umum yang tidak membantu menentukan apakah dua berita membahas hal yang sama.
KATA_UMUM = set("""
yang dan di ke dari untuk dengan ini itu ada pada akan tak tidak usai jelang vs lawan saat bisa
jadi kata soal tim laga main lagi sudah masih hingga atau juga baru bakal dalam the karena oleh
agar demi para sang bikin buat makin lebih sebut ingin punya dapat kini mau tetap hari pekan
musim berita jadwal hasil prediksi klasemen live link nonton siaran tayang top cara siapa apa
begini ini fakta momen resmi terbaru terkini kabar update bola sepak pemain pelatih klub
terakhir selama peluang ungkap tahun start nasib media asing sebut kalah menang gol juara bek
kiper gelandang penyerang striker bintang hal takjub tinggal lolos sempurna rekor buruk baik besar
pertama kedua ketiga dua tiga empat lima enam satu banyak semua tanpa bersama setelah sebelum
alasan respons reaksi kritik tegas kalahkan bantai hajar tumbang imbang skor babak final tanding
duel kembali akhirnya bukan hanya cuma sempat terus belum segera langsung harus wajib perlu siap
akui bilang tegaskan minta beber bongkar tantang hadapi jamu tamu kandang tandang liga kontra
inilah daftar link gratis malam pagi sore dini wib singgung soroti incar bidik rumor kabarnya
""".split())

FAVICON = ("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>"
           "<text y='.9em' font-size='90'>⚽</text></svg>")


def waktu_wib(iso):
    return datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).astimezone(WIB)


def tanggal_panjang(iso):
    t = waktu_wib(iso)
    return f"{HARI[t.weekday()]}, {t.day} {BULAN[t.month - 1]} {t.year}, {t:%H.%M} WIB"


def tanggal_pendek(iso):
    t = waktu_wib(iso)
    return f"{t.day} {BULAN[t.month - 1][:3]}, {t:%H.%M} WIB"


def slug(teks):
    return re.sub(r"\s+", "-", teks.lower())


def kata_kunci(judul):
    # Singkatan dua huruf kapital (MU, AC) tetap dihitung; angka diabaikan.
    return {k.lower() for k in re.findall(r"[A-Za-z0-9]+", judul)
            if not k.isdigit() and (len(k) >= 3 or (len(k) == 2 and k.isupper())) and k.lower() not in KATA_UMUM}


def cari_terkait(berita):
    """Untuk tiap berita, cari berita lain yang judulnya berbagi kata penting (nama klub, pemain...)."""
    kata = {b["id"]: kata_kunci(b["judul"]) for b in berita}
    df = Counter(k for ks in kata.values() for k in ks)
    n = len(berita)
    bobot = {k: math.log(n / d) for k, d in df.items()}
    hasil = {}
    for a in berita:
        skor = []
        for b in berita:
            if b is a:
                continue
            sama = kata[a["id"]] & kata[b["id"]]
            nilai = sum(bobot[k] for k in sama)
            if len(sama) >= 2 and nilai >= 5:
                skor.append((nilai, b["waktu"], b))
        skor.sort(key=lambda s: (s[0], s[1]), reverse=True)
        hasil[a["id"]] = [b for _, _, b in skor[:JUMLAH_TERKAIT]]
    return hasil


def gambar_html(src, alt="", besar=False):
    if not src:
        return '<div class="gambar kosong"></div>'
    muat = "eager" if besar else "lazy"
    return (f'<div class="gambar"><img src="{escape(src)}" alt="{escape(alt)}" loading="{muat}" '
            f'referrerpolicy="no-referrer" onerror="this.parentNode.classList.add(\'kosong\');this.remove()"></div>')


def kartu_html(b):
    return (f'<a class="kartu" href="{b["id"]}.html">{gambar_html(b.get("gambar"))}'
            f'<div class="teks"><div class="info"><span class="sumber">{escape(b["sumber"])}</span>'
            f'<span class="titik"></span><time datetime="{b["waktu"]}">{tanggal_pendek(b["waktu"])}</time></div>'
            f'<h4>{escape(b["judul"])}</h4><p>{escape(b["ringkasan"])}</p></div></a>')


def halaman_html(b, terkait, terbaru):
    alamat = f"{ALAMAT}baca/{b['id']}.html"
    foto = b.get("gambar_besar") or b.get("gambar")
    judul, sumber = escape(b["judul"]), escape(b["sumber"])
    penulis = escape(b["penulis"]) if b.get("penulis") else None
    wa = "https://wa.me/?text=" + quote(f"{b['judul']}\n{alamat}")
    jejak = "".join(f' <span>›</span> <a href="../#{slug(k)}">{escape(k)}</a>' for k in b["kategori"][:1])
    info = f'<span class="sumber">{sumber}</span>'
    if penulis:
        info += f'<span class="titik"></span><span>{penulis}</span>'
    info += f'<span class="titik"></span><time datetime="{b["waktu"]}">{tanggal_panjang(b["waktu"])}</time>'

    bagian = ""
    if terkait:
        bagian += f'<section class="bagian"><h2>Berita terkait</h2><div class="grid">{"".join(map(kartu_html, terkait))}</div></section>'
    bagian += f'<section class="bagian"><h2>Terbaru di Balbalan</h2><div class="grid">{"".join(map(kartu_html, terbaru))}</div></section>'

    kredit = f"Judul, ringkasan, dan foto berita ini milik {sumber}"
    kredit += f" (penulis: {penulis})." if penulis else "."

    return f"""<!doctype html>
<html lang="id">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{judul} — Balbalan</title>
  <meta name="description" content="{escape(b['ringkasan'])}">
  <link rel="canonical" href="{escape(b['link'])}">
  <meta property="og:title" content="{judul}">
  <meta property="og:description" content="{escape(b['ringkasan'])}">
  <meta property="og:url" content="{alamat}">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="Balbalan">
  {f'<meta property="og:image" content="{escape(foto)}">' if foto else ''}
  <meta name="twitter:card" content="summary_large_image">
  <meta name="theme-color" content="#075a31">
  <link rel="icon" href="{FAVICON}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../style.css">
</head>
<body>
  <header class="kepala">
    <div class="wadah kepala-isi">
      <a class="logo" href="../" aria-label="Balbalan, ke halaman utama"><span class="logo-bola" aria-hidden="true">⚽</span>Balbalan</a>
      <a class="kembali" href="../">← Semua berita</a>
    </div>
  </header>

  <main class="wadah">
    <article class="artikel">
      <nav class="jejak" aria-label="Lokasi halaman"><a href="../">Beranda</a>{jejak}</nav>
      <h1>{judul}</h1>
      <div class="info">{info}</div>
      <figure class="foto">{gambar_html(foto, b['judul'], besar=True)}<figcaption>Foto: {sumber}</figcaption></figure>
      <p class="ringkasan">{escape(b['ringkasan'])}</p>
      <a class="tombol-baca" href="{escape(b['link'])}" target="_blank" rel="noopener">Baca selengkapnya di {sumber} <span aria-hidden="true">↗</span></a>
      <div class="bagikan">
        <span>Bagikan:</span>
        <a class="tombol-kecil wa" href="{escape(wa)}" target="_blank" rel="noopener">WhatsApp</a>
        <button class="tombol-kecil" type="button" id="salin" data-alamat="{alamat}">Salin tautan</button>
      </div>
    </article>
    {bagian}
    <p class="kredit">{kredit} Balbalan hanya menampilkan cuplikan; artikel lengkapnya ada di <a href="{escape(b['link'])}" target="_blank" rel="noopener">situs {sumber}</a>.</p>
  </main>

  <footer class="kaki">
    <div class="wadah"><p><a href="../"><strong>Balbalan</strong></a> · Berita bola terbaru dari media Indonesia, diperbarui otomatis setiap 3 jam.</p></div>
  </footer>

  <script>
    document.getElementById("salin").addEventListener("click", async (e) => {{
      const t = e.currentTarget;
      try {{ await navigator.clipboard.writeText(t.dataset.alamat); t.textContent = "Tersalin ✓"; }}
      catch {{ prompt("Salin tautan ini:", t.dataset.alamat); }}
    }});
  </script>
</body>
</html>
"""


def main():
    data = json.loads((AKAR / "data" / "berita.json").read_text(encoding="utf-8"))
    berita = data["berita"]
    terkait = cari_terkait(berita)

    folder = AKAR / "baca"
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir(parents=True)
    for b in berita:
        terbaru = [x for x in berita if x is not b and x not in terkait[b["id"]]][:JUMLAH_TERBARU]
        (folder / f"{b['id']}.html").write_text(halaman_html(b, terkait[b["id"]], terbaru), encoding="utf-8")
    punya = sum(1 for v in terkait.values() if v)
    print(f"Dibuat {len(berita)} halaman baca ({punya} punya berita terkait) di {folder}")


if __name__ == "__main__":
    main()
