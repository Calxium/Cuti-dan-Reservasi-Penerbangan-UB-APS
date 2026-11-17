import pytest
from datetime import date, datetime
from app import create_app
from app.config import TestConfig
from app.models import (
    db, Pegawai, PengajuanCuti, HakCutiTahunan,
    Lokasi, Maskapai, Penerbangan, Pemesanan, Penumpang,
    ProfilMember, AkunPengunjung, ETiket
)


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        seed_test_data()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def seed_test_data():
    """Seed data yang terkontrol untuk seluruh skenario pengujian."""
    # Pegawai
    p1 = Pegawai(nip="198501152010121001", nama="Budi Santoso", jabatan="Manager IT", email="budi@test.com")
    p2 = Pegawai(nip="199003202015032002", nama="Ani Wijaya", jabatan="HR Specialist", email="ani@test.com")
    p3 = Pegawai(nip="199804122023011005", nama="Eko Prasetyo", jabatan="Junior QA", email="eko@test.com")
    db.session.add_all([p1, p2, p3])
    db.session.flush()

    # Kuota Cuti
    q1 = HakCutiTahunan(pegawai_id=p1.id, tahun=2026, jumlah_hak=12, terpakai=3)
    q2 = HakCutiTahunan(pegawai_id=p2.id, tahun=2026, jumlah_hak=12, terpakai=5)
    q3 = HakCutiTahunan(pegawai_id=p3.id, tahun=2026, jumlah_hak=12, terpakai=0)  # Kosong untuk US-02 AC-04
    db.session.add_all([q1, q2, q3])

    # Pengajuan Cuti (US-01, US-02)
    c1 = PengajuanCuti(
        pegawai_id=p1.id, tanggal_mulai=date(2026, 3, 10), tanggal_selesai=date(2026, 3, 12),
        durasi=3, status="Disetujui", alasan="Cuti tahunan"
    )
    c2 = PengajuanCuti(
        pegawai_id=p2.id, tanggal_mulai=date(2026, 4, 1), tanggal_selesai=date(2026, 4, 5),
        durasi=5, status="Disetujui", alasan="Liburan"
    )
    c3 = PengajuanCuti(
        pegawai_id=p2.id, tanggal_mulai=date(2026, 6, 15), tanggal_selesai=date(2026, 6, 16),
        durasi=2, status="Menunggu", alasan="Keperluan keluarga"
    )
    db.session.add_all([c1, c2, c3])

    # Lokasi
    loc_cgk = Lokasi(kode_kota="JKT", nama_kota="Jakarta", kode_bandara="CGK", nama_bandara="Soekarno-Hatta")
    loc_sub = Lokasi(kode_kota="SUB", nama_kota="Surabaya", kode_bandara="SUB", nama_bandara="Juanda")
    loc_dps = Lokasi(kode_kota="DPS", nama_kota="Denpasar / Bali", kode_bandara="DPS", nama_bandara="Ngurah Rai")
    loc_kno = Lokasi(kode_kota="KNO", nama_kota="Medan", kode_bandara="KNO", nama_bandara="Kualanamu")
    db.session.add_all([loc_cgk, loc_sub, loc_dps, loc_kno])
    db.session.flush()

    # Maskapai
    air_ga = Maskapai(kode_maskapai="GA", nama="Garuda Indonesia", logo_color="#002b49")
    air_qg = Maskapai(kode_maskapai="QG", nama="Citilink", logo_color="#00a651")
    air_jt = Maskapai(kode_maskapai="JT", nama="Lion Air", logo_color="#ed1b24")
    db.session.add_all([air_ga, air_qg, air_jt])
    db.session.flush()

    # Penerbangan pada 2026-11-20
    test_date = date(2026, 11, 20)
    f1 = Penerbangan(
        nomor_penerbangan="GA-101",
        asal_id=loc_cgk.id, tujuan_id=loc_dps.id, maskapai_id=air_ga.id,
        jadwal_keberangkatan=datetime.combine(test_date, datetime.strptime("07:30", "%H:%M").time()),
        jadwal_kedatangan=datetime.combine(test_date, datetime.strptime("10:20", "%H:%M").time()),
        harga_tiket=1800000
    )
    f2 = Penerbangan(
        nomor_penerbangan="QG-102",
        asal_id=loc_cgk.id, tujuan_id=loc_dps.id, maskapai_id=air_qg.id,
        jadwal_keberangkatan=datetime.combine(test_date, datetime.strptime("19:30", "%H:%M").time()),
        jadwal_kedatangan=datetime.combine(test_date, datetime.strptime("22:20", "%H:%M").time()),
        harga_tiket=1200000
    )
    f3 = Penerbangan(
        nomor_penerbangan="GA-201",
        asal_id=loc_cgk.id, tujuan_id=loc_sub.id, maskapai_id=air_ga.id,
        jadwal_keberangkatan=datetime.combine(test_date, datetime.strptime("08:00", "%H:%M").time()),
        jadwal_kedatangan=datetime.combine(test_date, datetime.strptime("09:30", "%H:%M").time()),
        harga_tiket=1300000
    )
    f4 = Penerbangan(
        nomor_penerbangan="JT-301",
        asal_id=loc_sub.id, tujuan_id=loc_dps.id, maskapai_id=air_jt.id,
        jadwal_keberangkatan=datetime.combine(test_date, datetime.strptime("11:30", "%H:%M").time()),
        jadwal_kedatangan=datetime.combine(test_date, datetime.strptime("13:20", "%H:%M").time()),
        harga_tiket=700000
    )
    db.session.add_all([f1, f2, f3, f4])
    db.session.flush()

    # Member Profil & Akun Pengunjung
    m1 = ProfilMember(
        member_code="MB-7788",
        nama_lengkap="Budi Santoso",
        nomor_identitas="3171011501850002",
        tanggal_lahir=date(1985, 1, 15),
        kewarganegaraan="Indonesia",
        nomor_telepon="081288990011",
        alamat="Jakarta",
        status_kelengkapan=True
    )
    db.session.add(m1)

    v1 = AkunPengunjung(
        username="siti_rahma",
        nama="Siti Rahma",
        email_terdaftar="siti.rahma@example.com",
        nomor_telepon="081298765432"
    )
    db.session.add(v1)
    db.session.flush()

    # Pemesanan
    b1 = Pemesanan(
        kode_booking_reference="BK-TESTCONF01",
        penerbangan_id=f1.id,
        akun_pengunjung_id=v1.id,
        status="Confirmed",
        catatan_akses="AUTHORIZED_TRAVEL_MANAGER"
    )
    db.session.add(b1)
    db.session.flush()

    pax1 = Penumpang(
        pemesanan_id=b1.id,
        nama_lengkap="Siti Rahma",
        tipe_identitas="KTP",
        nomor_identitas="3201015509930005",
        email="siti.rahma@example.com",
        nomor_telepon="081298765432"
    )
    db.session.add(pax1)

    tkt1 = ETiket(
        pemesanan_id=b1.id,
        nomor_tiket="TKT-TEST-001",
        status_penerbitan="Diterbitkan",
        waktu_terbit=datetime.now()
    )
    db.session.add(tkt1)

    # Booking Booked
    b2 = Pemesanan(
        kode_booking_reference="BK-TESTBOOK02",
        penerbangan_id=f2.id,
        akun_pengunjung_id=v1.id,
        status="Booked",
        catatan_akses="AUTHORIZED_TRAVEL_MANAGER"
    )
    db.session.add(b2)
    db.session.flush()

    pax2 = Penumpang(
        pemesanan_id=b2.id,
        nama_lengkap="Siti Rahma",
        tipe_identitas="KTP",
        nomor_identitas="3201015509930005",
        email="siti.rahma@example.com",
        nomor_telepon="081298765432"
    )
    db.session.add(pax2)

    # Booking Restricted Agency (US-14 AC-05)
    b_restricted = Pemesanan(
        kode_booking_reference="BK-RESTRICTED99",
        penerbangan_id=f1.id,
        status="Confirmed",
        catatan_akses="OTHER_RESTRICTED_AGENCY"
    )
    db.session.add(b_restricted)
    db.session.flush()

    db.session.commit()
