# Panduan Menulis di Balbalan

Panduan ini untuk menulis prediksi, opini, dan analisis Anda sendiri, lalu menyiapkan website untuk Google dan AdSense. Anda tidak perlu menyentuh kode sama sekali.

## A. Sekali saja: sambungkan editor Pages CMS

1. Buka **https://app.pagescms.org** lalu klik **Sign in with GitHub**. Masuk dengan akun GitHub `bligobligo000-sudo`.
2. Saat diminta memasang aplikasi **Pages CMS**, klik **Install**. Pilih **Only select repositories**, centang **balbalan**, lalu klik **Install**.
3. Kembali ke Pages CMS dan pilih repositori **balbalan**. Di menu kiri akan muncul:
   - **Tulisan Saya**: semua prediksi, opini, dan analisis Anda
   - **Halaman Info**: Tentang Kami, Kontak, Kebijakan Privasi, Disclaimer
   - **Pengaturan Website**: nama penulis, email kontak, kode Google, dan kode AdSense
   - **Media**: foto yang pernah Anda unggah

## B. Menulis tulisan baru

1. Buka **Tulisan Saya**, lalu klik tombol untuk menambah tulisan baru (**Add**).
2. Isi formulirnya:
   - **Judul**: jelas dan memuat kata yang dicari orang. Contoh: *Prediksi Persib vs Persija, BRI Super League Pekan 8*.
   - **Jenis tulisan**: Prediksi, Opini, Analisis, atau Catatan.
   - **Tanggal terbit**: biarkan hari ini. Kalau diisi tanggal yang akan datang, tulisan otomatis terbit pada tanggal itu (paling lambat beberapa jam setelah tanggalnya tiba).
   - **Ringkasan**: 1–2 kalimat. Ringkasan ini tampil di daftar tulisan dan di hasil pencarian Google.
   - **Foto sampul** dan **Keterangan foto**: boleh dikosongkan. Lihat bagian C.
   - **Data pertandingan**: isi hanya untuk Prediksi. Website akan menampilkan kotak skor prediksi yang menarik.
   - **Isi tulisan**: ketik seperti di Word. Pakai tombol judul bagian (H2), daftar berpoin, tebal, dan kutipan supaya mudah dibaca.
3. Klik **Save**. Dalam 1–2 menit tulisan muncul di website, yaitu di bagian **Tulisan Balbalan** di beranda dan di menu **Tulisan**.

Tips lain:
- Mau menyimpan dulu tanpa menampilkan? Centang **Simpan sebagai draf**.
- Ada tulisan **CONTOH: Prediksi Atletico Madrid vs Manchester United** berstatus draf. Buka untuk melihat susunan tulisan prediksi yang baik, lalu hapus kalau sudah tidak diperlukan.

## C. Foto: boleh dan tidak boleh

Boleh dipakai:
- Foto milik Anda sendiri, misalnya foto stadion, nonton bareng, atau tangkapan layar statistik buatan sendiri.
- Foto bebas pakai dari **Unsplash**, **Pexels**, atau **Wikimedia Commons**. Tulis kreditnya di "Keterangan foto", contoh: *Foto: Unsplash/Nama Fotografer*.

Jangan dipakai:
- Foto dari situs berita, Instagram klub, atau Google Images. Foto-foto itu punya hak cipta dan bisa membuat website Anda ditolak AdSense atau diturunkan.

## D. Supaya disukai Google dan diterima AdSense

- **Tulis dengan kata-kata sendiri.** Jangan menyalin atau sekadar mengubah sedikit kata dari berita media lain. Google dan AdSense bisa mengenalinya.
- **Cukup panjang dan bermanfaat.** Untuk prediksi dan analisis, usahakan 600–1.000 kata: kondisi tim, pemain kunci, catatan pertemuan, dan alasan prediksi Anda.
- **Rutin.** Lebih baik 2–3 tulisan setiap minggu secara konsisten daripada 10 tulisan sekaligus lalu berhenti.
- **Kumpulkan dulu tulisan sebelum mendaftar AdSense.** Banyak pengelola website menyarankan sekitar 20–30 tulisan bermutu.
- **Sama sekali tanpa judi.** Jangan menulis odds, pasaran, voor, atau tautan ke situs taruhan. AdSense menolak konten seperti itu, dan judi melanggar hukum di Indonesia.
- **Isi email kontak** di Pengaturan Website, supaya halaman Kontak berisi alamat yang bisa dihubungi.

## E. Mendaftarkan website ke Google (Search Console)

1. Buka **https://search.google.com/search-console**, klik **Tambahkan properti**, lalu pilih **Awalan URL** dan isi:
   `https://bligobligo000-sudo.github.io/balbalan/`
2. Pilih metode verifikasi **Tag HTML**, lalu salin tag yang diberikan.
3. Di Pages CMS, buka **Pengaturan Website**, tempel tag tersebut di **Kode verifikasi Google Search Console**, lalu klik **Save**.
4. Tunggu sekitar 2 menit, lalu klik **Verifikasi** di Search Console.
5. Buka menu **Sitemap** di Search Console, ketik `sitemap.xml`, lalu klik **Kirim**. Google akan mulai mengenal semua tulisan Anda.

## F. AdSense: perlu domain sendiri

AdSense tidak menerima alamat `github.io`. Langkahnya:

1. **Beli domain sendiri**, misalnya `balbalan.my.id` atau `balbalan.com`. Setelah membeli, kabari saya dan saya bantu menyambungkannya ke website ini (hosting tetap gratis di GitHub).
2. Daftar di **https://adsense.google.com** memakai domain baru tersebut.
3. Salin **ID penayang** Anda (bentuknya `ca-pub-` diikuti angka). Di Pages CMS, buka **Pengaturan Website**, tempel di **ID penayang AdSense**, lalu klik **Save**. Kode AdSense dan berkas `ads.txt` akan dipasang otomatis.
4. Tunggu hasil peninjauan AdSense, biasanya beberapa hari sampai beberapa minggu.
