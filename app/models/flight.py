from datetime import datetime
from . import db


class Lokasi(db.Model):
    __tablename__ = 'lokasi'

    id = db.Column(db.Integer, primary_key=True)
    kode_kota = db.Column(db.String(10), unique=True, nullable=False)
    nama_kota = db.Column(db.String(100), nullable=False)
    kode_bandara = db.Column(db.String(10), unique=True, nullable=False)
    nama_bandara = db.Column(db.String(150), nullable=False)

    penerbangan_berangkat = db.relationship('Penerbangan', foreign_keys='Penerbangan.asal_id', backref='asal', lazy=True)
    penerbangan_tujuan = db.relationship('Penerbangan', foreign_keys='Penerbangan.tujuan_id', backref='tujuan', lazy=True)


class Maskapai(db.Model):
    __tablename__ = 'maskapai'

    id = db.Column(db.Integer, primary_key=True)
    kode_maskapai = db.Column(db.String(10), unique=True, nullable=False)
    nama = db.Column(db.String(100), nullable=False)
    logo_color = db.Column(db.String(30), default='#1e40af')

    penerbangan = db.relationship('Penerbangan', backref='maskapai', lazy=True)


class Penerbangan(db.Model):
    __tablename__ = 'penerbangan'

    id = db.Column(db.Integer, primary_key=True)
    nomor_penerbangan = db.Column(db.String(20), unique=True, nullable=False)
    asal_id = db.Column(db.Integer, db.ForeignKey('lokasi.id'), nullable=False)
    tujuan_id = db.Column(db.Integer, db.ForeignKey('lokasi.id'), nullable=False)
    maskapai_id = db.Column(db.Integer, db.ForeignKey('maskapai.id'), nullable=False)
    jadwal_keberangkatan = db.Column(db.DateTime, nullable=False)
    jadwal_kedatangan = db.Column(db.DateTime, nullable=False)
    harga_tiket = db.Column(db.Integer, nullable=False)
    kuota_kursi = db.Column(db.Integer, nullable=False, default=50)

    pemesanan = db.relationship('Pemesanan', backref='penerbangan', lazy=True)

    @property
    def durasi_menit(self) -> int:
        delta = self.jadwal_kedatangan - self.jadwal_keberangkatan
        return int(delta.total_seconds() // 60)

    @property
    def durasi_format(self) -> str:
        jam = self.durasi_menit // 60
        menit = self.durasi_menit % 60
        return f"{jam}j {menit}m"


class AkunPengunjung(db.Model):
    __tablename__ = 'akun_pengunjung'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    nama = db.Column(db.String(100), nullable=False)
    email_terdaftar = db.Column(db.String(120), unique=True, nullable=False)
    nomor_telepon = db.Column(db.String(30), nullable=False)

    pemesanan = db.relationship('Pemesanan', backref='akun_pengunjung', lazy=True)


class Pemesanan(db.Model):
    __tablename__ = 'pemesanan'

    id = db.Column(db.Integer, primary_key=True)
    kode_booking_reference = db.Column(db.String(30), unique=True, nullable=False)
    penerbangan_id = db.Column(db.Integer, db.ForeignKey('penerbangan.id'), nullable=False)
    akun_pengunjung_id = db.Column(db.Integer, db.ForeignKey('akun_pengunjung.id'), nullable=True)
    status = db.Column(db.String(40), nullable=False, default='Booked')  # 'Confirmed', 'Booked', 'Waiting for Payment', 'Dibatalkan'
    tanggal_pemesanan = db.Column(db.DateTime, default=datetime.now)
    catatan_akses = db.Column(db.String(100), default='AUTHORIZED_TRAVEL_MANAGER')

    penumpang = db.relationship('Penumpang', backref='pemesanan', uselist=False, lazy=True, cascade='all, delete-orphan')
    e_tiket = db.relationship('ETiket', backref='pemesanan', uselist=False, lazy=True, cascade='all, delete-orphan')


class Penumpang(db.Model):
    __tablename__ = 'penumpang'

    id = db.Column(db.Integer, primary_key=True)
    pemesanan_id = db.Column(db.Integer, db.ForeignKey('pemesanan.id'), nullable=False)
    nama_lengkap = db.Column(db.String(120), nullable=False)
    tipe_identitas = db.Column(db.String(20), default='KTP')
    nomor_identitas = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    nomor_telepon = db.Column(db.String(30), nullable=False)


class ProfilMember(db.Model):
    __tablename__ = 'profil_member'

    id = db.Column(db.Integer, primary_key=True)
    member_code = db.Column(db.String(30), unique=True, nullable=False)
    nama_lengkap = db.Column(db.String(120), nullable=True)
    nomor_identitas = db.Column(db.String(50), nullable=True)
    tanggal_lahir = db.Column(db.Date, nullable=True)
    kewarganegaraan = db.Column(db.String(50), nullable=True)
    nomor_telepon = db.Column(db.String(30), nullable=True)
    alamat = db.Column(db.String(255), nullable=True)
    status_kelengkapan = db.Column(db.Boolean, default=False)

    def check_completeness(self):
        missing = []
        if not self.nama_lengkap or not self.nama_lengkap.strip():
            missing.append("Nama Lengkap")
        if not self.nomor_identitas or not self.nomor_identitas.strip():
            missing.append("Nomor Identitas (NIK/Paspor)")
        if not self.tanggal_lahir:
            missing.append("Tanggal Lahir")
        if not self.kewarganegaraan or not self.kewarganegaraan.strip():
            missing.append("Kewarganegaraan")
        if not self.nomor_telepon or not self.nomor_telepon.strip():
            missing.append("Nomor Telepon")

        is_complete = len(missing) == 0
        self.status_kelengkapan = is_complete
        return is_complete, missing


class ETiket(db.Model):
    __tablename__ = 'e_tiket'

    id = db.Column(db.Integer, primary_key=True)
    pemesanan_id = db.Column(db.Integer, db.ForeignKey('pemesanan.id'), nullable=False)
    nomor_tiket = db.Column(db.String(50), unique=True, nullable=False)
    status_penerbitan = db.Column(db.String(30), default='Belum Diterbitkan')  # 'Diterbitkan', 'Belum Diterbitkan'
    waktu_terbit = db.Column(db.DateTime, nullable=True)


class SimulatedEmail(db.Model):
    __tablename__ = 'simulated_email'

    id = db.Column(db.Integer, primary_key=True)
    recipient = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.now)
    related_booking_code = db.Column(db.String(30), nullable=True)
