from datetime import datetime, time, timedelta
from decimal import Decimal
import pytest

from app.extensions import db
from app.models.audit import AuditLog
from app.models.guest import Guest
from app.models.reservation import Reservation, ReservationStatusHistory
from app.models.room import Room
from app.models.user import Role, User
from app.services.availability_service import is_room_available
from app.services.reservation_service import create_reservation, cancel_reservation
from app.utils.datetime_utils import india_today, INDIA_TZ


def _register(client, email='new.guest@example.com', phone='+91 9876543210'):
    phone_digits = ''.join(char for char in phone if char.isdigit())[-10:]
    response = client.post('/register', data={
        'first_name': 'New',
        'last_name': 'Guest',
        'username': 'new_guest',
        'email': email,
        'phone': phone_digits,
        'password': 'CorrectHorseBattery1',
        'confirm_password': 'CorrectHorseBattery1',
        'city': 'Bengaluru',
        'state': 'Karnataka',
        'postal_code': '560001',
    }, follow_redirects=True)
    if response.request.path == '/login':
        response = client.post('/login', data={
            'username': 'new_guest', 'password': 'CorrectHorseBattery1',
        }, follow_redirects=True)
    return response


def _make_reservation(app, guest_id, *, paid=Decimal('0.00'), room_number='101'):
    with app.app_context():
        room = Room.query.filter_by(room_number=room_number).one()
        today = india_today()
        return create_reservation(
            guest_id=guest_id,
            room_ids=[room.id],
            check_in=today + timedelta(days=12),
            check_out=today + timedelta(days=14),
            adults_count=1,
            initial_payment_amount=paid or None,
        ).id


def test_guest_registration_creates_linked_profile_and_login(client, app):
    response = client.post('/register', data={
        'first_name': 'New', 'last_name': 'Guest', 'username': 'new_guest',
        'email': 'new.guest@example.com', 'phone': '9876543210',
        'password': 'CorrectHorseBattery1', 'confirm_password': 'CorrectHorseBattery1',
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Your account was created successfully. Please log in.' in response.data
    assert b'Log in to your account' in response.data
    with app.app_context():
        user = User.query.filter_by(email='new.guest@example.com').one()
        assert user.username == 'new_guest'
        assert user.role.name.lower() == 'guest'
        assert user.guest_profile.email == user.email
        assert user.guest_profile.country == 'India'
        assert user.password_hash != 'CorrectHorseBattery1'
        assert 'scrypt:' in user.password_hash or 'pbkdf2:' in user.password_hash
    rejected = client.post('/login', data={
        'username': 'new_guest', 'password': 'incorrect-password',
    }, follow_redirects=True)
    assert b'Invalid username or password' in rejected.data
    rejected_email_login = client.post('/login', data={
        'username': 'new.guest@example.com', 'password': 'CorrectHorseBattery1',
    }, follow_redirects=True)
    assert b'Invalid username or password' in rejected_email_login.data
    response = client.post('/login', data={
        'username': 'new_guest', 'password': 'CorrectHorseBattery1',
    }, follow_redirects=True)
    assert b'Grand Haven Hotel' in response.data
    assert b'Rooms & Suites' in response.data
    assert b'Amenities' in response.data
    assert b'Your reservation history' not in response.data


def test_registration_rejects_invalid_phone_and_duplicate_username(client, app):
    invalid = client.post('/register', data={
        'first_name': 'New', 'last_name': 'Guest', 'username': 'new_guest',
        'email': 'bad.phone@example.com', 'phone': '12345abcde',
        'password': 'CorrectHorseBattery1', 'confirm_password': 'CorrectHorseBattery1',
    }, follow_redirects=True)
    assert b'exactly 10 digits' in invalid.data
    bad_length = client.post('/register', data={
        'first_name': 'New', 'last_name': 'Guest', 'username': 'new_guest',
        'email': 'short.phone@example.com', 'phone': '123456789',
        'password': 'CorrectHorseBattery1', 'confirm_password': 'CorrectHorseBattery1',
    }, follow_redirects=True)
    assert b'exactly 10 digits' in bad_length.data
    _register(client)
    client.post('/account/logout')
    duplicate = client.post('/register', data={
        'first_name': 'Other', 'last_name': 'Guest', 'username': 'NEW_GUEST',
        'email': 'other.guest@example.com', 'phone': '9876543211',
        'password': 'CorrectHorseBattery1', 'confirm_password': 'CorrectHorseBattery1',
    }, follow_redirects=True)
    assert b'username is already taken' in duplicate.data


def test_guest_booking_rejects_missing_required_fields(client):
    response = client.post('/book-now', data={}, follow_redirects=True)
    assert b'Please fill in all required guest and booking information.' in response.data
    with client.application.app_context():
        assert Reservation.query.count() == 0


def test_registration_does_not_claim_existing_unlinked_profile(client, app):
    response = _register(client, email='julian@test.com', phone='+91 9876543212')
    assert b'Contact reception to verify and link it safely' in response.data
    with app.app_context():
        assert User.query.filter_by(email='julian@test.com').first() is None
        assert Guest.query.filter_by(email='julian@test.com').count() == 1


def test_registered_guest_booking_uses_own_profile(client, app):
    _register(client)
    with app.app_context():
        room_id = Room.query.filter_by(room_number='101').one().id
        today = india_today()
        check_in = (today + timedelta(days=20)).isoformat()
        check_out = (today + timedelta(days=22)).isoformat()
    response = client.post('/book-now', data={
        'room_id': str(room_id),
        'check_in': check_in, 'check_out': check_out, 'adults': '1', 'children': '0',
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Your reservation has been confirmed' in response.data
    with app.app_context():
        user = User.query.filter_by(email='new.guest@example.com').one()
        reservation = Reservation.query.filter_by(guest_id=user.guest_profile_id).one()
        assert reservation.guest.first_name == 'New'


def test_public_guest_can_book_without_login(client, app):
    with app.app_context():
        room_id = Room.query.filter_by(room_number='101').one().id
        today = india_today()
        check_in = (today + timedelta(days=30)).isoformat()
        check_out = (today + timedelta(days=32)).isoformat()
    response = client.post('/book-now', data={
        'first_name': 'Avery', 'last_name': 'Stone', 'email': 'avery.stone@example.com',
        'phone': '+91 9876543212', 'room_id': str(room_id),
        'check_in': check_in, 'check_out': check_out, 'adults': '1', 'children': '0',
        'special_requests': 'Late arrival',
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Your reservation has been confirmed' in response.data
    with app.app_context():
        guest = Guest.query.filter_by(email='avery.stone@example.com').one()
        reservation = Reservation.query.filter_by(guest_id=guest.id).one()
        assert reservation.special_requests == 'Late arrival'
        assert reservation.check_in_date.isoformat() == check_in
        assert reservation.check_out_date.isoformat() == check_out


def test_public_guest_booking_rejects_missing_required_field(client, app):
    with app.app_context():
        room_id = Room.query.filter_by(room_number='101').one().id
        today = india_today()
    response = client.post('/book-now', data={
        'first_name': 'Julian', 'last_name': 'Thorne', 'email': 'julian@test.com',
        'phone': '+91 9876543212', 'room_id': str(room_id),
        'check_in': (today + timedelta(days=30)).isoformat(),
        # check_out deliberately omitted
    }, follow_redirects=True)
    assert b'Please fill in all required guest and booking information.' in response.data
    with app.app_context():
        assert Reservation.query.count() == 0


def test_guest_cannot_view_another_guests_reservation(client, app):
    response = _register(client)
    assert response.status_code == 200
    with app.app_context():
        owner = User.query.filter_by(email='new.guest@example.com').one()
        owner_reservation_id = _make_reservation(app, owner.guest_profile_id)
        other_guest = Guest.query.filter_by(email='julian@test.com').one()
        other_reservation_id = _make_reservation(app, other_guest.id, room_number='102')
    assert client.get(f'/account/reservations/{owner_reservation_id}').status_code == 200
    assert client.get(f'/account/reservations/{other_reservation_id}').status_code == 404
    assert b'julian.thorne@example.com' not in client.get('/account').data


def test_guest_cannot_open_staff_or_admin_pages(client):
    _register(client)
    assert client.get('/dashboard').status_code == 403
    assert client.get('/admin/settings').status_code == 403
    assert client.get('/api/admin/events').status_code == 403


def test_live_operations_feed_is_admin_only(client, app, auth):
    with app.app_context():
        db.session.add(AuditLog(
            action='GUEST_REGISTER', entity_type='Guest', entity_id='99',
            details='private test payload containing new.guest@example.com',
        ))
        db.session.commit()
    auth.login('rec_test', 'RecTest@123')
    assert client.get('/api/admin/events').status_code == 403
    assert client.get('/api/staff/events').status_code == 200
    auth.logout()
    auth.login('admin_test', 'AdminTest@123')
    response = client.get('/api/admin/events?after=0')
    assert response.status_code == 200
    assert any(event['label'] == 'Guest account registered' for event in response.json['events'])
    assert b'new.guest@example.com' not in response.data


def test_guest_logout_is_post_only_and_ends_session(client):
    _register(client)
    assert client.get('/account/logout').status_code == 405
    assert client.post('/account/logout', follow_redirects=True).status_code == 200
    assert b'Your reservation history' not in client.get('/account').data


def test_guest_password_change_requires_current_password(client, app):
    _register(client)
    with app.app_context():
        guest_user = User.query.filter_by(email='new.guest@example.com').one()
        old_hash = guest_user.password_hash
    bad = client.post('/account/profile', data={
        'first_name': 'New', 'last_name': 'Guest', 'phone': '+91 9876543210',
        'current_password': 'incorrect', 'new_password': 'AnotherSecurePass123',
        'confirm_password': 'AnotherSecurePass123',
    }, follow_redirects=True)
    assert b'enter your current password' in bad.data
    with app.app_context():
        guest_user = User.query.filter_by(email='new.guest@example.com').one()
        assert guest_user.password_hash == old_hash
    good = client.post('/account/profile', data={
        'first_name': 'New', 'last_name': 'Guest', 'phone': '+91 9876543210',
        'current_password': 'CorrectHorseBattery1', 'new_password': 'AnotherSecurePass123',
        'confirm_password': 'AnotherSecurePass123',
    }, follow_redirects=True)
    assert b'profile was updated' in good.data
    with app.app_context():
        assert User.query.filter_by(email='new.guest@example.com').one().check_password('AnotherSecurePass123')


def test_guest_self_cancellation_is_audited_and_does_not_complete_refund(client, app):
    _register(client)
    with app.app_context():
        owner = User.query.filter_by(email='new.guest@example.com').one()
        guest_id = owner.guest_profile_id
        reservation_id = _make_reservation(app, guest_id, paid=Decimal('25.00'))
        room_id = db.session.get(Reservation, reservation_id).assigned_rooms[0].id

    response = client.post(
        f'/account/reservations/{reservation_id}/cancel',
        data={'confirm_cancel': 'yes'},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b'Pending Review' in response.data
    assert b'no external payout is confirmed' in response.data
    duplicate = client.post(
        f'/account/reservations/{reservation_id}/cancel',
        data={'confirm_cancel': 'yes'}, follow_redirects=True,
    )
    assert b'no longer eligible for cancellation' in duplicate.data
    with app.app_context():
        reservation = db.session.get(Reservation, reservation_id)
        history = ReservationStatusHistory.query.filter_by(reservation_id=reservation_id).order_by(
            ReservationStatusHistory.id.desc()
        ).first()
        audit = AuditLog.query.filter_by(action='GUEST_SELF_CANCEL', entity_id=str(reservation_id)).one()
        assert reservation.status == 'cancelled'
        assert reservation.paid_amount == Decimal('25.00')
        assert history.request_source == 'guest_account'
        assert history.requested_by_guest_id == guest_id
        assert history.changed_by_id is None
        assert history.refund_status == 'pending_review'
        assert ReservationStatusHistory.query.filter_by(
            reservation_id=reservation_id, new_status='cancelled'
        ).count() == 1
        assert audit.user_id is None
        assert is_room_available(room_id, reservation.check_in_date, reservation.check_out_date)


def test_phone_cancellation_requires_multiple_matching_guest_details(client, app, auth):
    with app.app_context():
        guest = Guest.query.filter_by(email='julian@test.com').one()
        guest_id = guest.id
        reservation_id = _make_reservation(app, guest_id)
        reservation = db.session.get(Reservation, reservation_id)
        confirmation = reservation.confirmation_number
    auth.login('rec_test', 'RecTest@123')
    response = client.post(f'/reservations/{reservation_id}/cancel', data={
        'confirmation_number': confirmation,
        'verified_guest_name': 'Julian Thorne',
        'verified_guest_email': 'julian@test.com',
        'verified_guest_phone': '+91 0000000000',
        'reason': 'Guest called the front desk to cancel.',
    }, follow_redirects=True)
    assert b'Guest details did not match' in response.data
    with app.app_context():
        assert db.session.get(Reservation, reservation_id).status == 'confirmed'
    response = client.post(f'/reservations/{reservation_id}/cancel', data={
        'confirmation_number': confirmation,
        'verified_guest_name': 'Julian Thorne',
        'verified_guest_email': 'julian@test.com',
        'verified_guest_phone': '+91 9876543212',
        'reason': 'Guest called the front desk to cancel.',
    }, follow_redirects=True)
    assert b'cancelled' in response.data
    events = client.get('/api/staff/events?after=0').json['events']
    event = next(item for item in events if item['label'] == 'Reception processed a phone cancellation')
    assert set(event) == {'id', 'label', 'timestamp'}
    assert b'julian@test.com' not in client.get('/api/staff/events?after=0').data
    with app.app_context():
        history = ReservationStatusHistory.query.filter_by(reservation_id=reservation_id).order_by(
            ReservationStatusHistory.id.desc()
        ).first()
        assert history.request_source == 'phone'
        assert history.requested_by_guest_id == guest_id
        assert history.changed_by_id == User.query.filter_by(username='rec_test').one().id
        assert history.refund_status == 'not_applicable'


@pytest.mark.parametrize(
    ('hours_before_checkin', 'paid', 'expected_fee', 'expected_refund_status'),
    [
        (48, Decimal('5000.00'), Decimal('500.00'), 'pending_review'),
        (47, Decimal('5000.00'), Decimal('500.00'), 'pending_review'),
        (48, Decimal('300.00'), Decimal('300.00'), 'not_applicable'),
        (48, Decimal('0.00'), Decimal('0.00'), 'not_applicable'),
        (49, Decimal('500.00'), None, 'pending_review'),
    ],
)
def test_cancellation_fee_boundary_cap_and_review_status(
    app, monkeypatch, hours_before_checkin, paid, expected_fee, expected_refund_status
):
    with app.app_context():
        guest = Guest.query.filter_by(email='julian@test.com').one()
        room = Room.query.filter_by(room_number='201').one()
        check_in = india_today() + timedelta(days=80)
        check_out = check_in + timedelta(days=22 if paid > Decimal('1000.00') else 2)
        reservation = create_reservation(
            guest_id=guest.id, room_ids=[room.id], check_in=check_in,
            check_out=check_out, initial_payment_amount=paid,
        )
        checkin_boundary = datetime.combine(check_in, time(15, 0), tzinfo=INDIA_TZ)
        frozen_now = checkin_boundary - timedelta(hours=hours_before_checkin)
        monkeypatch.setattr('app.services.reservation_service.india_now', lambda: frozen_now)
        cancelled = cancel_reservation(
            reservation.id, request_source='guest_account', requested_by_guest_id=guest.id,
            reason='Policy boundary regression test',
        )
        db.session.refresh(cancelled)
        history = ReservationStatusHistory.query.filter_by(
            reservation_id=cancelled.id, new_status='cancelled'
        ).one()
        audit = AuditLog.query.filter_by(action='GUEST_SELF_CANCEL', entity_id=str(cancelled.id)).one()
        assert history.cancellation_fee == expected_fee
        assert history.refund_status == expected_refund_status
        assert cancelled.paid_amount == min(paid, cancelled.total_amount)
        assert cancelled.status == 'cancelled'
        audit_details = __import__('json').loads(audit.details)
        assert audit_details['potential_refund_amount'] == (
            str(max(Decimal('0.00'), cancelled.paid_amount - expected_fee))
            if expected_fee is not None else None
        )


def test_cancellation_rejects_already_passed_checkin_boundary(app, monkeypatch):
    with app.app_context():
        guest = Guest.query.filter_by(email='julian@test.com').one()
        reservation_id = _make_reservation(app, guest.id, paid=Decimal('100.00'))
        reservation = db.session.get(Reservation, reservation_id)
        frozen_now = datetime.combine(reservation.check_in_date, time(15, 1), tzinfo=INDIA_TZ)
        monkeypatch.setattr('app.services.reservation_service.india_now', lambda: frozen_now)
        with pytest.raises(ValueError, match='check-in time has passed'):
            cancel_reservation(
                reservation.id, request_source='guest_account', requested_by_guest_id=guest.id,
                reason='Past check-in regression test',
            )
        db.session.refresh(reservation)
        assert reservation.status == 'confirmed'
