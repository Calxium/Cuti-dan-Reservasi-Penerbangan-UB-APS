from datetime import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from ..models import db, Lokasi, Penerbangan, Pemesanan, ProfilMember, AkunPengunjung
from ..services.flight_service import (
    search_single_flight,
    search_multi_destination_alternatives,
    compare_flights_by_preference
)
from ..services.itinerary_service import search_multi_leg_itinerary
from ..services.booking_service import (
    create_booking,
    cancel_booking,
    filter_manager_bookings,
    lookup_booking_by_code
)

flight_bp = Blueprint('flight', __name__)


@flight_bp.route('/search', methods=['GET', 'POST'])
def search_single_view():
    """
    US-03: Mencari Penerbangan Satu Tujuan (Calon Penumpang).
    AC-01: Masukkan lokasi keberangkatan, tujuan, tanggal.
    AC-02: Menampilkan jadwal, maskapai, harga tiket.
    AC-03: Pesan jika tidak ada penerbangan yang sesuai.
    """
    locations = Lokasi.query.order_by(Lokasi.nama_kota.asc()).all()

    origin_id = request.args.get('origin_id', type=int) or request.form.get('origin_id', type=int)
    dest_id = request.args.get('dest_id', type=int) or request.form.get('dest_id', type=int)
    travel_date_str = request.args.get('travel_date') or request.form.get('travel_date')

    flights = []
    has_searched = False
    error_msg = None

    if origin_id and dest_id and travel_date_str:
        has_searched = True
        try:
            travel_date = datetime.strptime(travel_date_str, '%Y-%m-%d').date()
            flights = search_single_flight(origin_id, dest_id, travel_date)
        except ValueError as e:
            error_msg = str(e)
            flash(error_msg, "error")

    return render_template(
        'flight/search_single.html',
        locations=locations,
        origin_id=origin_id,
        dest_id=dest_id,
        travel_date_str=travel_date_str or '',
        flights=flights,
        has_searched=has_searched,
        error_msg=error_msg
    )


@flight_bp.route('/book/<int:flight_id>', methods=['GET', 'POST'])
def book_flight_view(flight_id):
    """
    US-04: Memesan Tiket Pilihan Pengguna (Calon Penumpang).
    AC-01: Ringkasan detail dan harga sebelum konfirmasi.
    AC-02: Meminta data penumpang wajib, tolak jika belum lengkap.
    AC-03: Simpan pemesanan, tampilkan kode booking & status.
    """
    flight = db.get_or_404(Penerbangan, flight_id)

    if request.method == 'POST':
        passenger_data = {
            'nama_lengkap': request.form.get('nama_lengkap', ''),
            'tipe_identitas': request.form.get('tipe_identitas', 'KTP'),
            'nomor_identitas': request.form.get('nomor_identitas', ''),
            'email': request.form.get('email', ''),
            'nomor_telepon': request.form.get('nomor_telepon', '')
        }

        # Cek apakah sedang dalam sesi pengunjung terdaftar
        account_id = None
        if session.get('current_role') == 'Pengunjung':
            visitor = AkunPengunjung.query.first()
            if visitor:
                account_id = visitor.id

        try:
            booking = create_booking(
                penerbangan_id=flight.id,
                passenger_data=passenger_data,
                account_id=account_id,
                initial_status='Confirmed',  # Langsung Confirmed agar e-tiket dan simulasi email terbit
                catatan_akses='AUTHORIZED_TRAVEL_MANAGER'
            )
            session['last_booked_email'] = passenger_data['email']
            flash(f"Pemesanan berhasil dibuat! Kode Booking: {booking.kode_booking_reference}", "success")
            return redirect(url_for('flight.booking_detail_view', booking_id=booking.id))
        except ValueError as e:
            flash(str(e), "error")

    return render_template('flight/book_form.html', flight=flight)


@flight_bp.route('/booking/<int:booking_id>')
def booking_detail_view(booking_id):
    """Melihat detail pemesanan."""
    booking = db.get_or_404(Pemesanan, booking_id)
    return render_template('flight/booking_detail.html', booking=booking)


@flight_bp.route('/cancel/<int:booking_id>', methods=['POST'])
def cancel_booking_view(booking_id):
    """
    US-05: Membatalkan Pemesanan Tiket (Penumpang Pemesan).
    AC-01: Hak akses pemesan.
    AC-02: Konfirmasi pembatalan.
    AC-03: Ubah status menjadi 'Dibatalkan'.
    AC-04: Tolak jika tidak memenuhi ketentuan.
    """
    current_role = session.get('current_role', 'Calon Penumpang')

    # Identifikasi identitas pemohon dari sesi/role
    user_email = session.get('last_booked_email')
    account_id = None
    if current_role == 'Pengunjung':
        visitor = AkunPengunjung.query.first()
        if visitor:
            account_id = visitor.id
            user_email = visitor.email_terdaftar

    try:
        booking = cancel_booking(
            booking_id=booking_id,
            requester_role=current_role,
            user_email=user_email,
            user_account_id=account_id
        )
        flash(f"Pemesanan {booking.kode_booking_reference} berhasil dibatalkan.", "success")
    except (ValueError, PermissionError) as e:
        flash(str(e), "error")

    return redirect(url_for('flight.booking_detail_view', booking_id=booking_id))


@flight_bp.route('/search-multi-dest', methods=['GET', 'POST'])
def search_multi_dest_view():
    """
    US-06: Mencari Penerbangan ke Beberapa Tujuan Alternatif (Calon Penumpang).
    AC-01: Memilih minimal dua kota tujuan alternatif.
    AC-02: Menampilkan hasil sesuai untuk setiap kota tujuan.
    AC-03: Menampilkan kota tujuan, jadwal, maskapai, harga.
    AC-04: Informasi jika tidak ada penerbangan ke salah satu tujuan.
    """
    locations = Lokasi.query.order_by(Lokasi.nama_kota.asc()).all()

    origin_id = request.args.get('origin_id', type=int) or request.form.get('origin_id', type=int)
    dest_ids = request.args.getlist('dest_ids', type=int) or request.form.getlist('dest_ids', type=int)
    travel_date_str = request.args.get('travel_date') or request.form.get('travel_date')

    results = {}
    has_searched = False
    error_msg = None

    if origin_id and travel_date_str and dest_ids:
        has_searched = True
        try:
            travel_date = datetime.strptime(travel_date_str, '%Y-%m-%d').date()
            results = search_multi_destination_alternatives(origin_id, dest_ids, travel_date)
        except ValueError as e:
            error_msg = str(e)
            flash(error_msg, "error")

    return render_template(
        'flight/search_multi_dest.html',
        locations=locations,
        origin_id=origin_id,
        selected_dest_ids=dest_ids,
        travel_date_str=travel_date_str or '',
        results=results,
        has_searched=has_searched,
        error_msg=error_msg
    )


@flight_bp.route('/itinerary', methods=['GET', 'POST'])
def itinerary_search_view():
    """
    US-07: Mencari Itinerary Penerbangan Multi-Destinasi (Member Frequent Traveller).
    AC-01: Memasukkan minimal dua segmen perjalanan.
    AC-02: Validasi urutan tanggal dan keterhubungan rute antarsegmen.
    AC-03: Menampilkan pilihan itinerary dan harga total masing-masing.
    AC-04: Mengetahui jumlah pilihan itinerary yang ditemukan.
    AC-05: Pesan jika tidak ada itinerary yang sesuai.
    """
    locations = Lokasi.query.order_by(Lokasi.nama_kota.asc()).all()

    itineraries = []
    has_searched = False
    error_msg = None

    if request.method == 'POST':
        has_searched = True
        origins = request.form.getlist('segment_origin_id', type=int)
        dests = request.form.getlist('segment_dest_id', type=int)
        dates = request.form.getlist('segment_date')

        segments = []
        try:
            for o, d, dt_str in zip(origins, dests, dates):
                if o and d and dt_str:
                    seg_dt = datetime.strptime(dt_str, '%Y-%m-%d').date()
                    segments.append({'origin_id': o, 'dest_id': d, 'date': seg_dt})

            itineraries = search_multi_leg_itinerary(segments)
        except ValueError as e:
            error_msg = str(e)
            flash(error_msg, "error")

    return render_template(
        'flight/itinerary.html',
        locations=locations,
        itineraries=itineraries,
        has_searched=has_searched,
        error_msg=error_msg
    )


@flight_bp.route('/profile', methods=['GET', 'POST'])
def member_profile_view():
    """
    US-08: Melengkapi Data Profil untuk Pemeriksaan Identitas Tiket (Member Frequent Traveller).
    AC-01: Mengubah dan menyimpan data profil wajib.
    AC-02: Mengidentifikasi bidang wajib yang belum terisi.
    AC-03: Mengizinkan proses validasi jika lengkap (bukan otomatis tiket valid).
    AC-04: Tolak dengan pesan 'Data profil tidak lengkap' jika ada yang kosong.
    """
    member = ProfilMember.query.first()
    if not member:
        member = ProfilMember(
            member_code="MB-7788",
            nama_lengkap="Budi Santoso",
            kewarganegaraan="Indonesia"
        )
        db.session.add(member)
        db.session.commit()

    missing_fields = []
    validation_status = None

    if request.method == 'POST':
        action = request.form.get('action')

        member.nama_lengkap = request.form.get('nama_lengkap', '').strip()
        member.nomor_identitas = request.form.get('nomor_identitas', '').strip()
        member.kewarganegaraan = request.form.get('kewarganegaraan', '').strip()
        member.nomor_telepon = request.form.get('nomor_telepon', '').strip()
        member.alamat = request.form.get('alamat', '').strip()

        dob_str = request.form.get('tanggal_lahir')
        if dob_str:
            try:
                member.tanggal_lahir = datetime.strptime(dob_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        is_complete, missing = member.check_completeness()
        db.session.commit()

        if action == 'validate_ticket':
            if not is_complete:
                missing_fields = missing
                validation_status = 'REJECTED'
                flash("Data profil tidak lengkap. Silakan lengkapi bidang yang ditandai sebelum validasi tiket.", "error")
            else:
                validation_status = 'ALLOWED'
                msg = (
                    "Profil lengkap! Proses pemeriksaan identitas tiket diizinkan untuk dilanjutkan "
                    "(Catatan: Kelengkapan profil tidak otomatis berarti tiket valid)."
                )
                flash(msg, "success")
        else:
            flash("Data profil berhasil diperbarui.", "info")

    is_complete, missing = member.check_completeness()
    return render_template(
        'flight/profile.html',
        member=member,
        is_complete=is_complete,
        missing_fields=missing_fields,
        validation_status=validation_status
    )


@flight_bp.route('/compare', methods=['GET', 'POST'])
def compare_preferences_view():
    """
    US-09: Membandingkan Penerbangan Berdasarkan Preferensi (Member Frequent Traveller).
    AC-01: Filter berdasarkan tujuan, tanggal, dan rentang jam keberangkatan.
    AC-02: Menampilkan opsi beserta maskapai, jadwal, harga tiket.
    AC-03: Membandingkan minimal dua opsi penerbangan.
    AC-04: Pesan jika tidak ada penerbangan atau jumlah opsi belum cukup.
    """
    locations = Lokasi.query.order_by(Lokasi.nama_kota.asc()).all()

    origin_id = request.args.get('origin_id', type=int) or request.form.get('origin_id', type=int)
    dest_id = request.args.get('dest_id', type=int) or request.form.get('dest_id', type=int)
    travel_date_str = request.args.get('travel_date') or request.form.get('travel_date')
    time_bucket = request.args.get('time_bucket') or request.form.get('time_bucket') or 'all'

    flights = []
    selected_compare_flights = []
    compare_ids = request.form.getlist('compare_flight_ids', type=int)

    has_searched = False
    error_msg = None

    if origin_id and dest_id and travel_date_str:
        has_searched = True
        try:
            travel_date = datetime.strptime(travel_date_str, '%Y-%m-%d').date()
            flights = compare_flights_by_preference(origin_id, dest_id, travel_date, time_bucket)
        except ValueError as e:
            error_msg = str(e)
            flash(error_msg, "error")

    if compare_ids:
        if len(compare_ids) < 2:
            flash("Pilih minimal dua penerbangan untuk melakukan perbandingan.", "warning")
        else:
            selected_compare_flights = Penerbangan.query.filter(Penerbangan.id.in_(compare_ids)).all()

    return render_template(
        'flight/compare.html',
        locations=locations,
        origin_id=origin_id,
        dest_id=dest_id,
        travel_date_str=travel_date_str or '',
        time_bucket=time_bucket,
        flights=flights,
        selected_compare_flights=selected_compare_flights,
        has_searched=has_searched,
        error_msg=error_msg
    )


@flight_bp.route('/manager/bookings')
def manager_bookings_view():
    """
    US-10: Memantau Status Seluruh Pemesanan Tiket (Manajer Travel).
    AC-01: Menampilkan seluruh pemesanan yang berhak diakses.
    AC-02 & AC-03: Filter Confirmed, Booked, Waiting for Payment.
    AC-04: Reset filter untuk melihat semua status.
    AC-05: Pesan jika tidak ada pemesanan dengan status yang dipilih.
    """
    status_filter = request.args.get('status', default=None)
    bookings = filter_manager_bookings(status_filter)

    return render_template(
        'flight/manager_bookings.html',
        bookings=bookings,
        current_status_filter=status_filter or 'ALL'
    )


@flight_bp.route('/visitor/search', methods=['GET', 'POST'])
def visitor_search_view():
    """
    US-11: Mencari Tiket untuk Pengunjung (Manajer Travel).
    AC-01: Masukkan lokasi keberangkatan, tujuan, tanggal.
    AC-02: Menampilkan daftar penerbangan, maskapai, jadwal, harga.
    AC-03: Pesan jika tidak ada penerbangan sesuai kriteria.
    """
    locations = Lokasi.query.order_by(Lokasi.nama_kota.asc()).all()

    origin_id = request.args.get('origin_id', type=int) or request.form.get('origin_id', type=int)
    dest_id = request.args.get('dest_id', type=int) or request.form.get('dest_id', type=int)
    travel_date_str = request.args.get('travel_date') or request.form.get('travel_date')

    flights = []
    has_searched = False
    error_msg = None

    if origin_id and dest_id and travel_date_str:
        has_searched = True
        try:
            travel_date = datetime.strptime(travel_date_str, '%Y-%m-%d').date()
            flights = search_single_flight(origin_id, dest_id, travel_date)
        except ValueError as e:
            error_msg = str(e)
            flash(error_msg, "error")

    return render_template(
        'flight/visitor_search.html',
        locations=locations,
        origin_id=origin_id,
        dest_id=dest_id,
        travel_date_str=travel_date_str or '',
        flights=flights,
        has_searched=has_searched,
        error_msg=error_msg
    )


@flight_bp.route('/visitor/book/<int:flight_id>', methods=['GET', 'POST'])
def visitor_book_view(flight_id):
    """
    US-12: Memesan Tiket atas Nama Pengunjung (Manajer Travel).
    AC-01: Memilih penerbangan dan memasukkan data pengunjung valid.
    AC-02: Menampilkan identitas pengunjung dan detail sebelum konfirmasi.
    AC-03: Menyimpan pemesanan atas nama pengunjung dan mengaitkan akun.
    AC-04: Menampilkan kode pemesanan dan statusnya.
    """
    flight = db.get_or_404(Penerbangan, flight_id)
    registered_visitors = AkunPengunjung.query.order_by(AkunPengunjung.nama.asc()).all()

    if request.method == 'POST':
        account_id = request.form.get('account_id', type=int)
        passenger_data = {
            'nama_lengkap': request.form.get('nama_lengkap', ''),
            'tipe_identitas': request.form.get('tipe_identitas', 'KTP'),
            'nomor_identitas': request.form.get('nomor_identitas', ''),
            'email': request.form.get('email', ''),
            'nomor_telepon': request.form.get('nomor_telepon', '')
        }

        try:
            booking = create_booking(
                penerbangan_id=flight.id,
                passenger_data=passenger_data,
                account_id=account_id if account_id else None,
                initial_status='Confirmed',
                catatan_akses='AUTHORIZED_TRAVEL_MANAGER'
            )
            flash(f"Pemesanan atas nama pengunjung berhasil dibuat! Kode: {booking.kode_booking_reference}", "success")
            return redirect(url_for('flight.booking_detail_view', booking_id=booking.id))
        except ValueError as e:
            flash(str(e), "error")

    return render_template(
        'flight/visitor_book_form.html',
        flight=flight,
        visitors=registered_visitors
    )


@flight_bp.route('/my-tickets')
def my_tickets_view():
    """
    US-13: Mengakses E-Tiket yang Telah Diterbitkan (Pengunjung).
    AC-01: Pengunjung hanya dapat melihat pemesanan terkait akunnya.
    AC-02: Sistem menampilkan e-tiket setelah berstatus Diterbitkan.
    AC-03: Sistem mengirim e-tiket ke email terdaftar (simulasi email).
    AC-04: Tidak menyatakan e-tiket tersedia ketika tiket belum diterbitkan.
    """
    visitor = AkunPengunjung.query.first()
    bookings = []
    if visitor:
        bookings = Pemesanan.query.filter_by(akun_pengunjung_id=visitor.id).order_by(Pemesanan.tanggal_pemesanan.desc()).all()

    return render_template('flight/my_tickets.html', visitor=visitor, bookings=bookings)


@flight_bp.route('/manager/lookup', methods=['GET', 'POST'])
def manager_lookup_view():
    """
    US-14: Memeriksa Status Pemesanan Menggunakan Kode Booking (Manajer Travel).
    AC-01: Memasukkan kode booking reference.
    AC-02: Menampilkan status dan informasi jika kode ditemukan dan berhak akses.
    AC-03: Pesan 'Kode booking reference tidak sesuai' jika tidak valid.
    AC-04: Memasukkan kembali untuk mencoba lagi.
    AC-05: Jika kode ada tetapi tidak berhak akses, tolak akses.
    """
    code_input = request.args.get('code') or request.form.get('code')
    booking = None
    error_msg = None
    has_searched = False

    if code_input:
        has_searched = True
        try:
            booking = lookup_booking_by_code(code_input, manager_agency='AUTHORIZED_TRAVEL_MANAGER')
        except (ValueError, PermissionError) as e:
            error_msg = str(e)
            flash(error_msg, "error")

    return render_template(
        'flight/manager_lookup.html',
        code_input=code_input or '',
        booking=booking,
        has_searched=has_searched,
        error_msg=error_msg
    )
