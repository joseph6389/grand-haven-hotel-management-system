from datetime import date, timedelta
from decimal import Decimal
import pytest
from app.extensions import db
from app.models.room import Room
from app.models.guest import Guest
from app.models.reservation import Reservation, ReservationStatusHistory
from app.models.audit import AuditLog
from app.models.payment import Payment
from app.models.user import User, Role
from app.services.reservation_service import create_reservation
from app.services.payment_service import process_payment, process_refund


def test_payment_recording_and_ledger(app):
    """Test payment simulation, balance calculation, and refund processing."""
    with app.app_context():
        today = date.today()
        guest = Guest.query.first()
        room201 = Room.query.filter_by(room_number='201').first()

        res = create_reservation(
            guest_id=guest.id,
            room_ids=[room201.id],
            check_in=today + timedelta(days=40),
            check_out=today + timedelta(days=42),  # 2 nights * ₹250 = ₹500 + 12% = ₹560
            adults_count=2
        )
        assert res.total_amount == Decimal('560.00')
        assert res.paid_amount == Decimal('0.00')
        assert res.outstanding_balance == Decimal('560.00')
        assert res.payment_status == 'unpaid'

        # Record partial payment ₹300
        pay1 = process_payment(res.id, Decimal('300.00'), payment_method='simulation', notes='Partial payment')
        assert pay1 is not None
        assert pay1.currency == 'INR'
        assert res.paid_amount == Decimal('300.00')
        assert res.outstanding_balance == Decimal('260.00')
        assert res.payment_status == 'partially_paid'

        # Attempting to overpay by ₹300 (when only ₹260 is due) must raise ValueError
        with pytest.raises(ValueError):
            process_payment(res.id, Decimal('300.00'))

        # Pay remaining balance ₹260
        pay2 = process_payment(res.id, Decimal('260.00'), payment_method='credit_card')
        assert res.paid_amount == Decimal('560.00')
        assert res.outstanding_balance == Decimal('0.00')
        assert res.payment_status == 'paid'

        # Process refund on pay1
        refunded_pay = process_refund(pay1.id, reason="Customer compensation")
        assert refunded_pay.payment_status == 'refunded'
        assert res.paid_amount == Decimal('260.00')
        assert res.outstanding_balance == Decimal('300.00')


def test_partial_and_full_refund(app):
    """Verify partial refunds preserve the correct payment and reservation balances."""
    with app.app_context():
        today = date.today()
        guest = Guest.query.first()
        room = Room.query.filter_by(room_number='201').first()

        reservation = create_reservation(
            guest_id=guest.id,
            room_ids=[room.id],
            check_in=today + timedelta(days=60),
            check_out=today + timedelta(days=62),
            adults_count=2
        )

        payment = process_payment(
            reservation.id,
            Decimal('300.00'),
            payment_method='simulation'
        )
        reservation.status = 'cancelled'
        cancellation = ReservationStatusHistory(
            reservation_id=reservation.id,
            previous_status='confirmed',
            new_status='cancelled',
            request_source='guest_account',
            requested_by_guest_id=guest.id,
            cancellation_fee=Decimal('100.00'),
            refund_status='pending_review',
            reason='Cancellation refund review test',
        )
        db.session.add(cancellation)
        db.session.commit()

        with pytest.raises(ValueError):
            process_refund(payment.id, refund_amount=Decimal('0.00'))
        with pytest.raises(ValueError):
            process_refund(payment.id, refund_amount=Decimal('301.00'))

        # Refund only ₹100 from the ₹300 payment.
        process_refund(
            payment.id,
            refund_amount=Decimal('100.00'),
            reason='Partial refund test'
        )

        db_payment = db.session.get(Payment, payment.id)
        db_reservation = db.session.get(Reservation, reservation.id)

        assert db_payment.refunded_amount == Decimal('100.00')
        assert db_payment.payment_status == 'partially_refunded'
        assert db_reservation.paid_amount == Decimal('200.00')
        assert db.session.get(ReservationStatusHistory, cancellation.id).refund_status == 'recorded'
        refund_audit = AuditLog.query.filter_by(
            action='PROCESS_REFUND', entity_id=payment.payment_reference
        ).one()
        assert 'External payout was not verified' in refund_audit.details

        # Refund the remaining ₹200 from the same payment.
        process_refund(payment.id, reason='Complete refund test')

        db.session.refresh(db_payment)
        db.session.refresh(db_reservation)

        assert db_payment.refunded_amount == Decimal('300.00')
        assert db_payment.payment_status == 'refunded'
        assert db_reservation.paid_amount == Decimal('0.00')

        # A fully refunded payment must not be refunded again.
        with pytest.raises(ValueError):
            process_refund(payment.id)


def test_payment_ledger_is_limited_to_hotel_staff(app, client):
    with app.app_context():
        role = Role(name='Auditor', description='Read-only audit role')
        db.session.add(role)
        db.session.flush()
        user = User(
            username='auditor_test',
            email='auditor_test@grandhavenhotel.com',
            full_name='Test Auditor',
            role_id=role.id,
            is_active=True,
        )
        user.set_password('AuditorTest@123')
        db.session.add(user)
        db.session.commit()

    login_response = client.post(
        '/login',
        data={'username': 'auditor_test', 'password': 'AuditorTest@123'},
    )
    assert login_response.status_code == 302

    response = client.get('/payments/')
    assert response.status_code == 403



def test_refund_dashboard_sums_partial_and_full_ledger_amounts(app, client, auth):
    with app.app_context():
        guest = Guest.query.first()
        room = Room.query.filter_by(room_number='201').first()
        reservation = create_reservation(
            guest_id=guest.id, room_ids=[room.id],
            check_in=date.today() + timedelta(days=100),
            check_out=date.today() + timedelta(days=102), adults_count=1,
        )
        db.session.add_all([
            Payment(reservation_id=reservation.id, payment_reference='TEST-PARTIAL',
                    amount=Decimal('300.00'), refunded_amount=Decimal('100.00'),
                    currency='INR', payment_method='simulation', payment_status='partially_refunded'),
            Payment(reservation_id=reservation.id, payment_reference='TEST-FULL',
                    amount=Decimal('200.00'), refunded_amount=Decimal('200.00'),
                    currency='INR', payment_method='simulation', payment_status='refunded'),
            Payment(reservation_id=reservation.id, payment_reference='TEST-FAILED',
                    amount=Decimal('900.00'), refunded_amount=Decimal('0.00'),
                    currency='INR', payment_method='simulation', payment_status='failed'),
        ])
        db.session.commit()
    auth.login('admin_test', 'AdminTest@123')
    response = client.get('/payments/')
    assert response.status_code == 200
    assert b'Refunds Recorded in Hotel Ledger' in response.data
    assert b'Net Payment Ledger' in response.data
    assert '₹300.00'.encode('utf-8') in response.data
    assert b'external payouts are not verified' in response.data
