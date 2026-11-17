from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .leave import Pegawai, PengajuanCuti, HakCutiTahunan  # noqa: E402
from .flight import (  # noqa: E402
    Lokasi,
    Maskapai,
    Penerbangan,
    Pemesanan,
    Penumpang,
    ProfilMember,
    AkunPengunjung,
    ETiket,
    SimulatedEmail
)

__all__ = [
    'db',
    'Pegawai',
    'PengajuanCuti',
    'HakCutiTahunan',
    'Lokasi',
    'Maskapai',
    'Penerbangan',
    'Pemesanan',
    'Penumpang',
    'ProfilMember',
    'AkunPengunjung',
    'ETiket',
    'SimulatedEmail'
]
