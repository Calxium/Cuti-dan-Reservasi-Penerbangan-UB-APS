# QUIZ 2 APS — Manajemen Cuti dan Reservasi Penerbangan

Prototipe aplikasi web terintegrasi untuk memenuhi tugas **QUIZ 2 Analisis dan Perancangan Sistem (APS)** Teknik Informatika FILKOM Universitas Brawijaya. Sistem ini mengimplementasikan secara menyeluruh **14 User Story (US-01 s.d. US-14)** yang mencakup dua modul bisnis: **Manajemen Cuti Pegawai** dan **Reservasi Penerbangan**.

---

## 1. Ringkasan Dua Modul Sistem

Sistem dirancang sebagai satu kesatuan aplikasi web yang memisahkan konteks bisnis secara jelas:
1. **Modul Manajemen Cuti Pegawai (US-01 s.d. US-02):**
   - **Filter Pengajuan Cuti (US-01):** Menyaring pengajuan cuti pegawai berdasarkan irisan rentang tanggal pencarian (*overlap formula*), validasi tanggal awal $\le$ tanggal akhir, dan kalkulasi durasi cuti.
   - **Riwayat & Sisa Hak Cuti Pegawai (US-02):** Memilih pegawai, menampilkan riwayat cuti tahun berjalan (periode, durasi, status), serta ringkasan kuota hak cuti, cuti terpakai, dan sisa hak cuti dengan pola antarmuka *June Dashboard*.
2. **Modul Reservasi Penerbangan (US-03 s.d. US-14):**
   - **Pencarian & Pemesanan Satu Tujuan (US-03, US-04):** Antarmuka kartu tiket ala Traveloka, validasi data wajib penumpang, dan penerbitan kode booking referensi unik.
   - **Pembatalan Tiket (US-05):** Pembatalan berbasis kepemilikan akses (*authorization guard*) dengan modal konfirmasi dan pemeriksaan syarat batas waktu keberangkatan.
   - **Pencarian Multi-Tujuan Alternatif (US-06):** Pencarian ke minimal dua kota tujuan alternatif dalam satu kali submit dengan pelaporan hasil per destinasi.
   - **Itinerary Multi-Destinasi (US-07):** Pemilihan multi-segmen perjalanan dengan validasi keterhubungan rute (tujuan segmen $N$ = asal segmen $N+1$), validasi tanggal kronologis, dan kalkulasi total harga tiket.
   - **Profil Member & Validasi Tiket (US-08):** Pengisian data profil wajib member frequent traveller dan validasi syarat pemeriksaan tiket penumpang.
   - **Komparasi Preferensi (US-09):** Penyaringan berdasarkan jam keberangkatan (pagi, siang, malam) serta perbandingan tabel berdampingan (*side-by-side*) minimal dua penerbangan.
   - **Monitoring & Pemesanan Manajer Travel (US-10, US-11, US-12, US-14):** Pemantauan seluruh status booking (*Confirmed*, *Booked*, *Waiting for Payment*), pemesanan atas nama pengunjung dengan penautan akun, dan pelacakan status via kode booking.
   - **E-Tiket & Simulasi Email (US-13):** Penerbitan tiket elektronik hanya saat status sah dan simulasi pengiriman notifikasi email lokal tanpa dependensi SMTP pihak ketiga.

📄 **Matriks Keterlacakan Lengkap:** Lihat [docs/matriks-user-story.md](docs/matriks-user-story.md) untuk pemetaan detail setiap User Story ke kode dan skenario uji.

---

## 2. Prasyarat Lingkungan

- **Python:** Versi 3.10, 3.11, atau 3.12 (Diuji pada Python 3.12.2).
- **Node.js & npm:** (Opsional, untuk SonarScanner otomatis via `npx`).
- **Docker Desktop:** (Opsional, untuk menjalankan SonarQube Community Edition lokal).
- **Browser:** Google Chrome, Microsoft Edge, atau Mozilla Firefox.

---

## 3. Panduan Instalasi dan Menjalankan Aplikasi

Jalankan perintah berikut secara berurutan pada terminal terminal / PowerShell di dalam direktori proyek:

```bash
# 1. Masuk ke folder proyek
cd "D:\kuliah\TIF\SMT 3\APS\QUIZ 2 APS"

# 2. Pasang pustaka dependensi yang dibutuhkan
pip install -r requirements.txt

# 3. Jalankan pengisian data awal (seed synthetic database)
python seed_data.py

# 4. Jalankan aplikasi web
python run.py
```

Setelah aplikasi berjalan, buka browser pada URL:
👉 **[http://127.0.0.1:5000/](http://127.0.0.1:5000/)**

---

## 4. Cara Mencoba dan Berpindah Peran Demo

Untuk memudahkan evaluasi oleh Dosen atau Asisten Praktikum, aplikasi dilengkapi dengan **Demo Role Switcher** instan pada bilah navigasi atas (*topbar*). Anda dapat memilih salah satu dari 5 persona berikut kapan saja:

1. **Manajer HRD:**
   - URL Cepat: `http://127.0.0.1:5000/leave/filter`
   - Buka menu **Filter Pengajuan Cuti (US-01)** untuk menguji rentang tanggal beririsan (misal: `2026-03-01` s.d. `2026-03-31`).
   - Buka menu **Riwayat & Kuota Pegawai (US-02)**, pilih pegawai "Budi Santoso" atau "Eko Prasetyo" (pegawai yang belum pernah cuti).
2. **Calon Penumpang (Umum):**
   - URL Cepat: `http://127.0.0.1:5000/flight/search`
   - Buka menu **Cari 1 Tujuan & Pesan (US-03/04)**, pilih Jakarta (CGK) ke Bali (DPS), tanggal `2026-11-20`.
   - Klik **Pilih Tiket**, lengkapi formulir penumpang wajib, dan dapatkan kode booking.
   - Buka menu **Cari Multi-Tujuan Alternatif (US-06)**, pilih asal Jakarta dan centang minimal dua tujuan (misal Surabaya & Bali).
3. **Member Frequent Traveller:**
   - URL Cepat: `http://127.0.0.1:5000/flight/itinerary`
   - Buka menu **Itinerary Multi-Destinasi (US-07)**, susun Segmen 1 (Jakarta ke Surabaya) dan Segmen 2 (Surabaya ke Bali).
   - Buka menu **Profil Member & Validasi (US-08)** untuk mencoba pengujian kelengkapan profil dan tombol "Uji Validasi Identitas Tiket".
   - Buka menu **Komparasi Preferensi (US-09)**, filter jam pagi/malam, centang 2 tiket, dan klik "Bandingkan Opsi Terpilih".
4. **Manajer Travel:**
   - URL Cepat: `http://127.0.0.1:5000/flight/manager/bookings`
   - Buka menu **Monitoring Seluruh Booking (US-10)** dan klik tombol filter status (`Confirmed`, `Booked`, `Waiting for Payment`, atau reset `Semua Status`).
   - Buka menu **Pesan Tiket Pengunjung (US-11/12)** untuk memesankan tiket atas nama tamu dan menautkan akun pengunjung terdaftar.
   - Buka menu **Lacak Kode Booking (US-14)**, masukkan kode `BK-TESTCONF01` untuk melihat status, atau kode acak untuk melihat penolakan.
5. **Pengunjung Terdaftar:**
   - URL Cepat: `http://127.0.0.1:5000/flight/my-tickets`
   - Buka menu **E-Tiket Saya (US-13)** untuk melihat e-tiket akun Siti Rahma dan membuka **Simulated Mailbox** lokal.

---

## 5. Menjalankan Pengujian Otomatis (Pytest)

Seluruh 14 User Story telah dilengkapi dengan unit test dan integration test otomatis dengan coverage mencapai **91%**.

Jalankan perintah berikut untuk menjalankan seluruh pengujian dan menghasilkan laporan coverage:

```bash
# Menjalankan 39 test cases dan menghasilkan laporan cakupan kode
pytest -v --cov=app --cov-report=term-missing --cov-report=xml:coverage.xml
```

Hasil pengujian: **39 Passed**, **0 Failed**, **0 Warnings**.

---

## 6. Pemindaian Kualitas Kode (SonarQube)

Aplikasi telah disiapkan dengan konfigurasi `sonar-project.properties` dan script runner pemindaian otomatis.

### Menjalankan SonarQube Lokal (Docker)
Jika menggunakan SonarQube lokal:
1. Pastikan container SonarQube aktif:
   ```bash
   docker run -d --name sonarqube -e SONAR_ES_BOOTSTRAP_CHECKS_DISABLE=true -p 9000:9000 sonarqube:community
   ```
2. Jalankan skrip runner pemindaian:
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts/run_sonar_scanner.ps1
   ```
3. Variabel lingkungan yang dapat disesuaikan (opsional):
   - `SONAR_HOST_URL`: Default `http://localhost:9000`
   - `SONAR_TOKEN`: Token autentikasi SonarQube / SonarCloud

📄 **Laporan Analisis SonarQube Aktual:** Lihat [docs/hasil-sonarqube.md](docs/hasil-sonarqube.md) untuk ringkasan commit, status Quality Gate, dan metrik Bugs/Code Smells.

---

## 7. Catatan Observasi & Keterbatasan Prototipe

- 📄 **Catatan Observasi Vibe Coding:** Lihat [docs/observasi-vibe-coding.md](docs/observasi-vibe-coding.md) untuk detail alur pengembangan, bug awal yang ditemukan, perbaikan teknis, dan refleksi evaluasi.
- **Keterbatasan Prototipe:** Pengiriman email dilakukan via simulasi lokal di database SQLite (`SimulatedEmail`), dataset jadwal penerbangan sintetis untuk rute kota-kota besar di Indonesia, dan mekanisme pembayaran instan tanpa payment gateway pihak ketiga nyata.
