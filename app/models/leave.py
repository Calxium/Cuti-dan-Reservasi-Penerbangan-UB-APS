from datetime import datetime
from . import db


class Pegawai(db.Model):
    __tablename__ = 'pegawai'

    id = db.Column(db.Integer, primary_key=True)
    nip = db.Column(db.String(30), unique=True, nullable=False)
    nama = db.Column(db.String(100), nullable=False)
    jabatan = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    pengajuan_cuti = db.relationship('PengajuanCuti', backref='pegawai', lazy=True, cascade='all, delete-orphan')
    hak_cuti_tahunan = db.relationship('HakCutiTahunan', backref='pegawai', lazy=True, cascade='all, delete-orphan')

    def get_quota_for_year(self, year: int):
        quota = HakCutiTahunan.query.filter_by(pegawai_id=self.id, tahun=year).first()
        if not quota:
            quota = HakCutiTahunan(pegawai_id=self.id, tahun=year, jumlah_hak=12, terpakai=0)
            db.session.add(quota)
            db.session.commit()
        return quota


class PengajuanCuti(db.Model):
    __tablename__ = 'pengajuan_cuti'

    id = db.Column(db.Integer, primary_key=True)
    pegawai_id = db.Column(db.Integer, db.ForeignKey('pegawai.id'), nullable=False)
    tanggal_mulai = db.Column(db.Date, nullable=False)
    tanggal_selesai = db.Column(db.Date, nullable=False)
    durasi = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(30), nullable=False, default='Menunggu')  # 'Disetujui', 'Menunggu', 'Ditolak', 'Dibatalkan'
    alasan = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)


class HakCutiTahunan(db.Model):
    __tablename__ = 'hak_cuti_tahunan'

    id = db.Column(db.Integer, primary_key=True)
    pegawai_id = db.Column(db.Integer, db.ForeignKey('pegawai.id'), nullable=False)
    tahun = db.Column(db.Integer, nullable=False)
    jumlah_hak = db.Column(db.Integer, nullable=False, default=12)
    terpakai = db.Column(db.Integer, nullable=False, default=0)

    @property
    def sisa(self) -> int:
        return max(0, self.jumlah_hak - self.terpakai)
