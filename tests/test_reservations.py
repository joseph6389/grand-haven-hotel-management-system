import pytest
from datetime import date, timedelta
from decimal import Decimal
from app.extensions import db
from app.models.room import Room
from app.models.guest import Guest
from app.models.reservation import Reservation
from app.models.audit import AuditLog
from app.services.availability_service import is_room_available, get_available_rooms, parse_date
from app.services.reservation_service import create_reservation, edit_reservation, update_reservation_status
from app.utils.datetime_utils import india_today


def test_availability_service(app):
    """Test date-overlap checking and maintenance filtering."""
    with app.app_context():
        today = date.today()
        d_in = today + timedelta(days=10)
        d_out = today + timedelta(days=14)

        # Operational rooms (101, 102, 201) should be available
        avail = get_available_rooms(d_in, d_out)
        avail_numbers = [r.room_number for r in avail]
        assert '101' in avail_numbers
        assert '102' in avail_numbers
        assert '201' in avail_numbers

        # Maintenance room (204) must NOT be available
        assert '204' not in avail_numbers
        assert not is_room_available(4, d_in, d_out)  # Room 204


def test_parse_date_normalizes_datetime_to_date():
    from datetime import datetime

    value = datetime(2026, 10, 25, 15, 30)
    assert parse_date(value) == date(2026, 10, 25)


def test_reservation_creation_and_overlap_prevention(app):
    """Test transactional reservation creation and double-booking barrier."""
    with app.app_context():
        today = date.today()
        guest = Guest.query.first()
        room101 = Room.query.filter_by(room_number='101').first()

        d1_in = today + timedelta(days=5)
        d1_out = today + timedelta(days=9)

        # 1. Create first reservation
        res1 = create_reservation(
            guest_id=guest.id,
            room_ids=[room101.id],
            check_in=d1_in,
            check_out=d1_out,
            adults_count=2,
            children_count=0
        )
        assert res1 is not None
        assert res1.confirmation_number.startswith('GH-')
        assert res1.status == 'confirmed'
        assert res1.total_nights == 4
        # Room rate ₹150 * 4 = ₹600 + 12% tax (₹72) = ₹672
        assert res1.total_amount == Decimal('672.00')

        # 2. Verify Room 101 is now NOT available for overlapping dates
        assert not is_room_available(room101.id, d1_in, d1_out)
        # Partially overlapping (days 7 to 11)
        assert not is_room_available(room101.id, today + timedelta(days=7), today + timedelta(days=11))

        # 3. Attempt to book same room for overlapping dates -> MUST RAISE EXCEPTION
        with pytest.raises(ValueError) as excinfo:
            create_reservation(
                guest_id=guest.id,
                room_ids=[room101.id],
                check_in=today + timedelta(days=6),
                check_out=today + timedelta(days=8),
                adults_count=1
            )
        assert "unavailable" in str(excinfo.value).lower() or "booked" in str(excinfo.value).lower()

        # 4. Booking same room for non-overlapping future dates -> MUST SUCCEED
        d2_in = today + timedelta(days=10)
        d2_out = today + timedelta(days=12)
        res2 = create_reservation(
            guest_id=guest.id,
            room_ids=[room101.id],
            check_in=d2_in,
            check_out=d2_out,
            adults_count=1
        )
        assert res2 is not None
        assert res2.total_nights == 2


def test_reservation_lifecycle_and_cancellation(app):
    """Test transitions: confirmed -> checked_in -> checked_out and cancellation freeing inventory."""
    with app.app_context():
        today = date.today()
        guest = Guest.query.first()
        room102 = Room.query.filter_by(room_number='102').first()

        check_in = today + timedelta(days=20)
        check_out = today + timedelta(days=23)

        res = create_reservation(
            guest_id=guest.id,
            room_ids=[room102.id],
            check_in=check_in,
            check_out=check_out,
            adults_count=2
        )
        assert res.status == 'confirmed'

        # Check-in
        res = update_reservation_status(res.id, 'checked_in', reason='Guest arrived')
        assert res.status == 'checked_in'

        # Check-out
        res = update_reservation_status(res.id, 'checked_out', reason='Guest departed')
        assert res.status == 'checked_out'

        # Create another reservation to test cancellation
        res_cancel = create_reservation(
            guest_id=guest.id,
            room_ids=[room102.id],
            check_in=today + timedelta(days=30),
            check_out=today + timedelta(days=33)
        )
        # Room is blocked
        assert not is_room_available(room102.id, today + timedelta(days=30), today + timedelta(days=33))

        # Cancel reservation
        res_cancel = update_reservation_status(res_cancel.id, 'cancelled', reason='Test cancellation')
        assert res_cancel.status == 'cancelled'

        # Room MUST be available again!
        assert is_room_available(room102.id, today + timedelta(days=30), today + timedelta(days=33))


def test_reservation_rejects_invalid_guest_counts_and_duplicate_rooms(app):
    """Reject malformed booking inputs before creating any reservation records."""
    with app.app_context():
        today = date.today()
        guest = Guest.query.first()
        room101 = Room.query.filter_by(room_number='101').first()
        before = Reservation.query.count()

        with pytest.raises(ValueError, match='adult'):
            create_reservation(
                guest_id=guest.id, room_ids=[room101.id],
                check_in=today + timedelta(days=40),
                check_out=today + timedelta(days=42), adults_count=0
            )

        with pytest.raises(ValueError, match='negative'):
            create_reservation(
                guest_id=guest.id, room_ids=[room101.id],
                check_in=today + timedelta(days=40),
                check_out=today + timedelta(days=42), children_count=-1
            )

        with pytest.raises(ValueError, match='once'):
            create_reservation(
                guest_id=guest.id, room_ids=[room101.id, room101.id],
                check_in=today + timedelta(days=40),
                check_out=today + timedelta(days=42)
            )

        assert Reservation.query.count() == before


@pytest.mark.parametrize(('field', 'value', 'message'), [
    ('adults', '', 'Adults is required'),
    ('adults', 'two', 'Adults must be a whole number'),
    ('adults', '1.5', 'Adults must be a whole number'),
    ('adults', '0', 'At least one adult is required'),
    ('children', '', 'Children is required'),
    ('children', 'many', 'Children must be a whole number'),
    ('children', '1.5', 'Children must be a whole number'),
    ('children', '-1', 'Children count cannot be negative'),
])
def test_reservation_form_guest_count_validation(client, auth, field, value, message):
    auth.login()
    from datetime import date, timedelta
    check_in = date.today() + timedelta(days=5)
    data = {
        'guest_option': 'existing',
        'guest_id': '1',
        'check_in': check_in.isoformat(),
        'check_out': (check_in + timedelta(days=2)).isoformat(),
        'adults': '1',
        'children': '0',
    }
    data[field] = value
    response = client.post('/reservations/create', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert message.encode() in response.data


@pytest.mark.parametrize('room_numbers', [('101',), ('101', '102')])
def test_staff_reservation_wizard_creates_one_or_multiple_rooms_with_zero_payment(
    client, app, auth, room_numbers
):
    auth.login('rec_test', 'RecTest@123')
    with app.app_context():
        guest_id = Guest.query.filter_by(email='julian@test.com').one().id
        room_ids = [Room.query.filter_by(room_number=number).one().id for number in room_numbers]
        check_in = india_today() + timedelta(days=60)
        check_out = check_in + timedelta(days=2)

    response = client.post('/reservations/create', data={
        'guest_option': 'existing',
        'guest_id': str(guest_id),
        'check_in': check_in.isoformat(),
        'check_out': check_out.isoformat(),
        'adults': '2',
        'children': '0',
        'room_ids': [str(room_id) for room_id in room_ids],
        'initial_payment': '0.00',
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'created successfully' in response.data
    with app.app_context():
        reservation = Reservation.query.filter_by(guest_id=guest_id).one()
        assert {allocation.room.room_number for allocation in reservation.room_allocations} == set(room_numbers)
        assert reservation.payments.count() == 0


def test_staff_reservation_wizard_rejects_missing_rooms_and_invalid_dates(client, auth, app):
    auth.login('rec_test', 'RecTest@123')
    with app.app_context():
        guest_id = Guest.query.filter_by(email='julian@test.com').one().id
        check_in = india_today() + timedelta(days=70)
        before = Reservation.query.count()

    base_data = {
        'guest_option': 'existing',
        'guest_id': str(guest_id),
        'check_in': check_in.isoformat(),
        'check_out': (check_in + timedelta(days=2)).isoformat(),
        'adults': '1',
        'children': '0',
    }
    missing_rooms = client.post('/reservations/create', data=base_data, follow_redirects=True)
    assert b'At least one room must be selected' in missing_rooms.data

    invalid_dates = dict(base_data, room_ids='1', check_out=check_in.isoformat())
    invalid = client.post('/reservations/create', data=invalid_dates, follow_redirects=True)
    assert b'Check-out date must be strictly after check-in date' in invalid.data
    with app.app_context():
        assert Reservation.query.count() == before


def test_reservation_edit_updates_rooms_dates_pricing_and_audit(app):
    with app.app_context():
        today = date.today()
        guest = Guest.query.first()
        room101 = Room.query.filter_by(room_number='101').first()
        room102 = Room.query.filter_by(room_number='102').first()
        reservation = create_reservation(
            guest_id=guest.id,
            room_ids=[room101.id],
            check_in=today + timedelta(days=10),
            check_out=today + timedelta(days=13),
            adults_count=2,
            initial_payment_amount=Decimal('100.00'),
        )
        reservation_id = reservation.id
        guest_id = reservation.guest_id
        payment_ids = [payment.id for payment in reservation.payments.all()]

        edited = edit_reservation(
            reservation_id=reservation.id,
            room_ids=[room102.id],
            check_in=today + timedelta(days=11),
            check_out=today + timedelta(days=13),
            adults_count=1,
            children_count=1,
            changed_by_id=None,
        )

        assert edited.id == reservation_id
        assert edited.guest_id == guest_id
        assert edited.check_in_date == today + timedelta(days=11)
        assert edited.check_out_date == today + timedelta(days=13)
        assert edited.total_nights == 2
        assert edited.total_amount == Decimal('336.00')
        assert edited.paid_amount == Decimal('100.00')
        assert [room.id for room in edited.assigned_rooms] == [room102.id]
        assert [payment.id for payment in edited.payments.all()] == payment_ids
        assert AuditLog.query.filter_by(action='UPDATE_RESERVATION', entity_id=str(reservation_id)).count() == 1
        assert is_room_available(room101.id, today + timedelta(days=10), today + timedelta(days=13))
        assert not is_room_available(room102.id, today + timedelta(days=11), today + timedelta(days=13))


def test_reservation_edit_rejects_overlap_without_partial_changes(app):
    with app.app_context():
        today = date.today()
        guest = Guest.query.first()
        room101 = Room.query.filter_by(room_number='101').first()
        room102 = Room.query.filter_by(room_number='102').first()
        occupied = create_reservation(
            guest_id=guest.id, room_ids=[room101.id],
            check_in=today + timedelta(days=20), check_out=today + timedelta(days=23),
        )
        target = create_reservation(
            guest_id=guest.id, room_ids=[room102.id],
            check_in=today + timedelta(days=30), check_out=today + timedelta(days=33),
        )
        with pytest.raises(ValueError, match='booked by another guest'):
            edit_reservation(
                reservation_id=target.id,
                room_ids=[room101.id],
                check_in=today + timedelta(days=21),
                check_out=today + timedelta(days=24),
                adults_count=1,
            )
        db_target = db.session.get(Reservation, target.id)
        assert db_target.check_in_date == today + timedelta(days=30)
        assert [room.id for room in db_target.assigned_rooms] == [room102.id]
        assert AuditLog.query.filter_by(action='UPDATE_RESERVATION', entity_id=str(target.id)).count() == 0


def test_reservation_edit_rejects_checked_in_reservation(app):
    with app.app_context():
        today = date.today()
        guest = Guest.query.first()
        room = Room.query.filter_by(room_number='101').first()
        reservation = create_reservation(
            guest_id=guest.id, room_ids=[room.id],
            check_in=today + timedelta(days=40), check_out=today + timedelta(days=42),
        )
        update_reservation_status(reservation.id, 'checked_in', reason='Test lifecycle')
        with pytest.raises(ValueError, match='Only pending or confirmed'):
            edit_reservation(
                reservation_id=reservation.id,
                room_ids=[room.id],
                check_in=today + timedelta(days=40),
                check_out=today + timedelta(days=42),
                adults_count=1,
            )


def test_reservation_edit_route_renders_and_saves_form(client, auth, app):
    with app.app_context():
        today = date.today()
        guest = Guest.query.first()
        room101 = Room.query.filter_by(room_number='101').first()
        room102 = Room.query.filter_by(room_number='102').first()
        reservation = create_reservation(
            guest_id=guest.id, room_ids=[room101.id],
            check_in=today + timedelta(days=50), check_out=today + timedelta(days=53),
        )
        reservation_id = reservation.id
        new_room_id = room102.id
        new_check_in = today + timedelta(days=51)
        new_check_out = today + timedelta(days=53)

    auth.login()
    page = client.get(f'/reservations/{reservation_id}/edit')
    assert page.status_code == 200
    assert b'Edit Reservation' in page.data
    response = client.post(
        f'/reservations/{reservation_id}/edit',
        data={
            'check_in': new_check_in.isoformat(),
            'check_out': new_check_out.isoformat(),
            'adults': '1',
            'children': '1',
            'room_ids': str(new_room_id),
        },
    )
    assert response.status_code == 302
    with app.app_context():
        updated = db.session.get(Reservation, reservation_id)
        assert updated.check_in_date == new_check_in
        assert updated.check_out_date == new_check_out
        assert [room.id for room in updated.assigned_rooms] == [new_room_id]


def test_reservation_edit_route_shows_input_errors_without_server_error(client, auth, app):
    with app.app_context():
        today = date.today()
        guest = Guest.query.first()
        room = Room.query.filter_by(room_number='101').first()
        reservation = create_reservation(
            guest_id=guest.id, room_ids=[room.id],
            check_in=today + timedelta(days=60), check_out=today + timedelta(days=62),
        )
        reservation_id = reservation.id

    auth.login()
    response = client.post(
        f'/reservations/{reservation_id}/edit',
        data={
            'check_in': (today + timedelta(days=60)).isoformat(),
            'check_out': (today + timedelta(days=62)).isoformat(),
            'adults': '1.5',
            'children': '0',
            'room_ids': '1',
        },
    )
    assert response.status_code == 200
    assert b'Adults must be a whole number.' in response.data
    with app.app_context():
        unchanged = db.session.get(Reservation, reservation_id)
        assert unchanged.adults_count == 1


def test_reservation_creation_rejects_invalid_date_and_excess_capacity(app):
    with app.app_context():
        today = date.today()
        guest = Guest.query.first()
        room = Room.query.filter_by(room_number='101').first()
        before = Reservation.query.count()
        with pytest.raises(ValueError, match='after check-in'):
            create_reservation(
                guest_id=guest.id, room_ids=[room.id],
                check_in=today + timedelta(days=4), check_out=today + timedelta(days=4),
            )
        with pytest.raises(ValueError, match='capacity'):
            create_reservation(
                guest_id=guest.id, room_ids=[room.id],
                check_in=today + timedelta(days=5), check_out=today + timedelta(days=7),
                adults_count=2, children_count=1,
            )
        assert Reservation.query.count() == before


def test_reservation_edit_rejects_excess_capacity_and_total_below_paid(app):
    with app.app_context():
        today = date.today()
        guest = Guest.query.first()
        room = Room.query.filter_by(room_number='101').first()
        reservation = create_reservation(
            guest_id=guest.id, room_ids=[room.id],
            check_in=today + timedelta(days=70), check_out=today + timedelta(days=73),
            initial_payment_amount=Decimal('500.00'),
        )
        original_check_in = reservation.check_in_date
        with pytest.raises(ValueError, match='capacity'):
            edit_reservation(
                reservation_id=reservation.id, room_ids=[room.id],
                check_in=today + timedelta(days=71), check_out=today + timedelta(days=73),
                adults_count=2, children_count=1,
            )
        with pytest.raises(ValueError, match='less than payments already recorded'):
            edit_reservation(
                reservation_id=reservation.id, room_ids=[room.id],
                check_in=today + timedelta(days=71), check_out=today + timedelta(days=72),
                adults_count=1,
            )
        unchanged = db.session.get(Reservation, reservation.id)
        assert unchanged.check_in_date == original_check_in
        assert unchanged.paid_amount == Decimal('500.00')
