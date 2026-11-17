from datetime import datetime
from typing import List
from ..models import db, SimulatedEmail


def send_simulated_email(recipient: str, subject: str, body: str, related_booking_code: str = None) -> SimulatedEmail:
    """
    US-13 AC-03: Simulasi pengiriman email lokal ketika e-tiket berhasil diterbitkan.
    Menyimpan pesan ke database agar dapat diperiksa langsung di antarmuka web dan log pengujian.
    """
    email_record = SimulatedEmail(
        recipient=recipient,
        subject=subject,
        body=body,
        sent_at=datetime.now(),
        related_booking_code=related_booking_code
    )
    db.session.add(email_record)
    db.session.commit()
    return email_record


def get_simulated_emails(recipient: str = None) -> List[SimulatedEmail]:
    """Mengambil daftar email terkirim untuk pengecekan pengujian atau tampilan UI Mailbox."""
    query = SimulatedEmail.query
    if recipient:
        query = query.filter_by(recipient=recipient)
    return query.order_by(SimulatedEmail.sent_at.desc()).all()
