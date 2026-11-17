from app.models import Penerbangan, Lokasi, Pemesanan, AkunPengunjung


def test_main_routes(client):
    """Test dashboard index and switch-role endpoints."""
    # Index
    res = client.get('/')
    assert res.status_code == 200
    assert b"QUIZ 2 APS" in res.data

    # Switch roles
    res_hr = client.get('/switch-role/Manajer%20HRD', follow_redirects=True)
    assert res_hr.status_code == 200

    res_mem = client.get('/switch-role/Member%20Frequent%20Traveller', follow_redirects=True)
    assert res_mem.status_code == 200

    res_mgr = client.get('/switch-role/Manajer%20Travel', follow_redirects=True)
    assert res_mgr.status_code == 200

    res_vis = client.get('/switch-role/Pengunjung', follow_redirects=True)
    assert res_vis.status_code == 200

    res_pax = client.get('/switch-role/Calon%20Penumpang', follow_redirects=True)
    assert res_pax.status_code == 200

    # Mailbox
    res_mb = client.get('/mailbox')
    assert res_mb.status_code == 200


def test_leave_routes_full(client, app):
    """Test all leave routes and employee listing."""
    res_list = client.get('/leave/employees')
    assert res_list.status_code == 200
    assert b"Budi Santoso" in res_list.data

    # Filter with invalid dates
    res_err = client.get('/leave/filter?start_date=2026-05-10&end_date=2026-05-01')
    assert res_err.status_code == 200
    assert b"tidak boleh melebihi" in res_err.data

    # Filter with only start_date
    res_start = client.get('/leave/filter?start_date=2026-03-01')
    assert res_start.status_code == 200

    # Filter with only end_date
    res_end = client.get('/leave/filter?end_date=2026-04-30')
    assert res_end.status_code == 200

    # Employee detail not found
    res_notfound = client.get('/leave/employee/99999', follow_redirects=True)
    assert res_notfound.status_code == 200


def test_flight_search_routes(client, app):
    """Test single and multi search routes."""
    with app.app_context():
        cgk = Lokasi.query.filter_by(kode_bandara="CGK").first()
        dps = Lokasi.query.filter_by(kode_bandara="DPS").first()
        sub = Lokasi.query.filter_by(kode_bandara="SUB").first()
        cgk_id, dps_id, sub_id = cgk.id, dps.id, sub.id

    # Single search GET with query
    res = client.get(f'/flight/search?origin_id={cgk_id}&dest_id={dps_id}&travel_date=2026-11-20')
    assert res.status_code == 200
    assert b"GA-101" in res.data or b"Pilihan Penerbangan" in res.data

    # Single search with same origin & dest error
    res_err = client.get(f'/flight/search?origin_id={cgk_id}&dest_id={cgk_id}&travel_date=2026-11-20')
    assert res_err.status_code == 200
    assert b"tidak boleh sama" in res_err.data

    # Multi-dest search GET
    res_multi = client.get(
        f'/flight/search-multi-dest?origin_id={cgk_id}&dest_ids={dps_id}&dest_ids={sub_id}&travel_date=2026-11-20'
    )
    assert res_multi.status_code == 200
    assert b"Tujuan: Denpasar" in res_multi.data

    # Multi-dest error under 2
    res_multi_err = client.get(f'/flight/search-multi-dest?origin_id={cgk_id}&dest_ids={dps_id}&travel_date=2026-11-20')
    assert res_multi_err.status_code == 200
    assert b"minimal dua" in res_multi_err.data


def test_booking_routes_flow(client, app):
    """Test booking creation, detail view, and cancellation."""
    with app.app_context():
        flight = Penerbangan.query.first()
        f_id = flight.id

    # Book GET form
    res_form = client.get(f'/flight/book/{f_id}')
    assert res_form.status_code == 200

    # Book POST valid
    post_data = {
        'nama_lengkap': 'Dewi Lestari',
        'tipe_identitas': 'KTP',
        'nomor_identitas': '3171019908870001',
        'email': 'dewi.lestari@example.com',
        'nomor_telepon': '081299998888'
    }
    res_post = client.post(f'/flight/book/{f_id}', data=post_data, follow_redirects=True)
    assert res_post.status_code == 200
    assert b"Pemesanan berhasil dibuat" in res_post.data

    # Find created booking id
    with app.app_context():
        new_booking = Pemesanan.query.filter_by(status="Confirmed").order_by(Pemesanan.id.desc()).first()
        b_id = new_booking.id

    # View booking detail
    res_detail = client.get(f'/flight/booking/{b_id}')
    assert res_detail.status_code == 200
    assert b"Dewi Lestari" in res_detail.data

    # Cancel booking
    res_cancel = client.post(f'/flight/cancel/{b_id}', follow_redirects=True)
    assert res_cancel.status_code == 200
    assert b"berhasil dibatalkan" in res_cancel.data


def test_itinerary_routes(client, app):
    """Test multi-leg itinerary search routes."""
    with app.app_context():
        cgk = Lokasi.query.filter_by(kode_bandara="CGK").first()
        sub = Lokasi.query.filter_by(kode_bandara="SUB").first()
        dps = Lokasi.query.filter_by(kode_bandara="DPS").first()
        cgk_id, sub_id, dps_id = cgk.id, sub.id, dps.id

    # GET itinerary
    res_get = client.get('/flight/itinerary')
    assert res_get.status_code == 200

    # POST valid itinerary
    data = {
        'segment_origin_id': [cgk_id, sub_id],
        'segment_dest_id': [sub_id, dps_id],
        'segment_date': ['2026-11-20', '2026-11-20']
    }
    res_post = client.post('/flight/itinerary', data=data)
    assert res_post.status_code == 200
    assert b"Opsi Itinerary" in res_post.data


def test_member_profile_and_compare_routes(client, app):
    """Test member profile update, ticket validation, and preferences comparison."""
    # Profile GET
    res_prof = client.get('/flight/profile')
    assert res_prof.status_code == 200

    # Profile POST update
    update_data = {
        'action': 'validate_ticket',
        'nama_lengkap': 'Budi Santoso',
        'nomor_identitas': '3171011501850002',
        'tanggal_lahir': '1985-01-15',
        'kewarganegaraan': 'Indonesia',
        'nomor_telepon': '081288990011',
        'alamat': 'Jakarta'
    }
    res_val = client.post('/flight/profile', data=update_data)
    assert res_val.status_code == 200
    assert b"Profil lengkap" in res_val.data

    # Compare GET with time bucket
    with app.app_context():
        cgk = Lokasi.query.filter_by(kode_bandara="CGK").first()
        dps = Lokasi.query.filter_by(kode_bandara="DPS").first()
        cgk_id, dps_id = cgk.id, dps.id

    res_comp = client.get(f'/flight/compare?origin_id={cgk_id}&dest_id={dps_id}&travel_date=2026-11-20&time_bucket=pagi')
    assert res_comp.status_code == 200
    assert b"GA-101" in res_comp.data


def test_manager_routes(client, app):
    """Test manager bookings, visitor search, visitor booking, and lookup."""
    with app.app_context():
        cgk = Lokasi.query.filter_by(kode_bandara="CGK").first()
        dps = Lokasi.query.filter_by(kode_bandara="DPS").first()
        cgk_id, dps_id = cgk.id, dps.id
        flight = Penerbangan.query.first()
        f_id = flight.id
        visitor = AkunPengunjung.query.first()
        v_id = visitor.id

    # Manager bookings
    res_mgr = client.get('/flight/manager/bookings?status=Confirmed')
    assert res_mgr.status_code == 200

    # Visitor search
    res_vis_s = client.get(f'/flight/visitor/search?origin_id={cgk_id}&dest_id={dps_id}&travel_date=2026-11-20')
    assert res_vis_s.status_code == 200

    # Visitor book form GET
    res_vis_form = client.get(f'/flight/visitor/book/{f_id}')
    assert res_vis_form.status_code == 200

    # Visitor book POST
    vis_data = {
        'account_id': v_id,
        'nama_lengkap': 'Siti Rahma',
        'tipe_identitas': 'KTP',
        'nomor_identitas': '3201015509930005',
        'email': 'siti.rahma@example.com',
        'nomor_telepon': '081298765432'
    }
    res_vis_post = client.post(f'/flight/visitor/book/{f_id}', data=vis_data, follow_redirects=True)
    assert res_vis_post.status_code == 200
    assert b"Pemesanan atas nama pengunjung berhasil dibuat" in res_vis_post.data

    # Manager lookup valid code
    res_lookup = client.get('/flight/manager/lookup?code=BK-TESTCONF01')
    assert res_lookup.status_code == 200
    assert b"Pemesanan Ditemukan" in res_lookup.data

    # Manager lookup invalid code
    res_lookup_inv = client.get('/flight/manager/lookup?code=BK-INVALID999')
    assert res_lookup_inv.status_code == 200
    assert b"Kode booking reference tidak sesuai" in res_lookup_inv.data
