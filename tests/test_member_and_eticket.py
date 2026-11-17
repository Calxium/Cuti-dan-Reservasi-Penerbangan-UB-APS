from datetime import date
from app.models import ProfilMember, Pemesanan
from app.services.booking_service import issue_ticket_for_booking
from app.services.notification import get_simulated_emails


def test_member_profile_completeness_check(app):
    """
    US-08 AC-01 & AC-02:
    Memeriksa kelengkapan profil member frequent traveller dan mendeteksi kolom kosong.
    """
    with app.app_context():
        # Member dengan profil belum lengkap
        member = ProfilMember(
            member_code="MB-INCOMPLETE",
            nama_lengkap="Calon Member",
            nomor_identitas=""  # Kosong
        )
        is_complete, missing = member.check_completeness()
        assert is_complete is False
        assert "Nomor Identitas (NIK/Paspor)" in missing
        assert "Tanggal Lahir" in missing
        assert "Kewarganegaraan" in missing

        # Lengkapi seluruh profil
        member.nomor_identitas = "3171012345678901"
        member.tanggal_lahir = date(1990, 5, 20)
        member.kewarganegaraan = "Indonesia"
        member.nomor_telepon = "08123456789"
        is_complete, missing = member.check_completeness()
        assert is_complete is True
        assert len(missing) == 0


def test_eticket_access_only_when_issued(app):
    """
    US-13 AC-01, AC-02, AC-04:
    E-tiket hanya berstatus Diterbitkan jika pemesanan Confirmed / Issued.
    Jika masih Booked/Waiting, e-tiket belum boleh dinyatakan tersedia.
    """
    with app.app_context():
        # Booking 1: Confirmed (BK-TESTCONF01)
        b_conf = Pemesanan.query.filter_by(kode_booking_reference="BK-TESTCONF01").first()
        assert b_conf.e_tiket is not None
        assert b_conf.e_tiket.status_penerbitan == "Diterbitkan"

        # Booking 2: Booked (BK-TESTBOOK02) -> belum diterbitkan
        b_booked = Pemesanan.query.filter_by(kode_booking_reference="BK-TESTBOOK02").first()
        if b_booked.e_tiket:
            assert b_booked.e_tiket.status_penerbitan != "Diterbitkan"


def test_eticket_issuance_triggers_simulated_email(app):
    """
    US-13 AC-03:
    Penerbitan tiket memicu simulasi pengiriman email ke alamat terdaftar.
    """
    with app.app_context():
        b_booked = Pemesanan.query.filter_by(kode_booking_reference="BK-TESTBOOK02").first()

        # Terbitkan tiket
        tkt = issue_ticket_for_booking(b_booked.id)
        assert tkt.status_penerbitan == "Diterbitkan"

        # Periksa simulated outbox email
        emails = get_simulated_emails(recipient=b_booked.penumpang.email)
        assert len(emails) >= 1
        assert "E-Tiket" in emails[0].subject
        assert b_booked.penumpang.email in emails[0].recipient


def test_visitor_access_isolation(client, app):
    """
    US-13 AC-01:
    Pengunjung hanya melihat pemesanan terkait akunnya.
    """
    with client.session_transaction() as sess:
        sess['current_role'] = 'Pengunjung'

    response = client.get('/flight/my-tickets')
    assert response.status_code == 200
    assert b"siti_rahma" in response.data
    assert b"BK-TESTCONF01" in response.data
