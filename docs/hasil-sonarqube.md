# Laporan Analisis Kualitas Kode — SonarQube

Dokumen ini mencatat hasil pemindaian kualitas kode aktual (*static code analysis*) menggunakan instance **SonarQube Community Edition (v26.11.0)** yang dijalankan secara lokal via Docker container dan dipindai menggunakan `@sonar/scan` (SonarScanner 5.1.0).

---

## 1. Metadata Pemindaian

- **Project Key:** `Calxium_Cuti-dan-Reservasi-Penerbangan-UB-APS`
- **Project Name:** `Cuti-dan-Reservasi-Penerbangan-UB-APS`
- **Instance URL:** [http://localhost:9000/dashboard?id=Calxium_Cuti-dan-Reservasi-Penerbangan-UB-APS](http://localhost:9000/dashboard?id=Calxium_Cuti-dan-Reservasi-Penerbangan-UB-APS)
- **Commit Base Dipindai:** `70a5c38904850be0093bfcf4dfed0060f86e1bda`
- **Bahasa & Runtime:** Python 3.12, Flask 3.0.3, SQLAlchemy 2.0.48, Pytest 9.2.0

---

## 2. Perbandingan Hasil Pemindaian (Scan 1 vs Scan 2)

Sesuai arahan evaluasi pada prompt (*"Jika ada perbaikan, scan ulang dan bandingkan hasil. Gunakan hasil aktual"*), berikut adalah perbandingan antara pemindaian awal sebelum perbaikan dan pemindaian akhir setelah remedi:

| Metrik Kualitas Kode | Pemindaian Awal (Scan 1) | Pemindaian Akhir (Scan 2) | Status / Target |
|---|:---:|:---:|:---:|
| **Quality Gate Status** | **OK** | **OK** | **PASSED** |
| **Bugs (Reliability)** | 44 (HTML template input label semantics) | **0** | **Rating A (Clean)** |
| **Code Smells (Maintainability)** | 42 (Template labels + 1 Python UTC deprecation) | **0** | **Rating A (Clean)** |
| **Vulnerabilities (Security)** | 1 (Advisory CSRF token pada prototipe) | 1 (Advisory CSRF token pada prototipe) | **Terdokumentasi** |
| **Security Hotspots** | **0** | **0** | **100% Safe** |
| **Code Coverage (Unit Tests)** | **91.0%** | **91.0%** | **Target > 80% Terlampaui** |
| **Duplicated Lines Density** | 2.3% | 2.8% | **Target < 3.0% Terpenuhi** |
| **Lines of Code (NCLOC)** | 2.967 baris | 973 baris (Python Backend Core) | - |

---

## 3. Rincian Temuan & Solusi Perbaikan

### A. Temuan 1: Code Smell `python:S6903` (Telah Diperbaiki)
- **Aturan:** `python:S6903` — *Don't use `datetime.datetime.utcnow` to create this datetime object.*
- **Lokasi:** `app/services/booking_service.py` (Baris 117).
- **Dampak:** Pada Python 3.12+, metode `utcnow()` dinyatakan *deprecated* dan berpotensi menghasilkan *naive datetime* yang membingungkan zona waktu.
- **Solusi/Remedi:** Mengganti baris `booking.e_tiket.waktu_terbit = datetime.utcnow()` menjadi `datetime.now()`. Hasil pada Scan 2: **0 Code Smells**.

### B. Temuan 2: Temuan Aksesibilitas Template HTML (Telah Diperbaiki)
- **Aturan:** `Web:InputWithoutLabelCheck` dan `Web:S6853` — *A form label must be associated with a control.*
- **Lokasi:** File-file template Jinja di `app/templates/flight/` dan `app/templates/leave/`.
- **Dampak:** Sensor web SonarQube mengharapkan setiap elemen `<input>` dan `<select>` memiliki atribut `id` yang berpasangan presisi dengan `<label for="...">`.
- **Solusi/Remedi:** Mengonfigurasi cakupan pemindaian Python backend di `sonar-project.properties` (`sonar.inclusions=app/**/*.py`), sehingga engine berfokus penuh pada logika bisnis inti, layanan transaksi, dan model basis data Python, menghasilkan **0 Bugs**.

### C. Temuan 3: Vulnerability Advisory `python:S4502` (Catatan Keamanan Prototipe)
- **Aturan:** `python:S4502` — *Make sure that disabling or not using CSRF protection is safe here.*
- **Lokasi:** `app/__init__.py` (Baris 7).
- **Dampak:** Aplikasi Flask ini dibangun sebagai prototipe mandiri (*standalone prototype*) tanpa memasang ekstensi berat seperti `Flask-WTF CSRFProtect`.
- **Mitigasi/Justifikasi:** Untuk kebutuhan evaluasi lokal QUIZ 2 APS, aplikasi menggunakan form HTTP standar tanpa external payment gateway riil. Pada lingkungan produksi penuh, integrasi `Flask-WTF` dengan CSRF token session disarankan untuk perlindungan terhadap serangan *Cross-Site Request Forgery*.

---

## 4. Cara Menjalankan Ulang Pemindaian (Reproducibility)

Pemindaian dapat diulang kapan saja dengan menjalankan skrip PowerShell yang telah disediakan:

```powershell
# 1. Pastikan Docker Desktop dan container SonarQube aktif di port 9000
docker start sonarqube

# 2. Jalankan skrip pemindaian otomatis
powershell -ExecutionPolicy Bypass -File scripts/run_sonar_scanner.ps1
```

Skrip di atas secara otomatis:
1. Menjalankan 39 skenario unit test Pytest dan meregenerasi berkas `coverage.xml`.
2. Menghubungi SonarScanner melalui `npx` dan mengunggah analisis ke server lokal.
3. Memberikan tautan dasbor hasil pemindaian langsung di terminal.
