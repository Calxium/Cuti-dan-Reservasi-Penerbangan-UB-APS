import pytest
from datetime import date
from app.services.leave_service import filter_leaves, get_employee_leave_summary, calculate_working_days
from app.models import Pegawai


def test_calculate_working_days_valid():
    """Menguji perhitungan durasi hari kalender."""
    days = calculate_working_days(date(2026, 3, 10), date(2026, 3, 12))
    assert days == 3


def test_calculate_working_days_invalid():
    """AC-01: Memastikan penolakan jika tanggal awal > tanggal akhir."""
    with pytest.raises(ValueError) as exc:
        calculate_working_days(date(2026, 3, 15), date(2026, 3, 10))
    assert "tidak boleh melebihi" in str(exc.value)


def test_filter_leaves_overlap(app):
    """
    US-01 AC-02 & AC-03:
    Menguji filter pengajuan cuti yang beririsan dengan rentang pencarian.
    Cuti Budi: 10 Maret - 12 Maret 2026.
    Pencarian: 11 Maret - 20 Maret 2026 (Beririsan).
    """
    with app.app_context():
        results = filter_leaves(date(2026, 3, 11), date(2026, 3, 20))
        assert len(results) >= 1
        budi_leave = next((leave for leave in results if leave.pegawai.nama == "Budi Santoso"), None)
        assert budi_leave is not None
        assert budi_leave.durasi == 3
        assert budi_leave.tanggal_mulai == date(2026, 3, 10)


def test_filter_leaves_empty_result(app):
    """
    US-01 AC-04:
    Menampilkan daftar kosong jika tidak ada pengajuan yang beririsan pada rentang tersebut.
    """
    with app.app_context():
        results = filter_leaves(date(2026, 1, 1), date(2026, 1, 15))
        assert len(results) == 0


def test_filter_leaves_invalid_range_raises(app):
    """
    US-01 AC-01:
    Memastikan exception jika rentang filter tanggal awal > tanggal akhir.
    """
    with app.app_context():
        with pytest.raises(ValueError):
            filter_leaves(date(2026, 5, 10), date(2026, 5, 5))


def test_get_employee_leave_summary(app):
    """
    US-02 AC-01, AC-02, AC-03:
    Memilih pegawai, melihat riwayat cuti tahun berjalan, dan sisa kuota hak cuti.
    """
    with app.app_context():
        budi = Pegawai.query.filter_by(nama="Budi Santoso").first()
        summary = get_employee_leave_summary(budi.id, 2026)

        assert summary['pegawai'].id == budi.id
        assert summary['year'] == 2026
        assert summary['has_leaves'] is True
        assert len(summary['leaves']) >= 1
        assert summary['quota'].jumlah_hak == 12
        assert summary['quota'].terpakai == 3
        assert summary['sisa_hak'] == 9  # 12 - 3 = 9


def test_get_employee_leave_summary_no_history(app):
    """
    US-02 AC-04:
    Jika pegawai belum mempunyai riwayat cuti pada tahun berjalan.
    """
    with app.app_context():
        eko = Pegawai.query.filter_by(nama="Eko Prasetyo").first()
        summary = get_employee_leave_summary(eko.id, 2026)

        assert summary['has_leaves'] is False
        assert len(summary['leaves']) == 0
        assert summary['quota'].terpakai == 0
        assert summary['sisa_hak'] == 12


def test_leave_routes_filter_view(client):
    """Uji HTTP GET endpoint /leave/filter."""
    response = client.get('/leave/filter?start_date=2026-03-01&end_date=2026-03-31')
    assert response.status_code == 200
    assert b"Budi Santoso" in response.data


def test_leave_routes_employee_detail_view(client, app):
    """Uji HTTP GET endpoint /leave/employee/<id>."""
    with app.app_context():
        budi = Pegawai.query.filter_by(nama="Budi Santoso").first()
        budi_id = budi.id

    response = client.get(f'/leave/employee/{budi_id}?year=2026')
    assert response.status_code == 200
    assert b"Sisa Hak Cuti Pegawai" in response.data
    assert b"9" in response.data
