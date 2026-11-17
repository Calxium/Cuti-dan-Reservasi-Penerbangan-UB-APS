import pytest
from app.models import db, Penerbangan, Pemesanan, AkunPengunjung
from app.services.booking_service import (
    create_booking,
    cancel_booking,
    filter_manager_bookings,
    lookup_booking_by_code
)


def test_create_booking_success(app):
    """
    US-04 AC-01 s.d. AC-03:
    Memesan tiket dengan data wajib lengkap, kode booking unik terbentuk dan status Confirmed/Booked.
    """
    with app.app_context():
        flight = Penerbangan.query.first()
        passenger_data = {
            'nama_lengkap': 'Ahmad Dahlan',
            'tipe_identitas': 'KTP',
            'nomor_identitas': '3171012345678901',
            'email': 'ahmad.dahlan@example.com',
            'nomor_telepon': '081234567890'
        }

        booking = create_booking(flight.id, passenger_data, initial_status='Confirmed')

        assert booking.id is not None
        assert booking.kode_booking_reference.startswith("BK-")
        assert booking.status == "Confirmed"
        assert booking.penumpang.nama_lengkap == "Ahmad Dahlan"
        assert booking.e_tiket is not None
        assert booking.e_tiket.status_penerbitan == "Diterbitkan"


def test_create_booking_missing_required_fields_raises(app):
    """US-04 AC-02: Sistem menolak jika ada data wajib yang belum lengkap."""
    with app.app_context():
        flight = Penerbangan.query.first()
        incomplete_data = {
            'nama_lengkap': 'Ahmad Dahlan',
            'nomor_telepon': '081234567890'
        }

        with pytest.raises(ValueError) as exc:
            create_booking(flight.id, incomplete_data)
        assert "belum lengkap" in str(exc.value)


def test_cancel_booking_success(app):
    """
    US-05 AC-01 s.d. AC-03:
    Pembatalan tiket oleh pemilik sah, status berubah menjadi 'Dibatalkan'.
    """
    with app.app_context():
        booking = Pemesanan.query.filter_by(kode_booking_reference="BK-TESTCONF01").first()
        visitor = AkunPengunjung.query.filter_by(username="siti_rahma").first()

        updated_booking = cancel_booking(
            booking_id=booking.id,
            requester_role="Pengunjung",
            user_account_id=visitor.id,
            user_email=visitor.email_terdaftar
        )

        assert updated_booking.status == "Dibatalkan"
        assert updated_booking.e_tiket.status_penerbitan == "Belum Diterbitkan"


def test_cancel_booking_unauthorized_raises(app):
    """
    US-05 AC-01:
    Pengguna lain yang tidak berhak dilarang membatalkan pemesanan.
    """
    with app.app_context():
        booking = Pemesanan.query.filter_by(kode_booking_reference="BK-TESTCONF01").first()

        with pytest.raises(PermissionError) as exc:
            cancel_booking(
                booking_id=booking.id,
                requester_role="Pengunjung",
                user_account_id=999,
                user_email="orang.asing@example.com"
            )
        assert "tidak memiliki hak akses" in str(exc.value)


def test_cancel_booking_already_cancelled_raises(app):
    """US-05 AC-04: Menolak pembatalan jika tiket sudah dibatalkan."""
    with app.app_context():
        booking = Pemesanan.query.filter_by(kode_booking_reference="BK-TESTCONF01").first()
        booking.status = "Dibatalkan"
        db.session.commit()

        with pytest.raises(ValueError) as exc:
            cancel_booking(booking.id, requester_role="Manajer Travel")
        assert "sudah berstatus Dibatalkan" in str(exc.value)


def test_filter_manager_bookings(app):
    """
    US-10 AC-01 s.d. AC-04:
    Manajer travel memfilter berdasarkan status Confirmed, Booked, atau reset ALL.
    """
    with app.app_context():
        confirmed_bookings = filter_manager_bookings(status_filter="Confirmed")
        assert all(b.status == "Confirmed" for b in confirmed_bookings)

        booked_bookings = filter_manager_bookings(status_filter="Booked")
        assert all(b.status == "Booked" for b in booked_bookings)

        all_bookings = filter_manager_bookings(status_filter="ALL")
        assert len(all_bookings) >= 2


def test_create_booking_on_behalf_of_visitor(app):
    """
    US-12 AC-01 s.d. AC-04:
    Manajer Travel memesan tiket atas nama pengunjung dan mengaitkannya ke akun.
    """
    with app.app_context():
        flight = Penerbangan.query.first()
        visitor = AkunPengunjung.query.filter_by(username="siti_rahma").first()

        passenger_data = {
            'nama_lengkap': visitor.nama,
            'tipe_identitas': 'KTP',
            'nomor_identitas': '3201015509930005',
            'email': visitor.email_terdaftar,
            'nomor_telepon': visitor.nomor_telepon
        }

        booking = create_booking(
            penerbangan_id=flight.id,
            passenger_data=passenger_data,
            account_id=visitor.id,
            initial_status='Confirmed',
            catatan_akses='AUTHORIZED_TRAVEL_MANAGER'
        )

        assert booking.akun_pengunjung_id == visitor.id
        assert booking.penumpang.nama_lengkap == visitor.nama
        assert booking.status == "Confirmed"


def test_lookup_booking_by_code_valid(app):
    """US-14 AC-01 & AC-02: Pencarian dengan kode booking reference valid."""
    with app.app_context():
        booking = lookup_booking_by_code("BK-TESTCONF01")
        assert booking.kode_booking_reference == "BK-TESTCONF01"
        assert booking.status == "Confirmed"


def test_lookup_booking_by_code_invalid_raises(app):
    """US-14 AC-03 & AC-04: Kode tidak ditemukan menampilkan pesan kesalahan spesifik."""
    with app.app_context():
        with pytest.raises(ValueError) as exc:
            lookup_booking_by_code("BK-TIDAK-ADA-999")
        assert "Kode booking reference tidak sesuai" in str(exc.value)


def test_lookup_booking_restricted_access_raises(app):
    """US-14 AC-05: Kode ditemukan tapi tidak berhak akses harus ditolak."""
    with app.app_context():
        with pytest.raises(PermissionError) as exc:
            lookup_booking_by_code("BK-RESTRICTED99", manager_agency="AUTHORIZED_TRAVEL_MANAGER")
        assert "tidak memiliki wewenang" in str(exc.value)
