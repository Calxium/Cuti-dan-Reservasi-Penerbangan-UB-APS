from datetime import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for
from ..models import Pegawai
from ..services.leave_service import filter_leaves, get_employee_leave_summary


leave_bp = Blueprint('leave', __name__)


@leave_bp.route('/filter', methods=['GET', 'POST'])
def filter_leaves_view():
    """
    US-01: Memfilter Pengajuan Cuti Pegawai (Manajer HRD).
    AC-01: Rentang tanggal pencarian (tanggal awal <= tanggal akhir).
    AC-02: Pengajuan beririsan dengan rentang tanggal.
    AC-03: Menampilkan nama pegawai, tanggal mulai, tanggal selesai, durasi hari.
    AC-04: Pesan jika tidak ada pengajuan yang sesuai.
    """
    start_date_str = request.args.get('start_date') or request.form.get('start_date')
    end_date_str = request.args.get('end_date') or request.form.get('end_date')

    start_date = None
    end_date = None
    leaves = []
    has_searched = False
    error_msg = None

    if start_date_str or end_date_str:
        has_searched = True
        try:
            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

            leaves = filter_leaves(start_date, end_date)
        except ValueError as e:
            error_msg = str(e)
            flash(error_msg, "error")

    all_employees = Pegawai.query.order_by(Pegawai.nama.asc()).all()

    return render_template(
        'leave/filter.html',
        start_date_str=start_date_str or '',
        end_date_str=end_date_str or '',
        leaves=leaves,
        has_searched=has_searched,
        error_msg=error_msg,
        employees=all_employees
    )


@leave_bp.route('/employees')
def employee_list_view():
    """Daftar pegawai untuk memilih riwayat dan hak cuti."""
    employees = Pegawai.query.order_by(Pegawai.nama.asc()).all()
    return render_template('leave/employee_list.html', employees=employees)


@leave_bp.route('/employee/<int:pegawai_id>')
def employee_detail_view(pegawai_id):
    """
    US-02: Melihat Riwayat dan Sisa Hak Cuti Pegawai (Manajer HRD).
    AC-01: Memilih pegawai.
    AC-02: Menampilkan riwayat cuti tahun berjalan beserta periode, durasi, status.
    AC-03: Menampilkan jumlah hak, cuti terpakai, dan sisa cuti.
    AC-04: Pesan jika pegawai belum mempunyai riwayat cuti.
    """
    year = request.args.get('year', default=2026, type=int)
    all_employees = Pegawai.query.order_by(Pegawai.nama.asc()).all()

    try:
        summary = get_employee_leave_summary(pegawai_id, year)
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for('leave.employee_list_view'))

    return render_template(
        'leave/employee_detail.html',
        summary=summary,
        selected_pegawai_id=pegawai_id,
        employees=all_employees,
        current_year=year
    )
