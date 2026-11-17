from flask import Blueprint, render_template, redirect, url_for, session, flash
from ..models import Pegawai, Penerbangan, Pemesanan, SimulatedEmail


main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    total_pegawai = Pegawai.query.count()
    total_flights = Penerbangan.query.count()
    total_bookings = Pemesanan.query.count()
    recent_emails = SimulatedEmail.query.order_by(SimulatedEmail.sent_at.desc()).limit(5).all()

    return render_template(
        'index.html',
        total_pegawai=total_pegawai,
        total_flights=total_flights,
        total_bookings=total_bookings,
        recent_emails=recent_emails
    )


@main_bp.route('/switch-role/<role_name>')
def switch_role(role_name):
    allowed_roles = [
        'Manajer HRD',
        'Calon Penumpang',
        'Member Frequent Traveller',
        'Manajer Travel',
        'Pengunjung'
    ]
    if role_name in allowed_roles:
        session['current_role'] = role_name
        flash(f"Peran demo aktif dialihkan ke: {role_name}", "info")
    else:
        flash("Peran tidak dikenali.", "error")

    # Redirect ke halaman relevan berdasarkan peran
    if role_name == 'Manajer HRD':
        return redirect(url_for('leave.filter_leaves_view'))
    elif role_name == 'Member Frequent Traveller':
        return redirect(url_for('flight.itinerary_search_view'))
    elif role_name == 'Manajer Travel':
        return redirect(url_for('flight.manager_bookings_view'))
    elif role_name == 'Pengunjung':
        return redirect(url_for('flight.my_tickets_view'))
    else:
        return redirect(url_for('flight.search_single_view'))


@main_bp.route('/mailbox')
def mailbox():
    emails = SimulatedEmail.query.order_by(SimulatedEmail.sent_at.desc()).all()
    return render_template('mailbox.html', emails=emails)
