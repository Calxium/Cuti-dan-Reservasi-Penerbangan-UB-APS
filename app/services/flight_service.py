from datetime import date, datetime, time
from typing import List, Dict, Any, Optional
from ..models import db, Penerbangan, Lokasi


def search_single_flight(origin_id: int, dest_id: int, travel_date: date) -> List[Penerbangan]:
    """
    US-03: Mencari penerbangan satu tujuan (Calon Penumpang).
    US-11: Mencari penerbangan untuk pengunjung (Manajer Travel).
    AC-01: Memasukkan lokasi keberangkatan, tujuan, tanggal penerbangan.
    AC-02: Menampilkan daftar jadwal, maskapai, harga tiket.
    AC-03: Menampilkan hasil kosong jika tidak ada yang cocok.
    """
    if origin_id == dest_id:
        raise ValueError("Lokasi keberangkatan dan tujuan tidak boleh sama.")

    start_datetime = datetime.combine(travel_date, time.min)
    end_datetime = datetime.combine(travel_date, time.max)

    return Penerbangan.query.filter(
        Penerbangan.asal_id == origin_id,
        Penerbangan.tujuan_id == dest_id,
        Penerbangan.jadwal_keberangkatan >= start_datetime,
        Penerbangan.jadwal_keberangkatan <= end_datetime
    ).order_by(Penerbangan.jadwal_keberangkatan.asc()).all()


def search_multi_destination_alternatives(origin_id: int, dest_ids: List[int], travel_date: date) -> Dict[int, Dict[str, Any]]:
    """
    US-06: Mencari penerbangan ke beberapa tujuan alternatif dari satu asal.
    AC-01: Pengguna memilih minimal dua kota tujuan alternatif.
    AC-02 & AC-03: Menampilkan hasil per kota tujuan (jadwal, maskapai, harga).
    AC-04: Menampilkan informasi jika tidak ada penerbangan ke salah satu tujuan.
    """
    if not dest_ids or len(dest_ids) < 2:
        raise ValueError("Pencarian alternatif membutuhkan minimal dua kota tujuan berbeda.")

    results = {}
    for dest_id in dest_ids:
        destination = db.session.get(Lokasi, dest_id)
        if not destination:
            continue

        flights = search_single_flight(origin_id, dest_id, travel_date)
        results[dest_id] = {
            'destination': destination,
            'flights': flights,
            'has_flights': len(flights) > 0
        }

    return results


def compare_flights_by_preference(
    origin_id: int,
    dest_id: int,
    travel_date: date,
    time_bucket: Optional[str] = None
) -> List[Penerbangan]:
    """
    US-09: Membandingkan penerbangan berdasarkan preferensi jam keberangkatan.
    AC-01: Memfilter berdasarkan tujuan, tanggal, dan rentang jam keberangkatan.
    AC-02: Menampilkan opsi beserta maskapai, jadwal, dan harga tiket.
    """
    flights = search_single_flight(origin_id, dest_id, travel_date)

    if not time_bucket or time_bucket == 'all':
        return flights

    filtered = []
    for f in flights:
        hour = f.jadwal_keberangkatan.hour
        if time_bucket == 'pagi' and 0 <= hour < 12:
            filtered.append(f)
        elif time_bucket == 'siang' and 12 <= hour < 18:
            filtered.append(f)
        elif time_bucket == 'malam' and 18 <= hour <= 23:
            filtered.append(f)

    return filtered
