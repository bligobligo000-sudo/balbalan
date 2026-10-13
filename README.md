# ⚽ Balbalan

Website berita sepak bola terbaru yang **memperbarui dirinya sendiri setiap 3 jam**.

**Alamat website:** https://bligobligo000-sudo.github.io/balbalan/

## Cara kerjanya

1. Setiap 3 jam, GitHub menjalankan program kecil `scripts/ambil_berita.py` secara otomatis (gratis).
2. Program itu mengambil daftar berita terbaru dari detikSport, Liputan6, VIVA, iNews dan SINDOnews, lalu menyaring yang khusus sepak bola.
3. Hasilnya disimpan di `site/data/berita.json`, lalu website dipasang ulang.

Anda tidak perlu melakukan apa-apa: biarkan saja, website akan terus terisi berita baru.

Website hanya menampilkan judul, ringkasan singkat dan foto kecil. Pengunjung yang mengeklik berita dibawa ke situs aslinya untuk membaca selengkapnya.

## Isi folder

| Berkas | Gunanya |
|---|---|
| `site/index.html` | Kerangka halaman (judul, tulisan di atas, bagian bawah) |
| `site/style.css` | Warna, huruf dan tata letak |
| `site/app.js` | Menampilkan berita, tombol kategori dan kolom pencarian |
| `site/data/berita.json` | Daftar berita (dibuat otomatis, jangan diubah manual) |
| `scripts/ambil_berita.py` | Program pengambil berita: daftar sumber dan kategori ada di sini |
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
