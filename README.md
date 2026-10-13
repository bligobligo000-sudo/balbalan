# ⚽ Balbalan

Website berita sepak bola terbaru yang **memperbarui dirinya sendiri setiap 3 jam**.

**Alamat website:** https://bligobligo000-sudo.github.io/balbalan/

## Cara kerjanya

1. Setiap 3 jam, GitHub menjalankan program kecil `scripts/ambil_berita.py` secara otomatis (gratis).
2. Program itu mengambil daftar berita terbaru dari detikSport, Liputan6, VIVA, iNews dan SINDOnews, lalu menyaring yang khusus sepak bola.
3. Untuk setiap berita baru, foto ukuran besar dan nama penulisnya diambil dari halaman berita aslinya (isi artikelnya tidak diambil).
4. Hasilnya disimpan di `site/data/berita.json`. Program `scripts/buat_halaman.py` lalu membuat satu halaman baca untuk setiap berita (foto besar, ringkasan, tombol bagikan, berita terkait), dan website dipasang ulang.

Anda tidak perlu melakukan apa-apa: biarkan saja, website akan terus terisi berita baru.

Saat berita diklik, pembaca tetap di Balbalan: mereka melihat halaman baca berisi judul, ringkasan dan foto dari media, berita terkait, dan tombol **Baca selengkapnya** ke situs aslinya. Isi artikel lengkap sengaja tidak disalin supaya tidak melanggar hak cipta media.

## Isi folder

| Berkas | Gunanya |
|---|---|
| `site/index.html` | Kerangka halaman (judul, tulisan di atas, bagian bawah) |
| `site/style.css` | Warna, huruf dan tata letak |
| `site/app.js` | Menampilkan berita, tombol kategori dan kolom pencarian |
| `site/data/berita.json` | Daftar berita (dibuat otomatis, jangan diubah manual) |
| `scripts/ambil_berita.py` | Program pengambil berita: daftar sumber dan kategori ada di sini |
| `scripts/buat_halaman.py` | Pembuat halaman baca `site/baca/…` (dibuat otomatis, tidak disimpan di git) |
| `site/404.html` | Halaman "berita tidak ditemukan" untuk tautan berita yang sudah lebih dari 3 hari |
| `.github/workflows/perbarui-berita.yml` | Jadwal update otomatis |

## Pertanyaan umum

**Mau update berita sekarang juga, tanpa menunggu 3 jam?**
Buka tab **Actions** di halaman GitHub repositori ini → pilih **Perbarui berita** → klik **Run workflow**.

**Bagaimana kalau update gagal?**
GitHub akan mengirim email pemberitahuan. Website tetap menampilkan berita terakhir yang berhasil diambil. Biasanya penyebabnya salah satu situs berita sedang gangguan, dan akan pulih sendiri pada update berikutnya.

**Mau menambah atau membuang sumber berita / kategori?**
Ubah daftar `SUMBER` atau `KATEGORI` di `scripts/ambil_berita.py`. Kalau menambah kategori, tambahkan juga namanya di baris `KATEGORI` paling atas `site/app.js`.

**Mau mengganti warna?**
Ubah nilai warna di bagian paling atas `site/style.css` (misalnya `--hijau`).
