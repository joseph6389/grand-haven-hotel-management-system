from app.models.room import Room
from app.models.audit import AuditLog


def test_rooms_list_requires_login(client):
    """Test /rooms route is protected."""
    res = client.get('/rooms')
    assert res.status_code == 302


def test_rooms_management_flow(client, auth):
    """Test listing rooms, filtering, adding a room, and status update."""
    auth.login()

    # List rooms
    res = client.get('/rooms')
    assert res.status_code == 200
    assert b"Room 101" in res.data
    assert b"Room 204" in res.data

    # Add a room
    add_res = client.post('/rooms/create', data={
        'room_number': '301',
        'room_type_id': 1,
        'floor': 3,
        'capacity': 2,
        'operational_status': 'operational',
        'notes': 'New room created during test'
    }, follow_redirects=True)
    assert add_res.status_code == 200
    assert b"Room 301 added successfully" in add_res.data
    assert Room.query.filter_by(room_number='301').first() is not None

    # Duplicate room number rejection
    dup_res = client.post('/rooms/create', data={
        'room_number': '301',
        'room_type_id': 1,
        'floor': 3,
        'capacity': 2
    }, follow_redirects=True)
    assert b"already registered" in dup_res.data

    # Operational status transition (mark maintenance)
    room301 = Room.query.filter_by(room_number='301').first()
    stat_res = client.post(f'/rooms/{room301.id}/status', data={
        'operational_status': 'maintenance'
    }, follow_redirects=True)
    assert stat_res.status_code == 200
    assert room301.operational_status == 'maintenance'


def test_room_create_rejects_overlong_room_number_without_insert(client, auth):
    """Reject room numbers beyond the ORM column length before database insertion."""
    auth.login()
    initial_count = Room.query.count()
    initial_audit_count = AuditLog.query.count()
    too_long = 'R' * 21

    response = client.post('/rooms/create', data={
        'room_number': too_long,
        'room_type_id': 1,
        'floor': 3,
        'capacity': 2,
        'operational_status': 'operational',
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Room number must be 20 characters or fewer' in response.data
    assert Room.query.count() == initial_count
    assert AuditLog.query.count() == initial_audit_count
    assert Room.query.filter_by(room_number=too_long).first() is None


def test_room_edit_rejects_overlong_room_number_without_update(client, auth):
    """Reject overlong edits without changing the existing room record."""
    auth.login()
    room = Room.query.filter_by(room_number='101').one()
    original_number = room.room_number
    initial_audit_count = AuditLog.query.count()
    too_long = 'R' * 21

    response = client.post(f'/rooms/{room.id}/edit', data={
        'room_number': too_long,
        'room_type_id': room.room_type_id,
        'floor': room.floor,
        'capacity': room.capacity,
        'operational_status': room.operational_status,
        'notes': room.notes or '',
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Room number must be 20 characters or fewer' in response.data
    assert Room.query.filter_by(id=room.id).one().room_number == original_number
    assert AuditLog.query.count() == initial_audit_count
