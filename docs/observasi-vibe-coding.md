# Catatan Observasi Vibe Coding — QUIZ 2 APS

Dokumen ini mencatat seluruh proses observasi pengembangan prototipe berbasis *vibe coding* (pengembangan kolaboratif cepat antara asisten AI dan pengembang), hasil pengujian riil yang benar-benar dijalankan, kegagalan awal yang ditemukan beserta perbaikannya, dan keterbatasan prototipe yang tersisa.

Dokumen ini disiapkan sebagai referensi autentik untuk menjawab pertanyaan evaluasi dosen/asisten (Brone).

---

## 1. Pendekatan dan Alur Kerja Vibe Coding

Pengembangan prototipe untuk 14 User Story (US-01 s.d. US-14) dilakukan melalui pendekatan terstruktur:
1. **Analisis Kebutuhan & Traceability:**
   Membaca secara mendalam naskah `Requirements_14_User_Stories.md`, dokumen analisis alur, dan Domain Model PlantUML (`DM-01`). Setiap acceptance criteria (AC) dipetakan ke level arsitektur kode.
2. **Arsitektur Modular & Pemisahan Domain:**
   - Modul Manajemen Cuti Pegawai (US-01 s.d. US-02).
   - Modul Reservasi Penerbangan (US-03 s.d. US-14).
   - Desain UI mengacu pada standar visual modern: Shadcn dashboard layout, June Dashboard pattern (metrik cuti & filter tabel), dan Traveloka flight booking pattern (kartu penerbangan terstruktur).
3. **Mekanisme Demo Role Switcher:**
   Untuk mempermudah pengujian dosen/evaluator, disediakan bilah *Role Switcher* instan di bagian atas antarmuka web yang mencakup 5 persona (Manajer HRD, Calon Penumpang, Member Frequent Traveller, Manajer Travel, dan Pengunjung).
4. **Validasi Berulang & Static Analysis:**
   Setiap fungsi bisnis diuji menggunakan `pytest`, `pytest-cov`, `flake8`, dan pemindaian engine `SonarQube`.

---

## 2. Hasil Uji Aktual yang Dijalankan

Pengujian dilakukan melalui dua tingkatan: pengujian unit/integrasi otomatis dan verifikasi UI manual.

### A. Hasil Pengujian Otomatis (Pytest & Coverage)
- **Total Test Cases:** 39 skenario uji (mencakup 100% dari US-01 s.d. US-14).
- **Hasil:** **39 Passed**, **0 Failed**, **0 Errors**, **0 Warnings**.
- **Waktu Eksekusi:** ~5,4 detik.
- **Coverage Aktual:** **91%** pada seluruh direktori aplikasi (`app/`).

Rincian file pengujian:
1. `tests/test_leave_management.py` (8 skenario): Menguji irisan rentang tanggal cuti (*overlap logic*), penolakan tanggal awal > tanggal akhir, perhitungan durasi, dan ringkasan hak/sisa cuti pegawai.
2. `tests/test_flight_search.py` (9 skenario): Menguji pencarian satu tujuan, penolakan pencarian rute identik, pencarian tujuan alternatif $\ge 2$ kota, validasi keterhubungan dan kronologi itinerary multi-segmen, serta perbandingan preferensi jam (pagi/malam).
3. `tests/test_booking_lifecycle.py` (10 skenario): Menguji kelengkapan data wajib penumpang, kode booking unik, hak akses pembatalan tiket, pencegahan pembatalan ganda/kedaluwarsa, pemesanan atas nama pengunjung, dan pelacakan kode booking dengan restriksi wewenang.
4. `tests/test_member_and_eticket.py` (4 skenario): Menguji kelengkapan profil member frequent traveller, penerbitan e-tiket, pembatasan akses hanya untuk tiket yang sah, dan isolasi akun pengunjung.
5. `tests/test_ui_routes.py` (8 skenario integrasi): Menguji endpoint HTTP, penanganan session role switching, formulir pencarian, dan simulated mailbox.

---

## 3. Kegagalan Awal & Perbaikan yang Dilakukan

Selama proses *vibe coding* dan iterasi awal, beberapa isu teknis ditemukan dan diselesaikan secara langsung:

| No | Isu / Kegagalan Awal yang Ditemukan | Penyebab Teknis | Solusi & Perbaikan yang Diterapkan |
|:---:|---|---|---|
| 1 | **Deprecation Warning `datetime.utcnow()`** | Pada Python 3.12, fungsi `datetime.utcnow()` dinyatakan *deprecated* dan memicu peringatan runtime serta berpotensi menjadi *Code Smell* di SonarQube. | Seluruh pemanggilan diganti dengan `datetime.now()`, menghasilkan eksekusi bebas warning. |
| 2 | **ModuleNotFoundError `flask_sqlalchemy`** | Dependensi belum terinstal di lingkungan Python lokal saat pertama kali menjalankan database seeder. | Menginstal paket `flask-sqlalchemy>=3.1.0` dan mencatatnya ke dalam `requirements.txt`. |
| 3 | **SQLAlchemy 2.0 `LegacyAPIWarning`** | Pemanggilan `Model.query.get(id)` dan `Model.query.get_or_404(id)` merupakan pola legacy 1.x yang tidak dianjurkan di SQLAlchemy 2.0. | Melakukan refactoring ke `db.session.get(Model, id)` dan `db.get_or_404(Model, id)`. |
| 4 | **Pelanggaran Standar Linter (Flake8)** | Ditemukan import yang tidak terpakai (`F401`), nama variabel satu huruf ambigu `l` (`E741`), dan panjang baris melebihi batas (`E501`). | Membersihkan seluruh unused imports, mengubah nama variabel iterasi menjadi deskriptif (`leave`), merapikan pemotongan string panjang, sehingga `flake8 app tests` mencapai **0 error**. |
| 5 | **Kegagalan Otorisasi Pembatalan Tiket Tamu (US-05)** | Pada alur pemesanan tamu (*Calon Penumpang*), sistem belum mengikat email pemesan ke sesi aktif, sehingga ketika tamu menekan tombol batalkan tiket, sistem menganggapnya bukan pemilik tiket. | Menambahkan penyimpanan `session['last_booked_email']` saat formulir pemesanan berhasil, sehingga pemesan sah dapat langsung memproses pembatalan dari antarmuka web. |

---

## 4. Keterbatasan Prototipe yang Tersisa

Meskipun seluruh 14 User Story dan Acceptance Criteria telah terpenuhi secara fungsional, prototipe memiliki beberapa batasan yang dirancang sengaja untuk kebutuhan simulasi lokal:

1. **Simulasi Pengiriman Email Lokal (US-13):**
   - Tidak menggunakan gateway SMTP pihak ketiga (seperti SendGrid atau Mailgun) untuk menghindari ketergantungan kredensial eksternal.
   - Sebagai gantinya, sistem menyediakan **Simulated Mailbox** lokal berbasis database SQLite yang mencatat waktu kirim, alamat penerima, subjek, nomor tiket, dan isi pesan, yang dapat diinspeksi langsung pada bilah menu navigasi.
2. **Dataset Penerbangan Sintetis:**
   - Data maskapai dan penerbangan dibatasi pada rute domestik Indonesia populer (Jakarta, Surabaya, Denpasar, Medan, Yogyakarta) dengan variasi waktu pagi, siang, dan malam.
3. **Mekanisme Pembayaran Instan:**
   - Pemesanan tiket langsung menghasilkan status `Confirmed` atau `Booked` tanpa integrasi payment gateway perbankan nyata.
4. **Isolasi Database Sesi:**
   - Menggunakan SQLite lokal (`aps_quiz2.db`) dan SQLite in-memory untuk pengujian, yang sangat portabel dan tidak membutuhkan instalasi server database eksternal terpisah.

---

## 5. Ringkasan Refleksi untuk Brone

- **Tingkat Kepatuhan Spesifikasi:** Seluruh nomor task dan kriteria penerimaan dari US-01 hingga US-14 telah diuji dan terbukti valid.
- **Kualitas Kode:** Lolos audit statis PEP-8 (Flake8) tanpa peringatan, unit test otomatis dengan coverage 91%, dan terintegrasi dengan SonarQube Community Edition.
- **Kemudahan Evaluasi Dosen:** Penguji dapat mendemokan sistem dari web browser secara mandiri hanya dengan menggunakan bilah *Role Switcher* di bagian atas layar.
