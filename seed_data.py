from datetime import date, datetime, timedelta
from app import create_app
from app.models import (
    db, Pegawai, PengajuanCuti, HakCutiTahunan,
    Lokasi, Maskapai, Penerbangan, Pemesanan, Penumpang,
    ProfilMember, AkunPengunjung, ETiket, SimulatedEmail
)

def seed_database():
    app = create_app()
    with app.app_context():
        # Buat seluruh tabel
        db.create_all()

        # Bersihkan data lama jika ada
        SimulatedEmail.query.delete()
        ETiket.query.delete()
        Penumpang.query.delete()
        Pemesanan.query.delete()
        Penerbangan.query.delete()
        Maskapai.query.delete()
        Lokasi.query.delete()
        ProfilMember.query.delete()
        AkunPengunjung.query.delete()
        HakCutiTahunan.query.delete()
        PengajuanCuti.query.delete()
        Pegawai.query.delete()
        db.session.commit()

        print("[1/5] Mengisi data Pegawai dan Kuota Hak Cuti...")
        # 1. Pegawai & Hak Cuti
        p1 = Pegawai(nip="198501152010121001", nama="Budi Santoso", jabatan="Manager IT", email="budi.santoso@perusahaan.co.id")
        p2 = Pegawai(nip="199003202015032002", nama="Ani Wijaya", jabatan="Senior HR Specialist", email="ani.wijaya@perusahaan.co.id")
        p3 = Pegawai(nip="199207142018012003", nama="Citra Lestari", jabatan="UX Designer", email="citra.lestari@perusahaan.co.id")
        p4 = Pegawai(nip="199511052021021004", nama="Denny Pratama", jabatan="Backend Engineer", email="denny.pratama@perusahaan.co.id")
        p5 = Pegawai(nip="199804122023011005", nama="Eko Prasetyo", jabatan="Junior QA Engineer", email="eko.prasetyo@perusahaan.co.id")

        db.session.add_all([p1, p2, p3, p4, p5])
        db.session.flush()

        # Kuota Hak Cuti 2026 (standar 12 hari)
        q1 = HakCutiTahunan(pegawai_id=p1.id, tahun=2026, jumlah_hak=12, terpakai=3)
        q2 = HakCutiTahunan(pegawai_id=p2.id, tahun=2026, jumlah_hak=12, terpakai=5)
        q3 = HakCutiTahunan(pegawai_id=p3.id, tahun=2026, jumlah_hak=12, terpakai=0)
        q4 = HakCutiTahunan(pegawai_id=p4.id, tahun=2026, jumlah_hak=12, terpakai=0)
        q5 = HakCutiTahunan(pegawai_id=p5.id, tahun=2026, jumlah_hak=12, terpakai=0) # Untuk US-02 AC-04 (Belum ada cuti)

        db.session.add_all([q1, q2, q3, q4, q5])

        # Pengajuan Cuti (US-01, US-02)
        c1 = PengajuanCuti(pegawai_id=p1.id, tanggal_mulai=date(2026, 3, 10), tanggal_selesai=date(2026, 3, 12), durasi=3, status="Disetujui", alasan="Acara keluarga tahunan")
        c2 = PengajuanCuti(pegawai_id=p2.id, tanggal_mulai=date(2026, 4, 1), tanggal_selesai=date(2026, 4, 5), durasi=5, status="Disetujui", alasan="Liburan hari raya")
        c3 = PengajuanCuti(pegawai_id=p2.id, tanggal_mulai=date(2026, 6, 15), tanggal_selesai=date(2026, 6, 16), durasi=2, status="Menunggu", alasan="Keperluan pribadi mendesak")
        c4 = PengajuanCuti(pegawai_id=p3.id, tanggal_mulai=date(2026, 5, 18), tanggal_selesai=date(2026, 5, 20), durasi=3, status="Ditolak", alasan="Puncak rilis produk")
        c5 = PengajuanCuti(pegawai_id=p4.id, tanggal_mulai=date(2026, 2, 1), tanggal_selesai=date(2026, 2, 2), durasi=2, status="Dibatalkan", alasan="Dibatalkan sendiri oleh pegawai")

        db.session.add_all([c1, c2, c3, c4, c5])

        print("[2/5] Mengisi data Lokasi Bandara dan Maskapai...")
        # 2. Lokasi Bandara
        loc_cgk = Lokasi(kode_kota="JKT", nama_kota="Jakarta", kode_bandara="CGK", nama_bandara="Bandara Internasional Soekarno-Hatta")
        loc_sub = Lokasi(kode_kota="SUB", nama_kota="Surabaya", kode_bandara="SUB", nama_bandara="Bandara Internasional Juanda")
        loc_dps = Lokasi(kode_kota="DPS", nama_kota="Denpasar / Bali", kode_bandara="DPS", nama_bandara="Bandara Internasional I Gusti Ngurah Rai")
        loc_kno = Lokasi(kode_kota="KNO", nama_kota="Medan", kode_bandara="KNO", nama_bandara="Bandara Internasional Kualanamu")
        loc_yia = Lokasi(kode_kota="JOG", nama_kota="Yogyakarta", kode_bandara="YIA", nama_bandara="Bandara Internasional Yogyakarta")

        db.session.add_all([loc_cgk, loc_sub, loc_dps, loc_kno, loc_yia])
        db.session.flush()

        # Maskapai
        air_ga = Maskapai(kode_maskapai="GA", nama="Garuda Indonesia", logo_color="#002b49")
        air_qg = Maskapai(kode_maskapai="QG", nama="Citilink", logo_color="#00a651")
        air_jt = Maskapai(kode_maskapai="JT", nama="Lion Air", logo_color="#ed1b24")
        air_id = Maskapai(kode_maskapai="ID", nama="Batik Air", logo_color="#7b1113")
        air_iu = Maskapai(kode_maskapai="IU", nama="Super Air Jet", logo_color="#b8860b")

        db.session.add_all([air_ga, air_qg, air_jt, air_id, air_iu])
        db.session.flush()

        print("[3/5] Mengisi data Jadwal Penerbangan Sintetis...")
        # 3. Jadwal Penerbangan
        # Menggunakan tanggal dinamis (hari ini s.d. beberapa hari ke depan)
        today = date.today()
        # Tambah jadwal untuk hari ini, besok, lusa, dan tanggal statis 2026-11-20
        target_dates = [today, today + timedelta(days=1), today + timedelta(days=2), date(2026, 11, 20)]

        flight_list = []
        fn_counter = 100

        for d in target_dates:
            # CGK -> DPS (Pagi, Siang, Malam)
            fn_counter += 1
            f1 = Penerbangan(
                nomor_penerbangan=f"GA-{fn_counter}",
                asal_id=loc_cgk.id, tujuan_id=loc_dps.id, maskapai_id=air_ga.id,
                jadwal_keberangkatan=datetime.combine(d, datetime.strptime("07:30", "%H:%M").time()),
                jadwal_kedatangan=datetime.combine(d, datetime.strptime("10:20", "%H:%M").time()),
                harga_tiket=1850000
            )
            fn_counter += 1
            f2 = Penerbangan(
                nomor_penerbangan=f"QG-{fn_counter}",
                asal_id=loc_cgk.id, tujuan_id=loc_dps.id, maskapai_id=air_qg.id,
                jadwal_keberangkatan=datetime.combine(d, datetime.strptime("13:15", "%H:%M").time()),
                jadwal_kedatangan=datetime.combine(d, datetime.strptime("16:05", "%H:%M").time()),
                harga_tiket=1250000
            )
            fn_counter += 1
            f3 = Penerbangan(
                nomor_penerbangan=f"ID-{fn_counter}",
                asal_id=loc_cgk.id, tujuan_id=loc_dps.id, maskapai_id=air_id.id,
                jadwal_keberangkatan=datetime.combine(d, datetime.strptime("19:45", "%H:%M").time()),
                jadwal_kedatangan=datetime.combine(d, datetime.strptime("22:35", "%H:%M").time()),
                harga_tiket=1450000
            )

            # CGK -> SUB (Jakarta ke Surabaya)
            fn_counter += 1
            f4 = Penerbangan(
                nomor_penerbangan=f"GA-{fn_counter}",
                asal_id=loc_cgk.id, tujuan_id=loc_sub.id, maskapai_id=air_ga.id,
                jadwal_keberangkatan=datetime.combine(d, datetime.strptime("08:00", "%H:%M").time()),
                jadwal_kedatangan=datetime.combine(d, datetime.strptime("09:30", "%H:%M").time()),
                harga_tiket=1350000
            )
            fn_counter += 1
            f5 = Penerbangan(
                nomor_penerbangan=f"IU-{fn_counter}",
                asal_id=loc_cgk.id, tujuan_id=loc_sub.id, maskapai_id=air_iu.id,
                jadwal_keberangkatan=datetime.combine(d, datetime.strptime("14:30", "%H:%M").time()),
                jadwal_kedatangan=datetime.combine(d, datetime.strptime("16:00", "%H:%M").time()),
                harga_tiket=850000
            )

            # SUB -> DPS (Surabaya ke Bali - segmen kedua multi-leg itinerary)
            fn_counter += 1
            f6 = Penerbangan(
                nomor_penerbangan=f"ID-{fn_counter}",
                asal_id=loc_sub.id, tujuan_id=loc_dps.id, maskapai_id=air_id.id,
                jadwal_keberangkatan=datetime.combine(d, datetime.strptime("11:30", "%H:%M").time()),
                jadwal_kedatangan=datetime.combine(d, datetime.strptime("13:20", "%H:%M").time()),
                harga_tiket=750000
            )
            fn_counter += 1
            f7 = Penerbangan(
                nomor_penerbangan=f"JT-{fn_counter}",
                asal_id=loc_sub.id, tujuan_id=loc_dps.id, maskapai_id=air_jt.id,
                jadwal_keberangkatan=datetime.combine(d, datetime.strptime("17:45", "%H:%M").time()),
                jadwal_kedatangan=datetime.combine(d, datetime.strptime("19:35", "%H:%M").time()),
                harga_tiket=650000
            )

            # CGK -> KNO (Jakarta ke Medan)
            fn_counter += 1
            f8 = Penerbangan(
                nomor_penerbangan=f"GA-{fn_counter}",
                asal_id=loc_cgk.id, tujuan_id=loc_kno.id, maskapai_id=air_ga.id,
                jadwal_keberangkatan=datetime.combine(d, datetime.strptime("09:00", "%H:%M").time()),
                jadwal_kedatangan=datetime.combine(d, datetime.strptime("11:20", "%H:%M").time()),
                harga_tiket=1950000
            )

            # CGK -> YIA (Jakarta ke Jogja)
            fn_counter += 1
            f9 = Penerbangan(
                nomor_penerbangan=f"QG-{fn_counter}",
                asal_id=loc_cgk.id, tujuan_id=loc_yia.id, maskapai_id=air_qg.id,
                jadwal_keberangkatan=datetime.combine(d, datetime.strptime("10:15", "%H:%M").time()),
                jadwal_kedatangan=datetime.combine(d, datetime.strptime("11:30", "%H:%M").time()),
                harga_tiket=920000
            )

            flight_list.extend([f1, f2, f3, f4, f5, f6, f7, f8, f9])

        db.session.add_all(flight_list)
        db.session.flush()

        print("[4/5] Mengisi data Member Frequent Traveller & Akun Pengunjung...")
        # 4. Member Profil & Akun Pengunjung
        m1 = ProfilMember(
            member_code="MB-7788",
            nama_lengkap="Budi Santoso",
            nomor_identitas="3171011501850002",
            tanggal_lahir=date(1985, 1, 15),
            kewarganegaraan="Indonesia",
            nomor_telepon="081288990011",
            alamat="Jl. Sudirman Kav 21, Jakarta Selatan",
            status_kelengkapan=True
        )
        db.session.add(m1)

        v1 = AkunPengunjung(
            username="siti_rahma",
            nama="Siti Rahma",
            email_terdaftar="siti.rahma@example.com",
            nomor_telepon="081298765432"
        )
        v2 = AkunPengunjung(
            username="joko_susilo",
            nama="Joko Susilo",
            email_terdaftar="joko.susilo@example.com",
            nomor_telepon="081377889900"
        )
        db.session.add_all([v1, v2])
        db.session.flush()

        print("[5/5] Mengisi data Riwayat Pemesanan dan E-Tiket...")
        # 5. Pemesanan Demo (Confirmed, Booked, Waiting for Payment, Dibatalkan)
        ref_flight = flight_list[0]
        # Pemesanan 1: Confirmed milik Siti Rahma (US-13 ada e-tiket)
        b1 = Pemesanan(
            kode_booking_reference="BK-CONFIRMED01",
            penerbangan_id=ref_flight.id,
            akun_pengunjung_id=v1.id,
            status="Confirmed",
            tanggal_pemesanan=datetime.now() - timedelta(days=2),
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
            nomor_tiket="TKT-2026-SR001",
            status_penerbitan="Diterbitkan",
            waktu_terbit=datetime.now() - timedelta(days=2)
        )
        db.session.add(tkt1)

        email1 = SimulatedEmail(
            recipient="siti.rahma@example.com",
            subject=f"[E-Tiket] Konfirmasi Pemesanan {b1.kode_booking_reference} - {ref_flight.nomor_penerbangan}",
            body=f"Halo Siti Rahma,\n\nE-Tiket Anda telah diterbitkan dengan nomor {tkt1.nomor_tiket}.",
            related_booking_code=b1.kode_booking_reference
        )
        db.session.add(email1)

        # Pemesanan 2: Booked
        b2 = Pemesanan(
            kode_booking_reference="BK-BOOKED02",
            penerbangan_id=flight_list[1].id,
            akun_pengunjung_id=v2.id,
            status="Booked",
            tanggal_pemesanan=datetime.now() - timedelta(days=1),
            catatan_akses="AUTHORIZED_TRAVEL_MANAGER"
        )
        db.session.add(b2)
        db.session.flush()

        pax2 = Penumpang(
            pemesanan_id=b2.id,
            nama_lengkap="Joko Susilo",
            tipe_identitas="KTP",
            nomor_identitas="3374011204890001",
            email="joko.susilo@example.com",
            nomor_telepon="081377889900"
        )
        db.session.add(pax2)
        tkt2 = ETiket(
            pemesanan_id=b2.id,
            nomor_tiket="TKT-2026-JS002",
            status_penerbitan="Belum Diterbitkan",
            waktu_terbit=None
        )
        db.session.add(tkt2)

        # Pemesanan 3: Waiting for Payment
        b3 = Pemesanan(
            kode_booking_reference="BK-WAITPAY03",
            penerbangan_id=flight_list[3].id,
            akun_pengunjung_id=v1.id,
            status="Waiting for Payment",
            tanggal_pemesanan=datetime.now() - timedelta(hours=5),
            catatan_akses="AUTHORIZED_TRAVEL_MANAGER"
        )
        db.session.add(b3)
        db.session.flush()

        pax3 = Penumpang(
            pemesanan_id=b3.id,
            nama_lengkap="Siti Rahma",
            tipe_identitas="KTP",
            nomor_identitas="3201015509930005",
            email="siti.rahma@example.com",
            nomor_telepon="081298765432"
        )
        db.session.add(pax3)

        # Pemesanan 4: Dibatalkan
        b4 = Pemesanan(
            kode_booking_reference="BK-CANCELLED04",
            penerbangan_id=flight_list[4].id,
            akun_pengunjung_id=None,
            status="Dibatalkan",
            tanggal_pemesanan=datetime.now() - timedelta(days=3),
            catatan_akses="AUTHORIZED_TRAVEL_MANAGER"
        )
        db.session.add(b4)
        db.session.flush()

        pax4 = Penumpang(
            pemesanan_id=b4.id,
            nama_lengkap="Rian Ardiansyah",
            tipe_identitas="KTP",
            nomor_identitas="3172021008950003",
            email="rian.ardiansyah@example.com",
            nomor_telepon="08151234567"
        )
        db.session.add(pax4)

        # Pemesanan 5: Restricted Agency (untuk US-14 AC-05: Penolakan akses bila beda wewenang)
        b5 = Pemesanan(
            kode_booking_reference="BK-RESTRICTED99",
            penerbangan_id=flight_list[0].id,
            akun_pengunjung_id=None,
            status="Confirmed",
            tanggal_pemesanan=datetime.now() - timedelta(days=1),
            catatan_akses="OTHER_RESTRICTED_AGENCY"
        )
        db.session.add(b5)
        db.session.flush()

        pax5 = Penumpang(
            pemesanan_id=b5.id,
            nama_lengkap="Rahasia Negara",
            tipe_identitas="Paspor",
            nomor_identitas="A12345678",
            email="rahasia@example.com",
            nomor_telepon="0800000000"
        )
        db.session.add(pax5)

        db.session.commit()
        print("Pengisian database berhasil diselesaikan tanpa kendala!")

if __name__ == '__main__':
    seed_database()
