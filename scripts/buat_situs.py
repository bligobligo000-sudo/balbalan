"""Membangun semua halaman website sebelum dipasang (dijalankan oleh GitHub Actions):

- site/index.html          beranda, dari templat/beranda.html
- site/tulisan/...         tulisan sendiri, dari konten/tulisan/*.md (ditulis lewat Pages CMS)
- site/<nama>.html         halaman info (Tentang, Kontak, ...), dari konten/halaman/*.md
- site/baca/...            halaman baca berita (lewat buat_halaman.py)
- site/404.html dan site/sitemap.xml

Pemakaian:
    python scripts/buat_situs.py           tulisan draf tidak ikut
    python scripts/buat_situs.py --draf    pratinjau: draf dan tulisan terjadwal ikut tampil
"""
import json
import math
import re
import shutil
import sys
from collections import Counter
from datetime import date, datetime
from html import escape
from urllib.parse import quote

import buat_halaman
from tata_letak import (BULAN, KONTEN, PROYEK, SITUS, SKRIP_SALIN, WIB, baca_konten, daftar_halaman_info,
                        dokumen, head_umum, kaki, kepala, pengaturan, tanggal_panjang)

JENIS = ["Prediksi", "Opini", "Analisis", "Catatan"]


# ---------- Isi tulisan ----------

def inline_md(teks):
    teks = escape(teks, quote=False)
    teks = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)", r'<img src="\2" alt="\1">', teks)
    teks = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', teks)
    teks = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", teks)
    return re.sub(r"(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?![*\w])", r"<em>\1</em>", teks)


def markdown_sederhana(teks):
    """Cukup untuk tulisan yang diketik manual: judul (#), daftar (- / 1.), kutipan (>), tebal, miring, tautan, gambar."""
    html = []
    for blok in re.split(r"\n\s*\n", teks.strip()):
        baris = [b.rstrip() for b in blok.strip().splitlines()]
        if m := re.match(r"^(#{1,6})\s+(.*)", baris[0]):
            level = max(2, len(m.group(1)))  # h1 dipakai judul tulisan
            html.append(f"<h{level}>{inline_md(m.group(2))}</h{level}>")
            baris = baris[1:]
            if not baris:
                continue
        if all(re.match(r"^\s*[-*]\s+", b) for b in baris):
            html.append("<ul>" + "".join(f"<li>{inline_md(re.sub(r'^\s*[-*]\s+', '', b))}</li>" for b in baris) + "</ul>")
        elif all(re.match(r"^\s*\d+[.)]\s+", b) for b in baris):
            html.append("<ol>" + "".join(f"<li>{inline_md(re.sub(r'^\s*\d+[.)]\s+', '', b))}</li>" for b in baris) + "</ol>")
        elif all(b.startswith(">") for b in baris):
            html.append(f"<blockquote><p>{inline_md(' '.join(b.lstrip('> ') for b in baris))}</p></blockquote>")
        else:
            html.append(f"<p>{'<br>'.join(inline_md(b) for b in baris)}</p>")
    return "\n".join(html)


def isi_ke_html(isi):
    # Pages CMS menyimpan isi tulisan sebagai HTML; tulisan yang diketik manual boleh Markdown.
    if re.search(r"<(p|h[1-6]|ul|ol|div|blockquote|img|figure|table)\b", isi, re.I):
        return isi
    return markdown_sederhana(isi)


def perbaiki_gambar(html, akar):
    """Gambar unggahan Pages CMS ditulis sebagai /gambar/...; ubah jadi jalur relatif supaya
    tetap jalan di alamat github.io/balbalan maupun di domain sendiri."""
    return re.sub(r'(src|href)="/gambar/', rf'\1="{akar}gambar/', html)


def jalur_gambar(nilai, akar):
    if not nilai:
        return None
    nilai = str(nilai).strip()
    if nilai.startswith("/gambar/"):
        return akar + nilai[1:]
    return nilai if nilai.startswith(("http://", "https://")) else None


def ke_tanggal(nilai, cadangan=None):
    if isinstance(nilai, datetime):
        return nilai.date()
    if isinstance(nilai, date):
        return nilai
    try:
        return date.fromisoformat(str(nilai)[:10])
    except ValueError:
        return cadangan


def ke_waktu(nilai):
    if isinstance(nilai, datetime):
        return nilai
    try:
        return datetime.strptime(str(nilai).strip()[:16].replace("T", " "), "%Y-%m-%d %H:%M")
    except ValueError:
        return None


def tanggal_singkat(t):
    return f"{t.day} {BULAN[t.month - 1][:3]} {t.year}"


def muat_tulisan(dengan_draf):
    hari_ini = datetime.now(WIB).date()
    hasil, slug_terpakai = [], set()
    for berkas in sorted((KONTEN / "tulisan").glob("*.md")):
        data, isi = baca_konten(berkas)
        if not data.get("judul"):
            print(f"  dilewati (tanpa judul): {berkas.name}")
            continue
        dari_nama = ke_tanggal(berkas.stem[:10])
        tanggal = ke_tanggal(data.get("tanggal"), dari_nama) or hari_ini
        if not dengan_draf and (data.get("draf") or tanggal > hari_ini):
            continue  # draf, atau dijadwalkan terbit nanti
        slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", berkas.stem)
        slug = re.sub(r"[^a-z0-9-]+", "-", slug.lower()).strip("-") or berkas.stem
        if slug in slug_terpakai:
            slug = re.sub(r"[^a-z0-9-]+", "-", berkas.stem.lower())
        slug_terpakai.add(slug)
        html = isi_ke_html(isi)
        kata = len(re.sub(r"<[^>]+>", " ", html).split())
        laga = data.get("pertandingan") or {}
        jenis = data.get("jenis") if data.get("jenis") in JENIS else "Catatan"
        hasil.append({
            "slug": slug, "judul": str(data["judul"]).strip(), "jenis": jenis, "tanggal": tanggal,
            "ringkasan": str(data.get("ringkasan") or "").strip(), "gambar": data.get("gambar"),
            "kredit_gambar": str(data.get("kredit_gambar") or "").strip(), "isi": html,
            "menit_baca": max(1, round(kata / 200)), "kata": kata, "draf": bool(data.get("draf")),
            "laga": {k: str(laga.get(k) or "").strip() for k in ("kompetisi", "kandang", "tamu", "jadwal", "skor")},
        })
    return sorted(hasil, key=lambda t: (t["tanggal"], t["slug"]), reverse=True)


# ---------- Potongan HTML ----------

def kartu_tulisan(t, akar_tulisan, akar):
    sampul = jalur_gambar(t["gambar"], akar)
    laga = t["laga"]
    if sampul:
        gambar = buat_halaman.gambar_html(sampul, t["judul"])
    else:
        teks = f"{laga['kandang']} vs {laga['tamu']}" if laga["kandang"] and laga["tamu"] else t["jenis"]
        gambar = f'<div class="gambar sampul-teks"><span>{escape(teks)}</span></div>'
    return (f'<a class="kartu kartu-tulisan" href="{akar_tulisan}{t["slug"]}.html" data-jenis="{t["jenis"]}">{gambar}'
            f'<div class="teks"><div class="info"><span class="lencana">{escape(t["jenis"])}</span>'
            f'<time datetime="{t["tanggal"].isoformat()}">{tanggal_singkat(t["tanggal"])}</time>'
            f'{"<span>· draf</span>" if t["draf"] else ""}</div>'
            f'<h4>{escape(t["judul"])}</h4><p>{escape(t["ringkasan"])}</p></div></a>')


def kotak_laga(laga):
    if not (laga["kandang"] and laga["tamu"]):
        return ""
    atas = [escape(laga["kompetisi"])] if laga["kompetisi"] else []
    if waktu := ke_waktu(laga["jadwal"]):
        atas.append(tanggal_panjang(waktu))
    skor = escape(laga["skor"]).replace("-", " – ") if laga["skor"] else "vs"
    return f"""<div class="laga">
        {f'<div class="laga-atas">{" · ".join(atas)}</div>' if atas else ''}
        <div class="laga-tim"><span class="tim">{escape(laga['kandang'])}</span><span class="skor">{skor}</span><span class="tim">{escape(laga['tamu'])}</span></div>
        {'<div class="laga-bawah">Prediksi skor Balbalan</div>' if laga['skor'] else ''}
      </div>"""


def berita_untuk(t, berita):
    """Berita yang berkaitan dengan tulisan (berbagi nama klub/pemain), atau berita terbaru."""
    if not berita:
        return [], "Berita terbaru"
    kata = buat_halaman.kata_kunci(f"{t['judul']} {t['laga']['kandang']} {t['laga']['tamu']}")
    df = Counter(k for b in berita for k in buat_halaman.kata_kunci(b["judul"]))
    skor = []
    for b in berita:
        sama = kata & buat_halaman.kata_kunci(b["judul"])
        if len(sama) >= 2:
            skor.append((sum(math.log(len(berita) / df[k]) for k in sama), b["waktu"], b))
    skor.sort(key=lambda s: (s[0], s[1]), reverse=True)
    if len(skor) >= 3:
        return [b for _, _, b in skor[:6]], "Berita terkait"
    return berita[:6], "Berita terbaru"


def halaman_tulisan(t, semua, berita, atur, info):
    alamat = f"{atur['alamat_website']}tulisan/{t['slug']}.html"
    sampul = jalur_gambar(t["gambar"], "../")
    sampul_mutlak = jalur_gambar(t["gambar"], atur["alamat_website"])
    judul = escape(t["judul"])
    wa = "https://wa.me/?text=" + quote(f"{t['judul']}\n{alamat}")
    foto = ""
    if sampul:
        keterangan = f"<figcaption>{escape(t['kredit_gambar'])}</figcaption>" if t["kredit_gambar"] else ""
        foto = f'<figure class="foto">{buat_halaman.gambar_html(sampul, t["judul"], besar=True)}{keterangan}</figure>'

    lainnya = [x for x in semua if x is not t][:3]
    bagian = ""
    if lainnya:
        bagian += f'<section class="bagian"><h2>Tulisan lainnya</h2><div class="grid">{"".join(kartu_tulisan(x, "", "../") for x in lainnya)}</div></section>'
    daftar_berita, judul_berita = berita_untuk(t, berita)
    if daftar_berita:
        bagian += (f'<section class="bagian"><h2>{judul_berita}</h2><div class="grid">'
                   f'{"".join(buat_halaman.kartu_html(b, "../baca/") for b in daftar_berita)}</div></section>')

    data_terstruktur = {
        "@context": "https://schema.org", "@type": "BlogPosting", "headline": t["judul"],
        "description": t["ringkasan"], "datePublished": t["tanggal"].isoformat(),
        "dateModified": t["tanggal"].isoformat(), "mainEntityOfPage": alamat,
        "author": {"@type": "Person", "name": atur["penulis"], "url": f"{atur['alamat_website']}tentang.html"},
        "publisher": {"@type": "Organization", "name": atur["nama_website"], "url": atur["alamat_website"]},
    }
    if sampul_mutlak:
        data_terstruktur["image"] = [sampul_mutlak]
    meta = f"""<meta property="og:title" content="{judul}">
  <meta property="og:description" content="{escape(t['ringkasan'])}">
  <meta property="og:url" content="{alamat}">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="{escape(atur['nama_website'])}">
  {f'<meta property="og:image" content="{escape(sampul_mutlak)}">' if sampul_mutlak else ''}
  <meta name="twitter:card" content="{'summary_large_image' if sampul_mutlak else 'summary'}">
  <meta property="article:published_time" content="{t['tanggal'].isoformat()}">
  {'<meta name="robots" content="noindex">' if t['draf'] else ''}
  <script type="application/ld+json">{json.dumps(data_terstruktur, ensure_ascii=False)}</script>"""

    isi = f"""    <article class="artikel">
      <nav class="jejak" aria-label="Lokasi halaman"><a href="../">Beranda</a> <span>›</span> <a href="./">Tulisan</a> <span>›</span> <a href="./#{t['jenis'].lower()}">{escape(t['jenis'])}</a></nav>
      <span class="lencana lencana-besar">{escape(t['jenis'])}{' · DRAF' if t['draf'] else ''}</span>
      <h1>{judul}</h1>
      <div class="info"><span class="sumber">{escape(atur['penulis'])}</span><span class="titik"></span><time datetime="{t['tanggal'].isoformat()}">{tanggal_panjang(t['tanggal'], jam=False)}</time><span class="titik"></span><span>{t['menit_baca']} menit baca</span></div>
      {foto}
      {kotak_laga(t['laga'])}
      <div class="isi-tulisan">
{perbaiki_gambar(t['isi'], '../')}
      </div>
      <div class="bagikan">
        <span>Bagikan:</span>
        <a class="tombol-kecil wa" href="{escape(wa)}" target="_blank" rel="noopener">WhatsApp</a>
        <button class="tombol-kecil" type="button" id="salin" data-alamat="{alamat}">Salin tautan</button>
      </div>
      <aside class="kotak-penulis">
        <div class="avatar" aria-hidden="true">⚽</div>
        <div><strong>Ditulis oleh {escape(atur['penulis'])}</strong><p>{escape(atur.get('profil_penulis') or '')}</p></div>
      </aside>
    </article>
    {bagian}"""
    return dokumen(judul=f"{t['judul']} — {atur['nama_website']}", deskripsi=t["ringkasan"], akar="../",
                   isi=isi, aktif="tulisan", kanonik=alamat, meta=meta, skrip=SKRIP_SALIN, halaman_info=info)


def indeks_tulisan(semua, atur, info):
    if semua:
        ada = [j for j in JENIS if any(t["jenis"] == j for t in semua)]
        chip = "".join(f'<button type="button" class="chip" data-jenis="{j}" aria-pressed="false">{j}</button>' for j in ada)
        isi_daftar = f"""<nav class="saringan" aria-label="Pilih jenis tulisan" style="margin-bottom:16px">
      <button type="button" class="chip" data-jenis="" aria-pressed="true">Semua</button>{chip}
    </nav>
    <div class="grid" id="daftar-tulisan">{"".join(kartu_tulisan(t, "", "../") for t in semua)}</div>"""
    else:
        isi_daftar = '<p class="kosong">Belum ada tulisan. Nantikan prediksi, opini, dan analisis dari Balbalan.</p>'
    skrip = """  <script>
    // Saring tulisan per jenis; alamat #prediksi dsb. langsung memilih jenisnya.
    const chip = [...document.querySelectorAll(".chip")];
    function pilih(jenis) {
      chip.forEach((c) => c.setAttribute("aria-pressed", String(c.dataset.jenis === jenis)));
      document.querySelectorAll("#daftar-tulisan .kartu").forEach((k) => { k.hidden = jenis && k.dataset.jenis !== jenis; });
    }
    chip.forEach((c) => c.addEventListener("click", () => {
      pilih(c.dataset.jenis);
      history.replaceState(null, "", c.dataset.jenis ? "#" + c.dataset.jenis.toLowerCase() : location.pathname);
    }));
    const awal = chip.find((c) => c.dataset.jenis.toLowerCase() === location.hash.slice(1));
    if (awal) pilih(awal.dataset.jenis);
  </script>"""
    isi = f"""    <section class="pembuka">
      <h1>Tulisan Balbalan</h1>
      <p>Prediksi pertandingan, opini, dan analisis sepak bola yang ditulis sendiri oleh {escape(atur['penulis'])}.</p>
    </section>
    {isi_daftar}"""
    return dokumen(judul=f"Tulisan: Prediksi, Opini & Analisis Sepak Bola — {atur['nama_website']}",
                   deskripsi=f"Prediksi pertandingan, opini, dan analisis sepak bola dari {atur['nama_website']}.",
                   akar="../", isi=isi, aktif="tulisan", kanonik=f"{atur['alamat_website']}tulisan/",
                   skrip=skrip, halaman_info=info)


def isi_placeholder(teks, atur):
    email = atur.get("email", "").strip()
    nilai = {
        "nama_website": atur["nama_website"], "alamat_website": atur["alamat_website"],
        "penulis": atur["penulis"], "profil_penulis": atur.get("profil_penulis", ""), "email": email,
        "kontak_email": (f'Email: <a href="mailto:{escape(email)}">{escape(email)}</a>' if email
                         else "Alamat email kontak akan segera ditambahkan."),
    }
    return re.sub(r"\{\{\s*(\w+)\s*\}\}", lambda m: str(nilai.get(m.group(1), m.group(0))), teks)


def halaman_info(h, atur, info):
    isi = f"""    <article class="artikel">
      <nav class="jejak" aria-label="Lokasi halaman"><a href="./">Beranda</a></nav>
      <h1>{escape(h.get('judul') or h['nama'])}</h1>
      <div class="isi-tulisan">
{perbaiki_gambar(isi_placeholder(isi_ke_html(h['isi']), atur), '')}
      </div>
    </article>"""
    return dokumen(judul=f"{h.get('judul') or h['nama']} — {atur['nama_website']}",
                   deskripsi=h.get("deskripsi") or atur["deskripsi"], akar="", isi=isi,
                   kanonik=f"{atur['alamat_website']}{h['nama']}.html", halaman_info=info)


def tulisan_beranda(semua):
    if not semua:
        return ""
    return f"""    <section class="bagian tulisan-beranda">
      <div class="judul-bagian"><h2>Tulisan Balbalan</h2><a href="tulisan/">Lihat semua tulisan →</a></div>
      <div class="grid">{"".join(kartu_tulisan(t, "tulisan/", "") for t in semua[:3])}</div>
    </section>"""


def beranda(semua, atur, info):
    templat = (PROYEK / "templat" / "beranda.html").read_text(encoding="utf-8")
    ganti = {
        "{{DESKRIPSI}}": escape(atur["deskripsi"]), "{{ALAMAT}}": atur["alamat_website"],
        "{{HEAD_UMUM}}": head_umum(""), "{{KEPALA}}": kepala("", "berita"),
        "{{TULISAN_BERANDA}}": tulisan_beranda(semua), "{{KAKI}}": kaki("", info),
    }
    for k, v in ganti.items():
        templat = templat.replace(k, v)
    return templat


def halaman_404(atur, info):
    dasar = atur["jalur_dasar"]
    isi = f"""    <section class="artikel" style="text-align:center;padding:72px 0">
      <div style="font-size:3.5rem" aria-hidden="true">⚽</div>
      <h1>Halaman tidak ditemukan</h1>
      <p class="ringkasan">Balbalan hanya menyimpan berita 3 hari terakhir, jadi berita ini mungkin sudah tidak tersedia.</p>
      <a class="tombol-baca" href="{dasar}">Lihat berita terbaru</a>
    </section>"""
    return dokumen(judul=f"Halaman tidak ditemukan — {atur['nama_website']}", deskripsi=atur["deskripsi"],
                   akar=dasar, isi=isi, meta='<meta name="robots" content="noindex">', halaman_info=info)


def sitemap(semua, atur, info):
    alamat = atur["alamat_website"]
    hari_ini = datetime.now(WIB).date().isoformat()
    url = [(alamat, hari_ini), (f"{alamat}tulisan/", semua[0]["tanggal"].isoformat() if semua else hari_ini)]
    url += [(f"{alamat}tulisan/{t['slug']}.html", t["tanggal"].isoformat()) for t in semua]
    url += [(f"{alamat}{h['nama']}.html", None) for h in info]
    isi = "".join(f"<url><loc>{escape(u)}</loc>{f'<lastmod>{m}</lastmod>' if m else ''}</url>\n" for u, m in url)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{isi}</urlset>\n'


def main():
    dengan_draf = "--draf" in sys.argv
    atur = pengaturan()
    info = daftar_halaman_info()
    semua = muat_tulisan(dengan_draf)
    berkas_berita = SITUS / "data" / "berita.json"
    berita = json.loads(berkas_berita.read_text(encoding="utf-8"))["berita"] if berkas_berita.exists() else []

    folder = SITUS / "tulisan"
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir(parents=True)
    for t in semua:
        (folder / f"{t['slug']}.html").write_text(halaman_tulisan(t, semua, berita, atur, info), encoding="utf-8")
    (folder / "index.html").write_text(indeks_tulisan(semua, atur, info), encoding="utf-8")

    for h in info:
        (SITUS / f"{h['nama']}.html").write_text(halaman_info(h, atur, info), encoding="utf-8")
    (SITUS / "index.html").write_text(beranda(semua, atur, info), encoding="utf-8")
    (SITUS / "404.html").write_text(halaman_404(atur, info), encoding="utf-8")
    ads = SITUS / "ads.txt"
    if atur["adsense_id"]:
        ads.write_text(f"google.com, {atur['adsense_id'].removeprefix('ca-')}, DIRECT, f08c47fec0942fa0\n", encoding="utf-8")
    elif ads.exists():
        ads.unlink()
    (SITUS / "sitemap.xml").write_text(sitemap([t for t in semua if not t["draf"]], atur, info), encoding="utf-8")
    print(f"Dibuat {len(semua)} tulisan, {len(info)} halaman info, beranda, 404 dan sitemap")
    for t in semua:
        if t["kata"] < 300 and not t["draf"]:
            print(f"  catatan: '{t['judul']}' baru {t['kata']} kata; tulisan 600+ kata lebih disukai Google")

    if berita:
        buat_halaman.main()


if __name__ == "__main__":
    main()
