"""Bagian halaman yang dipakai bersama (kepala, kaki, <head>) oleh semua
pembuat halaman, plus pembaca pengaturan dan berkas konten."""
import json
import re
from functools import lru_cache
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path
from urllib.parse import urlparse

import yaml

PROYEK = Path(__file__).resolve().parent.parent
SITUS = PROYEK / "site"
KONTEN = PROYEK / "konten"

WIB = timezone(timedelta(hours=7))
HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli",
         "Agustus", "September", "Oktober", "November", "Desember"]
FAVICON = ("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>"
           "<text y='.9em' font-size='90'>⚽</text></svg>")


@lru_cache(maxsize=None)
def pengaturan():
    p = json.loads((KONTEN / "pengaturan.json").read_text(encoding="utf-8"))
    p["alamat_website"] = p["alamat_website"].rstrip("/") + "/"
    p["jalur_dasar"] = urlparse(p["alamat_website"]).path or "/"  # mis. "/balbalan/"
    # Boleh ditempel utuh: <meta name="google-site-verification" content="KODE" />
    kode = str(p.get("google_verifikasi") or "").strip()
    m = re.search(r"""content=["']([^"']+)""", kode)
    p["google_verifikasi"] = m.group(1) if m else kode
    # Boleh ditulis "pub-123..." atau "ca-pub-123..."
    m = re.search(r"pub-(\d{10,20})", str(p.get("adsense_id") or ""))
    p["adsense_id"] = f"ca-pub-{m.group(1)}" if m else ""
    return p


def baca_konten(berkas):
    """Berkas .md dengan bagian depan YAML (--- ... ---) seperti yang ditulis Pages CMS."""
    teks = berkas.read_text(encoding="utf-8").lstrip("\ufeff")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", teks, re.S)
    if not m:
        return {}, teks
    return yaml.safe_load(m.group(1)) or {}, m.group(2)


def daftar_halaman_info():
    hasil = []
    for berkas in sorted((KONTEN / "halaman").glob("*.md")):
        data, isi = baca_konten(berkas)
        hasil.append({**data, "nama": berkas.stem, "isi": isi})
    return sorted(hasil, key=lambda h: (h.get("urutan") or 99, h["nama"]))


def tanggal_panjang(t, jam=True):
    teks = f"{HARI[t.weekday()]}, {t.day} {BULAN[t.month - 1]} {t.year}"
    return f"{teks}, {t:%H.%M} WIB" if jam else teks


def head_umum(akar):
    atur = pengaturan()
    tambahan = ""
    if atur["google_verifikasi"]:
        tambahan += f'\n  <meta name="google-site-verification" content="{escape(atur["google_verifikasi"])}">'
    if atur["adsense_id"]:
        tambahan += ('\n  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js'
                     f'?client={atur["adsense_id"]}" crossorigin="anonymous"></script>')
    return f"""<meta name="theme-color" content="#075a31">
  <link rel="icon" href="{FAVICON}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{akar}style.css">{tambahan}"""


def kepala(akar, aktif=None):
    def tautan(nama, href, label):
        tanda = ' aria-current="page"' if aktif == nama else ""
        return f'<a href="{href}"{tanda}>{label}</a>'
    return f"""<header class="kepala">
    <div class="wadah kepala-isi">
      <a class="logo" href="{akar}" aria-label="Balbalan, ke halaman utama"><span class="logo-bola" aria-hidden="true">⚽</span>Balbalan</a>
      <nav class="menu" aria-label="Menu utama">
        {tautan("berita", akar, "Berita")}
        {tautan("tulisan", f"{akar}tulisan/", "Tulisan")}
      </nav>
    </div>
  </header>"""


def kaki(akar, halaman_info=None):
    halaman_info = halaman_info if halaman_info is not None else daftar_halaman_info()
    menu = "".join(f'<a href="{akar}{h["nama"]}.html">{escape(h.get("judul") or h["nama"])}</a>' for h in halaman_info)
    tahun = datetime.now(WIB).year
    return f"""<footer class="kaki">
    <div class="wadah">
      <nav class="kaki-menu" aria-label="Informasi">{menu}</nav>
      <p>© {tahun} <strong>Balbalan</strong>. Berita dari media lain tetap milik media masing-masing dan selalu dicantumkan sumbernya; prediksi dan opini adalah tulisan Balbalan sendiri.</p>
    </div>
  </footer>"""


def dokumen(*, judul, deskripsi, akar, isi, aktif=None, kanonik=None, meta="", skrip="", halaman_info=None):
    kanonik_html = f'<link rel="canonical" href="{escape(kanonik)}">' if kanonik else ""
    return f"""<!doctype html>
<html lang="id">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(judul)}</title>
  <meta name="description" content="{escape(deskripsi)}">
  {kanonik_html}
  {meta}
  {head_umum(akar)}
</head>
<body>
  {kepala(akar, aktif)}

  <main class="wadah">
{isi}
  </main>

  {kaki(akar, halaman_info)}
{skrip}
</body>
</html>
"""


SKRIP_SALIN = """  <script>
    document.getElementById("salin")?.addEventListener("click", async (e) => {
      const t = e.currentTarget;
      try { await navigator.clipboard.writeText(t.dataset.alamat); t.textContent = "Tersalin ✓"; }
      catch { prompt("Salin tautan ini:", t.dataset.alamat); }
    });
  </script>"""
