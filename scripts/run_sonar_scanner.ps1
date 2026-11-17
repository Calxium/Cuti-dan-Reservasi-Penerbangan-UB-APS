# Skrip Runner Pemindaian SonarQube Lokal / Cloud
param (
    [string]$HostUrl = $env:SONAR_HOST_URL,
    [string]$Token = $env:SONAR_TOKEN
)

if (-not $HostUrl) {
    $HostUrl = "http://localhost:9000"
}

if (-not $Token) {
    # Default token dari database lokal yang telah digenerate
    $Token = "squ_9912d56ec397299c6a0e10dd36fd8f967f6c49ee"
}

Write-Host "=== Memulai Pemindaian SonarQube ===" -ForegroundColor Cyan
Write-Host "Target Server : $HostUrl"
Write-Host "Project Key   : Calxium_Cuti-dan-Reservasi-Penerbangan-UB-APS"

# 1. Jalankan unit test untuk memastikan laporan coverage terbaru
Write-Host "`n[1/2] Menjalankan pytest dan menghasilkan coverage.xml..." -ForegroundColor Yellow
pytest -v --cov=app --cov-report=xml:coverage.xml

if ($LASTEXITCODE -ne 0) {
    Write-Host "Pytest gagal! Pemindaian SonarQube dibatalkan." -ForegroundColor Red
    exit 1
}

# 2. Jalankan SonarScanner
Write-Host "`n[2/2] Menjalankan SonarScanner via npx..." -ForegroundColor Yellow
npx -y sonarqube-scanner "-Dsonar.host.url=$HostUrl" "-Dsonar.token=$Token"

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n=== Pemindaian SonarQube Berhasil! ===" -ForegroundColor Green
    Write-Host "Buka hasil di: $HostUrl/dashboard?id=Calxium_Cuti-dan-Reservasi-Penerbangan-UB-APS" -ForegroundColor Green
} else {
    Write-Host "`nPemindaian gagal dengan kode keluar $LASTEXITCODE" -ForegroundColor Red
}
