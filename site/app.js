// Menampilkan isi data/berita.json (dibuat oleh scripts/ambil_berita.py) ke halaman.
const PER_HALAMAN = 24;
const KATEGORI = ["Semua", "Timnas", "Liga Indonesia", "Liga Inggris", "Liga Spanyol", "Liga Italia", "Liga Jerman", "Liga Champions"];
const ZONA = "Asia/Jakarta";

const el = (id) => document.getElementById(id);
const slug = (teks) => teks.toLowerCase().replace(/\s+/g, "-");

let semua = [];
let kategori = KATEGORI.find((k) => slug(k) === location.hash.slice(1)) || "Semua";
let kata = "";
let batas = PER_HALAMAN;
let dimuatPada = 0;

const fmtJam = new Intl.DateTimeFormat("id-ID", { timeZone: ZONA, hour: "2-digit", minute: "2-digit" });
const fmtHari = new Intl.DateTimeFormat("id-ID", { timeZone: ZONA, weekday: "long", day: "numeric", month: "long" });
const fmtPendek = new Intl.DateTimeFormat("id-ID", { timeZone: ZONA, day: "numeric", month: "short" });
const kunciHari = new Intl.DateTimeFormat("en-CA", { timeZone: ZONA }); // hasil: YYYY-MM-DD

function aman(teks) {
  return String(teks ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}

function urlAman(url) {
  return /^https?:\/\//i.test(url || "") ? url : null;
}

function waktuRelatif(tanggal) {
  const menit = Math.round((Date.now() - tanggal) / 60000);
  if (menit < 1) return "baru saja";
  if (menit < 60) return `${menit} menit lalu`;
  if (menit < 24 * 60) return `${Math.floor(menit / 60)} jam lalu`;
  return `${fmtJam.format(tanggal)} WIB`;
}

function labelHari(kunci) {
  if (kunci === kunciHari.format(new Date())) return "Hari ini";
  if (kunci === kunciHari.format(new Date(Date.now() - 864e5))) return "Kemarin";
  const teks = fmtHari.format(new Date(`${kunci}T12:00:00+07:00`));
  return teks.charAt(0).toUpperCase() + teks.slice(1);
}

function gambarHTML(berita, utama) {
  const src = urlAman(berita.gambar);
  if (!src) return `<div class="gambar kosong"></div>`;
  return `<div class="gambar"><img src="${aman(src)}" alt="" loading="${utama ? "eager" : "lazy"}" referrerpolicy="no-referrer"></div>`;
}

function infoHTML(berita) {
  const t = new Date(berita.waktu);
  return `<div class="info"><span class="sumber">${aman(berita.sumber)}</span><span class="titik"></span>` +
    `<time datetime="${aman(berita.waktu)}">${waktuRelatif(t)}</time></div>`;
}

// Berita dibuka di halaman baca milik Balbalan (dibuat oleh scripts/buat_halaman.py).
function alamatBaca(berita) {
  return berita.id ? `baca/${encodeURIComponent(berita.id)}.html` : urlAman(berita.link) || "#";
}

function kartuHTML(berita) {
  return `<a class="kartu" href="${aman(alamatBaca(berita))}">
    ${gambarHTML(berita, false)}
    <div class="teks">${infoHTML(berita)}<h4>${aman(berita.judul)}</h4><p>${aman(berita.ringkasan)}</p></div>
  </a>`;
}

function utamaHTML(berita) {
  return `<a class="utama" href="${aman(alamatBaca(berita))}">
    ${gambarHTML({ gambar: berita.gambar_besar || berita.gambar }, true)}
    <div class="teks">${infoHTML(berita)}<h2>${aman(berita.judul)}</h2><p>${aman(berita.ringkasan)}</p></div>
  </a>`;
}

function saring() {
  const q = kata.trim().toLowerCase();
  return semua.filter((b) =>
    (kategori === "Semua" || b.kategori.includes(kategori)) &&
    (!q || `${b.judul} ${b.ringkasan} ${b.sumber}`.toLowerCase().includes(q)));
}

function tampilkanChip() {
  el("saringan").innerHTML = KATEGORI.map((k) => {
    const jumlah = k === "Semua" ? semua.length : semua.filter((b) => b.kategori.includes(k)).length;
    return `<button type="button" class="chip" data-kategori="${aman(k)}" aria-pressed="${k === kategori}">` +
      `${aman(k)}<span class="jumlah">${jumlah}</span></button>`;
  }).join("");
}

function tampilkan() {
  const hasil = saring();
  const kosong = el("kosong");
  if (!hasil.length) {
    el("isi").innerHTML = "";
    el("muat").hidden = true;
    kosong.hidden = false;
    kosong.textContent = kata ? `Tidak ada berita yang cocok dengan "${kata}".` : "Belum ada berita di kategori ini.";
    return;
  }
  kosong.hidden = true;

  // Berita utama: yang terbaru dan punya gambar.
  const utama = hasil.slice(0, 5).find((b) => b.gambar) || hasil[0];
  const lain = hasil.filter((b) => b !== utama);
  const halaman = lain.slice(0, batas);

  const perHari = new Map();
  for (const b of halaman) {
    const k = kunciHari.format(new Date(b.waktu));
    if (!perHari.has(k)) perHari.set(k, []);
    perHari.get(k).push(b);
  }

  let html = utamaHTML(utama);
  for (const [k, daftar] of perHari) {
    html += `<section class="hari"><h3>${labelHari(k)}</h3><div class="grid">${daftar.map(kartuHTML).join("")}</div></section>`;
  }
  el("isi").innerHTML = html;
  el("muat").hidden = lain.length <= batas;
}

function tampilkanKerangka() {
  el("isi").innerHTML = `<div class="kerangka" style="height:320px;margin:12px 0"></div>` +
    `<div class="grid" style="margin-top:28px">${'<div class="kerangka" style="height:260px"></div>'.repeat(6)}</div>`;
}

async function muatData() {
  try {
    const r = await fetch(`data/berita.json?t=${Math.floor(Date.now() / 600000)}`);
    if (!r.ok) throw new Error(r.status);
    const data = await r.json();
    semua = data.berita || [];
    dimuatPada = Date.now();

    const diperbarui = new Date(data.diperbarui);
    const hariIni = kunciHari.format(diperbarui) === kunciHari.format(new Date());
    const jam = `${hariIni ? "" : fmtPendek.format(diperbarui) + ", "}${fmtJam.format(diperbarui)} WIB`;
    const nama = (data.sumber || []).map((s) => s.nama);
    el("keterangan").textContent = `${semua.length} berita dari ${nama.join(", ")}. Diperbarui otomatis setiap 3 jam, terakhir ${jam}.`;

    tampilkanChip();
    tampilkan();
  } catch (e) {
    el("isi").innerHTML = "";
    el("kosong").hidden = false;
    el("kosong").textContent = "Berita belum bisa dimuat. Periksa koneksi internet lalu muat ulang halaman.";
  }
}

el("saringan").addEventListener("click", (e) => {
  const tombol = e.target.closest(".chip");
  if (!tombol) return;
  kategori = tombol.dataset.kategori;
  batas = PER_HALAMAN;
  history.replaceState(null, "", kategori === "Semua" ? location.pathname : `#${slug(kategori)}`);
  tampilkanChip();
  tampilkan();
});

let jeda;
el("cari").addEventListener("input", (e) => {
  clearTimeout(jeda);
  jeda = setTimeout(() => { kata = e.target.value; batas = PER_HALAMAN; tampilkan(); }, 150);
});

el("muat").addEventListener("click", () => { batas += PER_HALAMAN; tampilkan(); });

// Gambar yang gagal dimuat diganti latar hijau bergambar bola.
document.addEventListener("error", (e) => {
  if (e.target.tagName === "IMG" && e.target.parentNode?.classList.contains("gambar")) {
    e.target.parentNode.classList.add("kosong");
    e.target.remove();
  }
}, true);

// Kalau halaman dibiarkan terbuka lama, ambil data terbaru saat dibuka lagi.
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible" && Date.now() - dimuatPada > 30 * 60000) muatData();
});

tampilkanKerangka();
muatData();
