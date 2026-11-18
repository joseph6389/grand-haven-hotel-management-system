from datetime import timedelta
from decimal import Decimal

from app.extensions import db
from app.models.reservation import Reservation, ReservationRoom
from app.models.service import ReservationService, Service
from app.services.reservation_service import create_reservation
from app.utils.datetime_utils import india_today


def test_reservation_totals_are_computed_from_booking_and_ledger_rows(app):
    with app.app_context():
        start = india_today() + timedelta(days=30)
        reservation = create_reservation(
            guest_id=1,
            room_ids=[1],
            check_in=start,
            check_out=start + timedelta(days=3),
            initial_payment_amount=Decimal('100.00'),
        )

        assert reservation.total_nights == 3
        assert reservation.room_charges == Decimal('450.00')
        assert reservation.total_amount == Decimal('504.00')
        assert reservation.paid_amount == Decimal('100.00')
        assert reservation.outstanding_balance == Decimal('404.00')
        assert Reservation.query.filter(
            Reservation.paid_amount < Reservation.total_amount
        ).count() == 1

        service = Service(name='Normalization Test Service', unit_price=Decimal('20.00'))
        db.session.add(service)
        db.session.flush()
        line = ReservationService(
            reservation_id=reservation.id,
            service_id=service.id,
            quantity=2,
            unit_price=Decimal('18.50'),
            service_date=start,
        )
        db.session.add(line)
        db.session.commit()
        assert line.total_price == Decimal('37.00')


def test_derived_values_are_not_persisted_columns(app):
    with app.app_context():
        assert not {'total_nights', 'room_charges', 'total_amount', 'paid_amount'} & set(Reservation.__table__.columns.keys())
        assert not {'subtotal'} & set(ReservationRoom.__table__.columns.keys())
        assert not {'total_price'} & set(ReservationService.__table__.columns.keys())
