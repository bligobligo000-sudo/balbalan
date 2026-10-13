# ⚽ Balbalan

Website sepak bola berisi **berita terbaru yang memperbarui dirinya sendiri setiap 3 jam**, plus **tulisan Anda sendiri** (prediksi, opini, analisis).

**Alamat website:** https://bligobligo000-sudo.github.io/balbalan/

👉 **Mau menulis?** Baca [PANDUAN-MENULIS.md](PANDUAN-MENULIS.md). Anda menulis lewat editor Pages CMS (https://app.pagescms.org) tanpa menyentuh kode.

## Cara kerjanya

1. Setiap 3 jam, GitHub menjalankan `scripts/ambil_berita.py` secara otomatis (gratis). Program ini mengambil berita terbaru dari detikSport, Liputan6, VIVA, iNews, dan SINDOnews, lalu menyaring yang khusus sepak bola. Untuk berita baru, foto besar dan nama penulisnya diambil dari halaman aslinya; isi artikelnya tidak diambil.
2. Hasilnya disimpan di `site/data/berita.json`.
3. `scripts/buat_situs.py` lalu menyusun seluruh website: beranda, halaman baca untuk tiap berita, tulisan Anda, halaman info, sitemap, dan halaman 404. Setelah itu website dipasang ulang.
4. Setiap kali Anda menyimpan tulisan di Pages CMS, website juga dipasang ulang otomatis (1–2 menit).

Saat berita diklik, pembaca tetap di Balbalan: mereka melihat halaman baca berisi judul, ringkasan, dan foto dari media, berita terkait, dan tombol **Baca selengkapnya** ke situs aslinya. Isi artikel lengkap sengaja tidak disalin supaya tidak melanggar hak cipta media.

## Isi folder

| Berkas | Gunanya |
|---|---|
| `konten/tulisan/` | Tulisan Anda (ditulis lewat Pages CMS) |
| `konten/halaman/` | Halaman info: Tentang Kami, Kontak, Kebijakan Privasi, Disclaimer |
| `konten/pengaturan.json` | Nama penulis, email kontak, kode Google Search Console, ID AdSense |
| `site/gambar/` | Foto yang diunggah lewat Pages CMS |
| `.pages.yml` | Susunan formulir di editor Pages CMS |
| `templat/beranda.html` | Kerangka beranda |
| `site/style.css` | Warna, huruf, dan tata letak |
| `site/app.js` | Menampilkan berita, tombol kategori, dan kolom pencarian di beranda |
| `site/data/berita.json` | Daftar berita (dibuat otomatis, jangan diubah manual) |
| `scripts/ambil_berita.py` | Pengambil berita: daftar sumber dan kategori ada di sini |
| `scripts/buat_situs.py` | Penyusun seluruh website (tulisan, halaman info, beranda, sitemap, 404) |
| `scripts/buat_halaman.py` | Penyusun halaman baca berita dan pencari berita terkait |
| `scripts/tata_letak.py` | Bagian halaman yang dipakai bersama (menu atas, bagian bawah) |
| `.github/workflows/perbarui-berita.yml` | Jadwal update otomatis dan pemasangan website |

Berkas HTML di `site/` (kecuali `style.css` dan `app.js`) dibuat otomatis saat website dipasang, jadi tidak disimpan di git.

## Pertanyaan umum

**Mau update berita sekarang juga, tanpa menunggu 3 jam?**
Buka tab **Actions** di halaman GitHub repositori ini, pilih **Perbarui berita**, lalu klik **Run workflow**.

**Bagaimana kalau update gagal?**
GitHub akan mengirim email pemberitahuan. Website tetap menampilkan berita terakhir yang berhasil diambil. Biasanya penyebabnya salah satu situs berita sedang gangguan, dan akan pulih sendiri pada update berikutnya.

**Mau melihat hasil di komputer sendiri sebelum dipasang?**
Jalankan `python scripts/buat_situs.py --draf` (perlu `pip install pyyaml`), lalu `python -m http.server --directory site`. Dengan `--draf`, tulisan draf dan tulisan terjadwal ikut tampil.

**Mau menambah atau membuang sumber berita / kategori?**
Ubah daftar `SUMBER` atau `KATEGORI` di `scripts/ambil_berita.py`. Kalau menambah kategori, tambahkan juga namanya di baris `KATEGORI` paling atas `site/app.js`.
