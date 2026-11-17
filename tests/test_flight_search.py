import pytest
from datetime import date
from app.models import Lokasi
from app.services.flight_service import (
    search_single_flight,
    search_multi_destination_alternatives,
    compare_flights_by_preference
)
from app.services.itinerary_service import search_multi_leg_itinerary


def test_search_single_flight_success(app):
    """
    US-03 AC-01 & AC-02, US-11 AC-01 & AC-02:
    Pencarian satu tujuan berhasil menampilkan jadwal, maskapai, harga.
    """
    with app.app_context():
        cgk = Lokasi.query.filter_by(kode_bandara="CGK").first()
        dps = Lokasi.query.filter_by(kode_bandara="DPS").first()

        flights = search_single_flight(cgk.id, dps.id, date(2026, 11, 20))
        assert len(flights) >= 2
        assert flights[0].maskapai.nama in ["Garuda Indonesia", "Citilink"]
        assert flights[0].harga_tiket > 0
        assert flights[0].jadwal_keberangkatan is not None


def test_search_single_flight_no_results(app):
    """US-03 AC-03 & US-11 AC-03: Hasil kosong jika tidak ada rute."""
    with app.app_context():
        dps = Lokasi.query.filter_by(kode_bandara="DPS").first()
        kno = Lokasi.query.filter_by(kode_bandara="KNO").first()

        flights = search_single_flight(dps.id, kno.id, date(2026, 11, 20))
        assert len(flights) == 0


def test_search_single_flight_same_origin_dest_raises(app):
    """Penolakan pencarian jika asal dan tujuan sama."""
    with app.app_context():
        cgk = Lokasi.query.filter_by(kode_bandara="CGK").first()
        with pytest.raises(ValueError):
            search_single_flight(cgk.id, cgk.id, date(2026, 11, 20))


def test_search_multi_dest_alternatives(app):
    """
    US-06: Mencari ke beberapa tujuan alternatif.
    AC-01: Memilih minimal dua kota tujuan alternatif.
    AC-02 & AC-03: Menampilkan hasil per kota tujuan.
    AC-04: Menampilkan informasi jika salah satu tujuan tidak ada penerbangan.
    """
    with app.app_context():
        cgk = Lokasi.query.filter_by(kode_bandara="CGK").first()
        dps = Lokasi.query.filter_by(kode_bandara="DPS").first()
        sub = Lokasi.query.filter_by(kode_bandara="SUB").first()
        kno = Lokasi.query.filter_by(kode_bandara="KNO").first()

        results = search_multi_destination_alternatives(cgk.id, [dps.id, sub.id, kno.id], date(2026, 11, 20))

        assert len(results) == 3
        assert results[dps.id]['has_flights'] is True
        assert len(results[dps.id]['flights']) >= 2
        assert results[sub.id]['has_flights'] is True

        # KNO tidak memiliki jadwal di seed -> AC-04
        assert results[kno.id]['has_flights'] is False
        assert len(results[kno.id]['flights']) == 0


def test_search_multi_dest_under_two_destinations_raises(app):
    """US-06 AC-01: Kurang dari dua kota alternatif ditolak."""
    with app.app_context():
        cgk = Lokasi.query.filter_by(kode_bandara="CGK").first()
        dps = Lokasi.query.filter_by(kode_bandara="DPS").first()
        with pytest.raises(ValueError) as exc:
            search_multi_destination_alternatives(cgk.id, [dps.id], date(2026, 11, 20))
        assert "minimal dua" in str(exc.value)


def test_itinerary_multi_leg_valid(app):
    """
    US-07: Itinerary Multi-Destinasi.
    AC-01: Minimal dua segmen.
    AC-02: Validasi keterhubungan rute & kronologis tanggal.
    AC-03: Menampilkan pilihan itinerary & harga total.
    AC-04: Mengetahui jumlah pilihan.
    """
    with app.app_context():
        cgk = Lokasi.query.filter_by(kode_bandara="CGK").first()
        sub = Lokasi.query.filter_by(kode_bandara="SUB").first()
        dps = Lokasi.query.filter_by(kode_bandara="DPS").first()

        segments = [
            {'origin_id': cgk.id, 'dest_id': sub.id, 'date': date(2026, 11, 20)},
            {'origin_id': sub.id, 'dest_id': dps.id, 'date': date(2026, 11, 20)}
        ]

        itineraries = search_multi_leg_itinerary(segments)
        assert len(itineraries) >= 1
        it = itineraries[0]
        assert it['num_legs'] == 2
        assert it['total_price'] == 2000000


def test_itinerary_disconnected_route_raises(app):
    """US-07 AC-02: Rute terputus (Tujuan Segmen 1 != Asal Segmen 2) harus ditolak."""
    with app.app_context():
        cgk = Lokasi.query.filter_by(kode_bandara="CGK").first()
        sub = Lokasi.query.filter_by(kode_bandara="SUB").first()
        dps = Lokasi.query.filter_by(kode_bandara="DPS").first()

        segments = [
            {'origin_id': cgk.id, 'dest_id': sub.id, 'date': date(2026, 11, 20)},
            {'origin_id': dps.id, 'dest_id': sub.id, 'date': date(2026, 11, 20)}
        ]
        with pytest.raises(ValueError) as exc:
            search_multi_leg_itinerary(segments)
        assert "Rute tidak terhubung" in str(exc.value)


def test_itinerary_invalid_date_order_raises(app):
    """US-07 AC-02: Tanggal segmen 2 lebih awal dari segmen 1 harus ditolak."""
    with app.app_context():
        cgk = Lokasi.query.filter_by(kode_bandara="CGK").first()
        sub = Lokasi.query.filter_by(kode_bandara="SUB").first()
        dps = Lokasi.query.filter_by(kode_bandara="DPS").first()

        segments = [
            {'origin_id': cgk.id, 'dest_id': sub.id, 'date': date(2026, 11, 25)},
            {'origin_id': sub.id, 'dest_id': dps.id, 'date': date(2026, 11, 20)}  # Mundur
        ]
        with pytest.raises(ValueError) as exc:
            search_multi_leg_itinerary(segments)
        assert "Urutan tanggal tidak valid" in str(exc.value)


def test_compare_flights_by_preference(app):
    """
    US-09 AC-01 & AC-02:
    Filter jam keberangkatan pagi vs malam.
    """
    with app.app_context():
        cgk = Lokasi.query.filter_by(kode_bandara="CGK").first()
        dps = Lokasi.query.filter_by(kode_bandara="DPS").first()

        morning_flights = compare_flights_by_preference(cgk.id, dps.id, date(2026, 11, 20), time_bucket='pagi')
        assert len(morning_flights) == 1
        assert morning_flights[0].nomor_penerbangan == "GA-101"

        evening_flights = compare_flights_by_preference(cgk.id, dps.id, date(2026, 11, 20), time_bucket='malam')
        assert len(evening_flights) == 1
        assert evening_flights[0].nomor_penerbangan == "QG-102"
