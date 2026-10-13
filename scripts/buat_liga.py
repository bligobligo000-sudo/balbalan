"""Membuat halaman jadwal, hasil, klasemen, dan halaman klub dari site/data/liga.json:

- site/liga/index.html          laga hari ini + ringkasan semua kompetisi
- site/liga/<kompetisi>.html    jadwal, hasil, klasemen, dan berita satu kompetisi
- site/klub/index.html          daftar semua klub
- site/klub/<klub>.html         jadwal, hasil, posisi klasemen, berita, dan tulisan satu klub

Dipanggil oleh buat_situs.py.
"""
import json
import re
import shutil
import unicodedata
from datetime import datetime, timedelta, timezone
from html import escape

import buat_halaman
from tata_letak import BULAN, HARI, SITUS, WIB, dokumen

# Nama tampilan dan nama panggilan klub populer, untuk mencocokkan berita dan tulisan.
# Kunci = slug nama klub. Nama panggilan diawali "re:" adalah pola regex.
KLUB_POPULER = {
    # Indonesia
    "persib-bandung": ("Persib Bandung", ["persib", "maung bandung"]),
    "persija-jakarta": ("Persija Jakarta", ["persija", "macan kemayoran"]),
    "persebaya-surabaya": ("Persebaya Surabaya", ["persebaya", "bajul ijo"]),
    "arema": ("Arema FC", ["arema", "singo edan"]),
    "psm-makassar": ("PSM Makassar", ["psm", "juku eja"]),
    "pss-sleman": ("PSS Sleman", ["pss", "super elja"]),
    "bali-united": ("Bali United", ["bali united", "serdadu tridatu"]),
    "borneo-fc-samarinda": ("Borneo FC", ["borneo", "pesut etam"]),
    "dewa-united-banten": ("Dewa United", ["dewa united"]),
    "madura-united": ("Madura United", ["madura united"]),
    "persik-kediri": ("Persik Kediri", ["persik", "macan putih"]),
    "persita": ("Persita Tangerang", ["persita", "pendekar cisadane"]),
    "psim-yogyakarta": ("PSIM Yogyakarta", ["psim", "laskar mataram"]),
    "persijap-jepara": ("Persijap Jepara", ["persijap", "laskar kalinyamat"]),
    "bhayangkara-presisi-lampung": ("Bhayangkara FC", ["bhayangkara"]),
    "garudayaksa": ("Garudayaksa", ["garudayaksa"]),
    "isenmulang-kalteng": ("Isenmulang Kalteng", ["isenmulang"]),
    "java-united": ("Java United", ["java united"]),
    # Eropa
    "manchester-united": ("Manchester United", ["man utd", "man united", "re:(?-i:MU)", "setan merah"]),
    "manchester-city": ("Manchester City", ["man city", "the citizens"]),
    "liverpool": ("Liverpool", ["liverpool", "the reds"]),
    "arsenal": ("Arsenal", ["arsenal", "the gunners"]),
    "chelsea": ("Chelsea", ["chelsea", "the blues"]),
    "tottenham-hotspur": ("Tottenham Hotspur", ["tottenham", "spurs"]),
    "newcastle-united": ("Newcastle United", ["newcastle"]),
    "aston-villa": ("Aston Villa", ["aston villa"]),
    "west-ham-united": ("West Ham United", ["west ham"]),
    "real-madrid": ("Real Madrid", ["real madrid", "los blancos"]),
    "barcelona": ("Barcelona", ["barcelona", "barca", "barça", "blaugrana"]),
    "club-atletico-de-madrid": ("Atletico Madrid", ["atletico madrid", "atletico", "atlético", "atleti"]),
    "atletico-madrid": ("Atletico Madrid", ["atletico madrid", "atletico", "atlético", "atleti"]),
    "internazionale-milano": ("Inter Milan", ["inter milan", r"re:inter(?!\s+miami)", "nerazzurri"]),
    "inter": ("Inter Milan", ["inter milan", r"re:inter(?!\s+miami)", "nerazzurri"]),
    "milan": ("AC Milan", ["ac milan", "rossoneri"]),
    "ac-milan": ("AC Milan", ["ac milan", "rossoneri"]),
    "juventus": ("Juventus", ["juventus", "juve", "bianconeri"]),
    "napoli": ("Napoli", ["napoli", "partenopei"]),
    "roma": ("AS Roma", ["as roma", "roma", "giallorossi"]),
    "as-roma": ("AS Roma", ["as roma", "roma", "giallorossi"]),
    "lazio": ("Lazio", ["lazio"]),
    "bayern-munchen": ("Bayern Munchen", ["bayern", "munchen", "münchen", "die roten"]),
    "bayern": ("Bayern Munchen", ["bayern", "munchen", "münchen", "die roten"]),
    "borussia-dortmund": ("Borussia Dortmund", ["dortmund", "bvb"]),
    "leverkusen": ("Bayer Leverkusen", ["leverkusen"]),
    "bayer-leverkusen": ("Bayer Leverkusen", ["leverkusen"]),
    "paris-saint-germain": ("Paris Saint-Germain", ["psg", "paris saint-germain", "paris saint germain"]),
}
AWALAN = r"^(?:1\.\s*)?(?:FC|AFC|AC|AS|SS|SSC|SL|RC|RCD|CF|SC)\s+"
AKHIRAN = r"\s+(?:FC|CF|AFC|SC|CFC|KV|FK)$"


def slug(teks):
    teks = unicodedata.normalize("NFKD", teks).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", teks.lower()).strip("-")


def ke_wib(iso):
    return datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).astimezone(WIB)


def tanggal_judul(t):
    return f"{HARI[t.weekday()]}, {t.day} {BULAN[t.month - 1]} {t.year}"


# ---------- Klub ----------

def siapkan_klub(data):
    """Lengkapi setiap tim dengan nama tampilan, slug halaman, kompetisi, dan pola pencocokan berita."""
    klub = {}
    for tid, t in data["tim"].items():
        if tid.startswith("idn-"):
            bersih = t["nama"]
        else:
            bersih = re.sub(AKHIRAN, "", re.sub(AWALAN, "", t["nama"]))
            if len(bersih) > 20 or re.search(r"\d", bersih):
                bersih = t.get("pendek") or bersih
        populer = KLUB_POPULER.get(slug(bersih)) or KLUB_POPULER.get(slug(t.get("pendek") or ""))
        nama = populer[0] if populer else bersih
        alias = {nama.lower(), bersih.lower()} | set(populer[1] if populer else [])
        if tid.startswith("idn-") and not populer:
            alias.add(nama.split()[0].lower())
        pola = [a[3:] if a.startswith("re:") else re.escape(a) for a in alias if len(a) >= 3 or a.startswith("re:")]
        klub[tid] = {**t, "id": tid, "tampil": nama, "slug": slug(nama), "kompetisi": [],
                     "pola": re.compile(r"(?<![\w-])(?:" + "|".join(sorted(pola, key=len, reverse=True)) + r")(?![\w-])", re.I)}
    terpakai = {}
    for k in klub.values():  # slug kembar (jarang): tambahkan akhiran
        if k["slug"] in terpakai:
            k["slug"] = f"{k['slug']}-{k['id'].split('-', 1)[1]}"
        terpakai[k["slug"]] = k
    for komp in data["kompetisi"]:
        anggota = {r["tim"] for r in komp["klasemen"]} | {m[x] for m in komp["laga"] for x in ("kandang", "tamu")}
        for tid in anggota:
            if tid in klub and komp["slug"] not in klub[tid]["kompetisi"]:
                klub[tid]["kompetisi"].append(komp["slug"])
    return klub


def klub_dalam_teks(klub, teks, batas=4):
    return [k for k in klub.values() if k["pola"].search(teks)][:batas]


# ---------- Potongan HTML ----------

def logo(k, ukuran=24):
    if k.get("logo"):
        return (f'<img class="logo-tim" src="{escape(k["logo"])}" alt="" width="{ukuran}" height="{ukuran}" '
                f'loading="lazy" referrerpolicy="no-referrer" onerror="this.style.visibility=\'hidden\'">')
    return f'<span class="logo-tim logo-kosong" style="width:{ukuran}px;height:{ukuran}px" aria-hidden="true"></span>'


def tautan_klub(k, akar, sisi=""):
    nama = f"<span>{escape(k['tampil'])}</span>"
    isi = f"{nama}{logo(k)}" if sisi == "kandang" else f"{logo(k)}{nama}"
    return f'<a class="laga-tim {sisi}" href="{akar}klub/{k["slug"]}.html">{isi}</a>'


def baris_laga(m, klub, akar, tampil_liga=None):
    t = ke_wib(m["waktu"])
    if m["status"] == "selesai":
        kiri, skor = "FT", f"{m['skor'][0]} – {m['skor'][1]}"
    elif m["status"] == "berlangsung":
        kiri, skor = '<span class="langsung">LIVE</span>', f"{m['skor'][0]} – {m['skor'][1]}" if m["skor"] else "vs"
    elif m["status"] in ("ditunda", "batal"):
        kiri, skor = "Tunda" if m["status"] == "ditunda" else "Batal", "vs"
    else:
        kiri, skor = (f"{t:%H.%M}" if m.get("jam_pasti", True) else "–"), "vs"
    kelas = "laga-baris" + (" selesai" if m["status"] == "selesai" else "")
    liga = f'<span class="laga-liga">{escape(tampil_liga)}</span>' if tampil_liga else ""
    return (f'<div class="{kelas}"><span class="laga-waktu">{kiri}</span>'
            f'{tautan_klub(klub[m["kandang"]], akar, "kandang")}<span class="laga-skor">{skor}</span>'
            f'{tautan_klub(klub[m["tamu"]], akar, "tamu")}{liga}</div>')


def daftar_laga(laga, klub, akar, nama_liga=None, kosong="Belum ada laga."):
    if not laga:
        return f'<p class="kosong-kecil">{kosong}</p>'
    html, hari_ini = [], None
    for m in laga:
        tgl = ke_wib(m["waktu"]).date()
        if tgl != hari_ini:
            if hari_ini is not None:
                html.append("</div>")
            hari_ini = tgl
            html.append(f'<div class="laga-hari"><h3 class="laga-tanggal">{tanggal_judul(tgl)}</h3>')
        html.append(baris_laga(m, klub, akar, nama_liga(m) if nama_liga else None))
    html.append("</div>")
    return "".join(html)


def titik_form(form):
    nama = {"M": "Menang", "S": "Seri", "K": "Kalah"}
    return "".join(f'<span class="form {f.lower()}" title="{nama[f]}">{f}</span>' for f in form)


def tabel_klasemen(komp, klub, akar, sorot=None, baris=None):
    isi = []
    grup_sebelum = None
    for r in komp["klasemen"]:
        if baris is not None and r["posisi"] not in baris:
            continue
        if r.get("grup") and r["grup"] != grup_sebelum:
            grup_sebelum = r["grup"]
            isi.append(f'<tr class="grup"><td colspan="10">{escape(r["grup"].replace("GROUP_", "Grup "))}</td></tr>')
        k = klub[r["tim"]]
        kelas = ' class="sorot"' if r["tim"] == sorot else ""
        catatan = f' <span class="potong" title="Pengurangan poin">−{r["potong_poin"]}</span>' if r.get("potong_poin") else ""
        isi.append(
            f'<tr{kelas}><td class="pos">{r["posisi"]}</td>'
            f'<td class="klub"><a href="{akar}klub/{k["slug"]}.html">{logo(k, 20)}<span>{escape(k["tampil"])}</span></a></td>'
            f'<td>{r["main"]}</td><td class="hp-sembunyi">{r["menang"]}</td><td class="hp-sembunyi">{r["seri"]}</td>'
            f'<td class="hp-sembunyi">{r["kalah"]}</td><td class="hp-sembunyi">{r["gm"]}:{r["gk"]}</td>'
            f'<td>{r["sg"]:+d}</td><td class="poin">{r["poin"]}{catatan}</td>'
            f'<td class="hp-sembunyi forms">{titik_form(r["form"])}</td></tr>')
    return (f'<div class="tabel-gulir"><table class="klasemen"><thead><tr><th>#</th><th class="klub">Klub</th>'
            f'<th title="Main">Main</th><th class="hp-sembunyi" title="Menang">M</th><th class="hp-sembunyi" title="Seri">S</th>'
            f'<th class="hp-sembunyi" title="Kalah">K</th><th class="hp-sembunyi" title="Gol memasukkan:kemasukan">Gol</th>'
            f'<th title="Selisih gol">SG</th><th>Poin</th><th class="hp-sembunyi">5 laga terakhir</th></tr></thead>'
            f'<tbody>{"".join(isi)}</tbody></table></div>')


def catatan_sumber(komp, diperbarui):
    t = ke_wib(diperbarui)
    return (f'<p class="sumber-data">Sumber data: <a href="{escape(komp["sumber_url"])}" target="_blank" rel="noopener">'
            f'{escape(komp["sumber"])}</a> · Diperbarui {t.day} {BULAN[t.month - 1][:3]}, {t:%H.%M} WIB · '
            f'Jam pertandingan dalam WIB</p>')


def kartu_berita(berita, akar):
    return f'<div class="grid">{"".join(buat_halaman.kartu_html(b, f"{akar}baca/") for b in berita)}</div>'


# ---------- Halaman ----------

def pisah_laga(laga, sekarang):
    iso = sekarang.strftime("%Y-%m-%dT%H:%M:%SZ")
    akan = [m for m in laga if m["status"] in ("jadwal", "berlangsung", "ditunda") and (m["waktu"] >= iso or m["status"] == "berlangsung")]
    lalu = [m for m in laga if m["status"] == "selesai"][::-1]
    return akan, lalu


def halaman_hub(data, klub, atur, info):
    sekarang = datetime.now(timezone.utc)
    hari_ini = sekarang.astimezone(WIB).date()
    nama_liga = {m["id"]: k["nama"] for k in data["kompetisi"] for m in k["laga"]}
    semua = sorted((m for k in data["kompetisi"] for m in k["laga"]), key=lambda m: m["waktu"])
    hari_ini_laga = [m for m in semua if ke_wib(m["waktu"]).date() == hari_ini]
    if hari_ini_laga:
        judul_laga, laga_tampil = "Laga hari ini", hari_ini_laga
    else:
        berikut = [m for m in semua if ke_wib(m["waktu"]).date() > hari_ini and m["status"] != "selesai"]
        tgl = ke_wib(berikut[0]["waktu"]).date() if berikut else None
        judul_laga = "Tidak ada laga hari ini · Laga berikutnya"
        laga_tampil = [m for m in berikut if ke_wib(m["waktu"]).date() == tgl]
    kemarin = [m for m in semua if m["status"] == "selesai" and ke_wib(m["waktu"]).date() in (hari_ini, hari_ini - timedelta(days=1))]

    kartu = []
    for k in data["kompetisi"]:
        akan, _ = pisah_laga(k["laga"], sekarang)
        kartu.append(f"""<section class="kartu-liga">
        <div class="judul-bagian"><h2><a href="{k['slug']}.html">{escape(k['nama'])}</a></h2><a href="{k['slug']}.html">Lengkap →</a></div>
        <p class="nama-resmi">{escape(k['nama_resmi'])}</p>
        {tabel_klasemen(k, klub, "../", baris=range(1, 6)) if k['klasemen'] else ''}
        {f'<h3 class="sub">Laga berikutnya</h3>{daftar_laga(akan[:3], klub, "../")}' if akan else ''}
      </section>""")
    belum_eropa = "" if len(data["kompetisi"]) > 1 else (
        '<p class="info-kecil">Jadwal dan klasemen Liga Inggris, Spanyol, Italia, Jerman, dan Liga Champions segera hadir.</p>')
    isi = f"""    <section class="pembuka">
      <h1>Jadwal Bola, Hasil &amp; Klasemen</h1>
      <p>Jadwal pertandingan (WIB), hasil terbaru, dan klasemen {', '.join(escape(k['nama']) for k in data['kompetisi'])}. Diperbarui otomatis setiap 3 jam.</p>
    </section>
    <nav class="saringan tab-liga" aria-label="Pilih kompetisi">{''.join(f'<a class="chip" href="{k["slug"]}.html">{escape(k["nama"])}</a>' for k in data['kompetisi'])}<a class="chip" href="../klub/">Semua klub</a></nav>
    {belum_eropa}
    <section class="bagian"><h2>{judul_laga}</h2>{daftar_laga(laga_tampil, klub, "../", lambda m: nama_liga[m["id"]], "Belum ada jadwal.")}</section>
    {f'<section class="bagian"><h2>Hasil terbaru</h2>{daftar_laga(kemarin[::-1], klub, "../", lambda m: nama_liga[m["id"]])}</section>' if kemarin else ''}
    <div class="grid-liga">{''.join(kartu)}</div>"""
    return dokumen(judul=f"Jadwal Bola Hari Ini, Hasil & Klasemen — {atur['nama_website']}",
                   deskripsi="Jadwal bola hari ini (WIB), hasil pertandingan terbaru, dan klasemen Liga Indonesia serta liga-liga top Eropa.",
                   akar="../", isi=isi, aktif="jadwal", kanonik=f"{atur['alamat_website']}liga/", halaman_info=info)


def halaman_kompetisi(k, data, klub, berita, atur, info):
    sekarang = datetime.now(timezone.utc)
    akan, lalu = pisah_laga(k["laga"], sekarang)
    berita_liga = [b for b in berita if k["nama"] in b.get("kategori", [])][:6]
    isi = f"""    <section class="pembuka">
      <h1>{escape(k['nama'])}: Jadwal, Hasil &amp; Klasemen</h1>
      <p>{escape(k['nama_resmi'])}</p>
    </section>
    <nav class="saringan tab-liga" aria-label="Bagian halaman"><a class="chip" href="#jadwal">Jadwal</a><a class="chip" href="#hasil">Hasil</a><a class="chip" href="#klasemen">Klasemen</a>{'<a class="chip" href="#berita">Berita</a>' if berita_liga else ''}</nav>
    <section class="bagian" id="jadwal"><h2>Jadwal</h2>{daftar_laga(akan[:20], klub, "../", kosong="Belum ada jadwal dalam 30 hari ke depan.")}</section>
    <section class="bagian" id="hasil"><h2>Hasil terbaru</h2>{daftar_laga(lalu[:20], klub, "../", kosong="Belum ada hasil.")}</section>
    <section class="bagian" id="klasemen"><h2>Klasemen</h2>{tabel_klasemen(k, klub, "../") if k['klasemen'] else '<p class="kosong-kecil">Klasemen belum tersedia.</p>'}
      <p class="keterangan-tabel">M = menang, S = seri, K = kalah, SG = selisih gol.</p></section>
    {f'<section class="bagian" id="berita"><h2>Berita {escape(k["nama"])}</h2>{kartu_berita(berita_liga, "../")}</section>' if berita_liga else ''}
    {catatan_sumber(k, data['diperbarui'])}"""
    return dokumen(judul=f"Jadwal {k['nama']}, Hasil & Klasemen Terbaru — {atur['nama_website']}",
                   deskripsi=f"Jadwal {k['nama']} ({k['nama_resmi']}) dalam WIB, hasil pertandingan terbaru, dan klasemen lengkap.",
                   akar="../", isi=isi, aktif="jadwal", kanonik=f"{atur['alamat_website']}liga/{k['slug']}.html", halaman_info=info)


def halaman_klub(kl, data, klub, berita, tulisan, kartu_tulisan, atur, info):
    sekarang = datetime.now(timezone.utc)
    komp = [k for k in data["kompetisi"] if k["slug"] in kl["kompetisi"]]
    laga = sorted((m for k in komp for m in k["laga"] if kl["id"] in (m["kandang"], m["tamu"])), key=lambda m: m["waktu"])
    akan, lalu = pisah_laga(laga, sekarang)
    nama_liga = {m["id"]: k["nama"] for k in komp for m in k["laga"]}
    label = (lambda m: nama_liga[m["id"]]) if len(komp) > 1 else None  # nama kompetisi hanya perlu kalau lebih dari satu

    posisi = []
    for k in komp:
        for r in k["klasemen"]:
            if r["tim"] == kl["id"]:
                posisi.append((k, r))
    ringkas = " · ".join(f'Peringkat {r["posisi"]} <a href="../liga/{k["slug"]}.html">{escape(k["nama"])}</a> ({r["poin"]} poin)' for k, r in posisi)

    hasil_html = ""
    if lalu:
        baris = []
        for m in lalu[:5]:
            kandang = m["kandang"] == kl["id"]
            gol, kebobolan = (m["skor"][0], m["skor"][1]) if kandang else (m["skor"][1], m["skor"][0])
            hasil = "M" if gol > kebobolan else "S" if gol == kebobolan else "K"
            baris.append(f'<div class="hasil-klub">{titik_form(hasil)}{baris_laga(m, klub, "../", label(m) if label else None)}</div>')
        hasil_html = f'<section class="bagian"><h2>Hasil terakhir</h2>{"".join(baris)}</section>'

    tabel_html = ""
    for k, r in posisi:
        sekitar = range(max(1, r["posisi"] - 2), r["posisi"] + 3)
        tabel_html += (f'<section class="bagian"><div class="judul-bagian"><h2>Klasemen {escape(k["nama"])}</h2>'
                       f'<a href="../liga/{k["slug"]}.html#klasemen">Lengkap →</a></div>'
                       f'{tabel_klasemen(k, klub, "../", sorot=kl["id"], baris=sekitar)}</section>')

    cocok = [b for b in berita if kl["pola"].search(f"{b['judul']} {b['ringkasan']}")][:9]
    tulisan_cocok = [t for t in tulisan if kl["pola"].search(f"{t['judul']} {t['ringkasan']} {t['laga']['kandang']} {t['laga']['tamu']}")][:3]
    tulisan_html = ""
    if tulisan_cocok:
        tulisan_html = (f'<section class="bagian"><h2>Tulisan tentang {escape(kl["tampil"])}</h2><div class="grid">'
                        f'{"".join(kartu_tulisan(t, "../tulisan/", "../") for t in tulisan_cocok)}</div></section>')

    isi = f"""    <section class="kepala-klub">
      {logo(kl, 72)}
      <div>
        <nav class="jejak" aria-label="Lokasi halaman"><a href="../liga/">Jadwal</a> <span>›</span> <a href="./">Klub</a></nav>
        <h1>{escape(kl['tampil'])}</h1>
        <p>{ringkas or ', '.join(escape(k['nama']) for k in komp)}</p>
      </div>
    </section>
    <section class="bagian"><h2>Jadwal berikutnya</h2>{daftar_laga(akan[:5], klub, "../", label, "Belum ada jadwal dalam 30 hari ke depan.")}</section>
    {hasil_html}
    {tabel_html}
    {tulisan_html}
    {f'<section class="bagian"><h2>Berita {escape(kl["tampil"])}</h2>{kartu_berita(cocok, "../")}</section>' if cocok else ''}
    {''.join(catatan_sumber(k, data['diperbarui']) for k in komp[:1])}"""
    nama = kl["tampil"]
    return dokumen(judul=f"Jadwal {nama}, Hasil & Berita Terbaru — {atur['nama_website']}",
                   deskripsi=f"Jadwal {nama} berikutnya (WIB), hasil pertandingan terakhir, posisi di klasemen, dan berita terbaru {nama}.",
                   akar="../", isi=isi, aktif="klub", kanonik=f"{atur['alamat_website']}klub/{kl['slug']}.html", halaman_info=info)


def indeks_klub(data, klub, atur, info):
    bagian, sudah = [], set()
    for k in data["kompetisi"]:
        anggota = [klub[r["tim"]] for r in k["klasemen"] if r["tim"] not in sudah] or \
                  sorted({klub[m[x]]["id"]: klub[m[x]] for m in k["laga"] for x in ("kandang", "tamu") if m[x] not in sudah}.values(), key=lambda c: c["tampil"])
        anggota = sorted(anggota, key=lambda c: c["tampil"])
        if not anggota:
            continue
        sudah |= {c["id"] for c in anggota}
        judul = k["nama"] if k["slug"] != "liga-champions" else "Klub Eropa lainnya (Liga Champions)"
        bagian.append(f'<section class="bagian"><h2>{escape(judul)}</h2><div class="daftar-klub">'
                      + "".join(f'<a class="chip-klub" href="{c["slug"]}.html">{logo(c, 28)}<span>{escape(c["tampil"])}</span></a>' for c in anggota)
                      + "</div></section>")
    isi = f"""    <section class="pembuka">
      <h1>Daftar Klub</h1>
      <p>Pilih klub untuk melihat jadwal, hasil, posisi di klasemen, dan berita terbarunya.</p>
    </section>
    {''.join(bagian) or '<p class="kosong">Data klub belum tersedia.</p>'}"""
    return dokumen(judul=f"Daftar Klub: Jadwal & Berita Klub Sepak Bola — {atur['nama_website']}",
                   deskripsi="Jadwal, hasil, klasemen, dan berita terbaru klub Liga Indonesia dan klub-klub top Eropa.",
                   akar="../", isi=isi, aktif="klub", kanonik=f"{atur['alamat_website']}klub/", halaman_info=info)


def main(atur, info, berita, tulisan, kartu_tulisan):
    """Buat semua halaman liga & klub. Mengembalikan (daftar URL untuk sitemap, data klub)."""
    berkas = SITUS / "data" / "liga.json"
    data = json.loads(berkas.read_text(encoding="utf-8")) if berkas.exists() else {"kompetisi": [], "tim": {}, "diperbarui": None}
    klub = siapkan_klub(data)
    for folder in ("liga", "klub"):
        shutil.rmtree(SITUS / folder, ignore_errors=True)
        (SITUS / folder).mkdir(parents=True)

    alamat = atur["alamat_website"]
    url = [f"{alamat}liga/", f"{alamat}klub/"]
    if data["kompetisi"]:
        (SITUS / "liga" / "index.html").write_text(halaman_hub(data, klub, atur, info), encoding="utf-8")
    else:
        kosong = '    <section class="pembuka"><h1>Jadwal, Hasil &amp; Klasemen</h1><p>Data sedang disiapkan.</p></section>'
        (SITUS / "liga" / "index.html").write_text(dokumen(judul="Jadwal Bola — Balbalan", deskripsi=atur["deskripsi"], akar="../",
                                                           isi=kosong, aktif="jadwal", halaman_info=info), encoding="utf-8")
    for k in data["kompetisi"]:
        (SITUS / "liga" / f"{k['slug']}.html").write_text(halaman_kompetisi(k, data, klub, berita, atur, info), encoding="utf-8")
        url.append(f"{alamat}liga/{k['slug']}.html")
    for kl in klub.values():
        (SITUS / "klub" / f"{kl['slug']}.html").write_text(halaman_klub(kl, data, klub, berita, tulisan, kartu_tulisan, atur, info), encoding="utf-8")
        url.append(f"{alamat}klub/{kl['slug']}.html")
    (SITUS / "klub" / "index.html").write_text(indeks_klub(data, klub, atur, info), encoding="utf-8")
    print(f"Dibuat {len(data['kompetisi'])} halaman kompetisi dan {len(klub)} halaman klub")
    return url, klub
