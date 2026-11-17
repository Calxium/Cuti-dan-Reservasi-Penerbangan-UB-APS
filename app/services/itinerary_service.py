import itertools
from typing import List, Dict, Any
from .flight_service import search_single_flight


def search_multi_leg_itinerary(segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    US-07: Mencari Itinerary Penerbangan Multi-Destinasi (Member Frequent Traveller).
    AC-01: Memasukkan minimal 2 segmen perjalanan.
    AC-02: Memvalidasi urutan tanggal dan keterhubungan rute antarsegmen.
    AC-03: Menampilkan pilihan itinerary beserta rute segmen dan harga total.
    AC-04: Mengetahui jumlah pilihan itinerary yang ditemukan.
    AC-05: Menampilkan pesan jika tidak ada itinerary yang sesuai.
    """
    if not segments or len(segments) < 2:
        raise ValueError("Itinerary multi-destinasi membutuhkan minimal 2 segmen perjalanan.")

    # Validasi keterhubungan rute dan urutan tanggal (AC-02)
    for i in range(len(segments) - 1):
        curr_seg = segments[i]
        next_seg = segments[i + 1]

        if curr_seg['dest_id'] != next_seg['origin_id']:
            raise ValueError(
                f"Rute tidak terhubung: Kota tujuan segmen {i+1} harus sama dengan kota asal segmen {i+2}."
            )

        if next_seg['date'] < curr_seg['date']:
            raise ValueError(
                f"Urutan tanggal tidak valid: Tanggal keberangkatan segmen {i+2} tidak boleh sebelum segmen {i+1}."
            )

    # Cari daftar penerbangan untuk setiap segmen
    legs_flights = []
    for seg in segments:
        flights = search_single_flight(seg['origin_id'], seg['dest_id'], seg['date'])
        if not flights:
            # Jika ada salah satu segmen yang kosong, tidak mungkin terbentuk itinerary lengkap
            return []
        legs_flights.append(flights)

    # Buat kombinasi produk Kartesian antarsegmen
    valid_itineraries = []
    for combination in itertools.product(*legs_flights):
        # Validasi waktu jika pada hari yang sama
        is_temporally_valid = True
        for i in range(len(combination) - 1):
            f_curr = combination[i]
            f_next = combination[i + 1]
            if f_curr.jadwal_keberangkatan.date() == f_next.jadwal_keberangkatan.date():
                if f_next.jadwal_keberangkatan <= f_curr.jadwal_kedatangan:
                    is_temporally_valid = False
                    break

        if is_temporally_valid:
            total_price = sum(f.harga_tiket for f in combination)
            total_duration = sum(f.durasi_menit for f in combination)
            valid_itineraries.append({
                'legs': list(combination),
                'total_price': total_price,
                'total_duration_minutes': total_duration,
                'num_legs': len(combination)
            })

    # Urutkan berdasarkan harga total termurah
    valid_itineraries.sort(key=lambda x: x['total_price'])
    return valid_itineraries
