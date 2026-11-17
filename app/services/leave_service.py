from datetime import date
from typing import List, Dict, Any, Optional
from sqlalchemy import extract
from ..models import db, Pegawai, PengajuanCuti


def calculate_working_days(start_date: date, end_date: date) -> int:
    """Menghitung jumlah hari kalender pengajuan cuti."""
    if start_date > end_date:
        raise ValueError("Tanggal awal tidak boleh melebihi tanggal akhir.")
    return (end_date - start_date).days + 1


def filter_leaves(start_date: Optional[date], end_date: Optional[date]) -> List[PengajuanCuti]:
    """
    US-01: Memfilter pengajuan cuti pegawai berdasarkan irisan rentang tanggal pencarian.
    AC-01: Tanggal awal tidak boleh melebihi tanggal akhir.
    AC-02: Pengajuan cuti beririsan dengan rentang yang dipilih.
    AC-03: Menampilkan nama pegawai, tanggal mulai, tanggal selesai, dan durasi.
    AC-04: Menghasilkan list kosong jika tidak ada yang sesuai.
    """
    if start_date and end_date and start_date > end_date:
        raise ValueError("Tanggal awal pencarian tidak boleh melebihi tanggal akhir pencarian.")

    query = PengajuanCuti.query

    if start_date and end_date:
        # Irisan: cuti.tanggal_mulai <= end_date AND cuti.tanggal_selesai >= start_date
        query = query.filter(
            PengajuanCuti.tanggal_mulai <= end_date,
            PengajuanCuti.tanggal_selesai >= start_date
        )
    elif start_date:
        query = query.filter(PengajuanCuti.tanggal_selesai >= start_date)
    elif end_date:
        query = query.filter(PengajuanCuti.tanggal_mulai <= end_date)

    return query.order_by(PengajuanCuti.tanggal_mulai.asc()).all()


def get_employee_leave_summary(pegawai_id: int, year: int) -> Dict[str, Any]:
    """
    US-02: Melihat riwayat dan sisa hak cuti pegawai pada tahun berjalan.
    AC-01: Memilih pegawai.
    AC-02: Menampilkan riwayat cuti tahun berjalan beserta periode, durasi, status.
    AC-03: Menampilkan jumlah hak, cuti terpakai, dan sisa hak cuti.
    AC-04: Jika belum memiliki riwayat, sistem menyatakan tidak ada riwayat cuti.
    """
    pegawai = db.session.get(Pegawai, pegawai_id)
    if not pegawai:
        raise ValueError(f"Pegawai dengan ID {pegawai_id} tidak ditemukan.")

    quota = pegawai.get_quota_for_year(year)

    # Ambil pengajuan cuti yang dimulai pada tahun tersebut
    leaves = PengajuanCuti.query.filter(
        PengajuanCuti.pegawai_id == pegawai.id,
        extract('year', PengajuanCuti.tanggal_mulai) == year
    ).order_by(PengajuanCuti.tanggal_mulai.desc()).all()

    # Hitung ulang cuti terpakai dari pengajuan yang disetujui
    total_approved = sum(leave.durasi for leave in leaves if leave.status == 'Disetujui')
    if quota.terpakai != total_approved:
        quota.terpakai = total_approved
        db.session.commit()

    return {
        'pegawai': pegawai,
        'year': year,
        'quota': quota,
        'leaves': leaves,
        'has_leaves': len(leaves) > 0,
        'sisa_hak': quota.sisa
    }
