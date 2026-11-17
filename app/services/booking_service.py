import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from ..models import db, Pemesanan, Penumpang, Penerbangan, ETiket
from .notification import send_simulated_email


def generate_booking_code() -> str:
    """Membuat kode booking acak yang unik."""
    return f"BK-{uuid.uuid4().hex[:8].upper()}"


def generate_ticket_number() -> str:
    """Membuat nomor e-tiket unik."""
    return f"TKT-{datetime.now().year}-{uuid.uuid4().hex[:6].upper()}"


def create_booking(
    penerbangan_id: int,
    passenger_data: Dict[str, Any],
    account_id: Optional[int] = None,
    initial_status: str = 'Booked',
    catatan_akses: str = 'AUTHORIZED_TRAVEL_MANAGER'
) -> Pemesanan:
    """
    US-04: Memesan tiket pilihan pengguna (Calon Penumpang).
    US-12: Memesan tiket atas nama pengunjung (Manajer Travel).
    AC: Validasi kelengkapan data wajib penumpang, generate kode booking, simpan status.
    """
    # Validasi data wajib penumpang (US-04 AC-02, US-12 AC-01)
    required_fields = ['nama_lengkap', 'nomor_identitas', 'email', 'nomor_telepon']
    missing = [f for f in required_fields if not passenger_data.get(f) or not str(passenger_data[f]).strip()]
    if missing:
        raise ValueError(f"Data penumpang belum lengkap. Kolom wajib belum terisi: {', '.join(missing)}")

    flight = db.session.get(Penerbangan, penerbangan_id)
    if not flight:
        raise ValueError(f"Penerbangan dengan ID {penerbangan_id} tidak ditemukan.")

    booking_code = generate_booking_code()
    booking = Pemesanan(
        kode_booking_reference=booking_code,
        penerbangan_id=flight.id,
        akun_pengunjung_id=account_id,
        status=initial_status,
        tanggal_pemesanan=datetime.now(),
        catatan_akses=catatan_akses
    )
    db.session.add(booking)
    db.session.flush()

    penumpang = Penumpang(
        pemesanan_id=booking.id,
        nama_lengkap=passenger_data['nama_lengkap'].strip(),
        tipe_identitas=passenger_data.get('tipe_identitas', 'KTP'),
        nomor_identitas=passenger_data['nomor_identitas'].strip(),
        email=passenger_data['email'].strip(),
        nomor_telepon=passenger_data['nomor_telepon'].strip()
    )
    db.session.add(penumpang)

    # Inisialisasi entitas E-Tiket
    if initial_status == 'Confirmed':
        ticket = ETiket(
            pemesanan_id=booking.id,
            nomor_tiket=generate_ticket_number(),
            status_penerbitan='Diterbitkan',
            waktu_terbit=datetime.now()
        )
        db.session.add(ticket)
        # US-13 AC-03: Kirim notifikasi simulasi email
        send_simulated_email(
            recipient=penumpang.email,
            subject=f"[E-Tiket] Konfirmasi Pemesanan {booking_code} - {flight.nomor_penerbangan}",
            body=f"Halo {penumpang.nama_lengkap},\n\nE-Tiket Anda untuk penerbangan {flight.nomor_penerbangan} "
                 f"({flight.asal.nama_kota} -> {flight.tujuan.nama_kota}) telah berhasil diterbitkan.\n"
                 f"Kode Booking: {booking_code}\nNomor Tiket: {ticket.nomor_tiket}\nStatus: Confirmed.\n\nTerima kasih.",
            related_booking_code=booking_code
        )
    else:
        # Belum diterbitkan
        ticket = ETiket(
            pemesanan_id=booking.id,
            nomor_tiket=generate_ticket_number(),
            status_penerbitan='Belum Diterbitkan',
            waktu_terbit=None
        )
        db.session.add(ticket)

    db.session.commit()
    return booking


def issue_ticket_for_booking(booking_id: int) -> ETiket:
    """
    US-13 AC-02 & AC-03: Menerbitkan tiket yang sudah lunas/dikonfirmasi,
    membuat e-tiket berstatus Diterbitkan, dan mengirimkan email simulasi.
    """
    booking = db.session.get(Pemesanan, booking_id)
    if not booking:
        raise ValueError("Pemesanan tidak ditemukan.")

    if booking.status == 'Dibatalkan':
        raise ValueError("Tidak dapat menerbitkan tiket untuk pemesanan yang telah dibatalkan.")

    booking.status = 'Confirmed'
    if not booking.e_tiket:
        booking.e_tiket = ETiket(
            pemesanan_id=booking.id,
            nomor_tiket=generate_ticket_number(),
            status_penerbitan='Diterbitkan',
            waktu_terbit=datetime.now()
        )
        db.session.add(booking.e_tiket)
    else:
        booking.e_tiket.status_penerbitan = 'Diterbitkan'
        booking.e_tiket.waktu_terbit = datetime.now()

    # Simulasi kirim email
    penumpang = booking.penumpang
    recipient_email = penumpang.email if penumpang else 'guest@example.com'
    passenger_name = penumpang.nama_lengkap if penumpang else 'Penumpang'

    send_simulated_email(
        recipient=recipient_email,
        subject=f"[E-Tiket Diterbitkan] Penerbangan {booking.penerbangan.nomor_penerbangan}",
        body=f"Halo {passenger_name},\n\nE-Tiket Anda ({booking.e_tiket.nomor_tiket}) telah resmi diterbitkan "
             f"untuk penerbangan {booking.penerbangan.nomor_penerbangan}. "
             f"Jadwal: {booking.penerbangan.jadwal_keberangkatan.strftime('%d %b %Y %H:%M')}.\n\nSalam,\nTravel Agency",
        related_booking_code=booking.kode_booking_reference
    )

    db.session.commit()
    return booking.e_tiket


def cancel_booking(
    booking_id: int,
    requester_role: str,
    user_email: Optional[str] = None,
    user_account_id: Optional[int] = None
) -> Pemesanan:
    """
    US-05: Membatalkan pemesanan tiket yang memenuhi ketentuan.
    AC-01: Hak akses pemesan.
    AC-02: Konfirmasi pembatalan.
    AC-03: Ubah status menjadi 'Dibatalkan'.
    AC-04: Tolak jika tidak memenuhi ketentuan pembatalan.
    """
    booking = db.session.get(Pemesanan, booking_id)
    if not booking:
        raise ValueError(f"Pemesanan dengan ID {booking_id} tidak ditemukan.")

    # Hak Akses (AC-01): Jika peran Penumpang/Pengunjung, hanya bisa membatalkan milik sendiri
    if requester_role in ['Calon Penumpang', 'Penumpang Pemesan', 'Pengunjung']:
        is_owner = False
        if user_account_id and booking.akun_pengunjung_id == user_account_id:
            is_owner = True
        elif user_email and booking.penumpang and booking.penumpang.email.lower() == user_email.lower():
            is_owner = True

        if not is_owner:
            raise PermissionError("Akses ditolak: Anda tidak memiliki hak akses untuk membatalkan pemesanan ini.")

    # Ketentuan pembatalan (AC-04):
    if booking.status == 'Dibatalkan':
        raise ValueError("Pemesanan ini sudah berstatus Dibatalkan sebelumnya.")

    # Ketentuan jadwal: tidak dapat dibatalkan jika jadwal telah berlalu
    if booking.penerbangan.jadwal_keberangkatan < datetime.now():
        raise ValueError("Pemesanan tidak dapat dibatalkan karena jadwal penerbangan telah lewat.")

    booking.status = 'Dibatalkan'
    if booking.e_tiket:
        booking.e_tiket.status_penerbitan = 'Belum Diterbitkan'

    db.session.commit()
    return booking


def filter_manager_bookings(
    status_filter: Optional[str] = None,
    manager_agency: str = 'AUTHORIZED_TRAVEL_MANAGER'
) -> List[Pemesanan]:
    """
    US-10: Memantau status seluruh pemesanan tiket (Manajer Travel).
    AC-01: Menampilkan daftar pemesanan yang dapat diakses.
    AC-02 & AC-03: Filter 'Confirmed', 'Booked', 'Waiting for Payment'.
    AC-04: Hapus filter untuk menampilkan seluruh status.
    """
    query = Pemesanan.query.filter_by(catatan_akses=manager_agency)

    allowed_statuses = ['Confirmed', 'Booked', 'Waiting for Payment']
    if status_filter and status_filter.strip() and status_filter != 'ALL':
        if status_filter in allowed_statuses:
            query = query.filter_by(status=status_filter)

    return query.order_by(Pemesanan.tanggal_pemesanan.desc()).all()


def lookup_booking_by_code(
    code: str,
    manager_agency: str = 'AUTHORIZED_TRAVEL_MANAGER'
) -> Pemesanan:
    """
    US-14: Memeriksa status pemesanan menggunakan kode booking reference.
    AC-01: Memasukkan kode booking.
    AC-02: Menampilkan status dan informasi jika ditemukan dan berhak.
    AC-03: Menampilkan pesan 'Kode booking reference tidak sesuai' jika tidak valid.
    AC-05: Jika kode ada tetapi tidak berhak akses, tolak akses.
    """
    if not code or not code.strip():
        raise ValueError("Kode booking reference tidak sesuai.")

    cleaned_code = code.strip().upper()
    booking = Pemesanan.query.filter(
        db.func.upper(Pemesanan.kode_booking_reference) == cleaned_code
    ).first()

    if not booking:
        raise ValueError("Kode booking reference tidak sesuai.")

    # AC-05: Validasi wewenang hak akses
    if booking.catatan_akses != manager_agency:
        raise PermissionError("Akses ditolak: Anda tidak memiliki wewenang untuk mengakses pemesanan ini.")

    return booking
