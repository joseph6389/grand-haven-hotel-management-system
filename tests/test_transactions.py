from datetime import timedelta
from decimal import Decimal
import pytest
from app.extensions import db
from app.models.guest import Guest
from app.models.room import Room
from app.models.reservation import Reservation
from app.services.reservation_service import create_reservation
from app.utils.datetime_utils import india_today


def test_transaction_rollback_on_failed_booking(app):
    """
    Test that if an error occurs during reservation creation,
    all changes are rolled back atomically and no partial records remain.
    """
    with app.app_context():
        today = india_today()
        guest = Guest.query.first()
        initial_reservation_count = Reservation.query.count()

        # Attempt to create reservation with invalid date range (checkout < checkin)
        with pytest.raises(ValueError):
            create_reservation(
                guest_id=guest.id,
                room_ids=[1],
                check_in=today + timedelta(days=10),
                check_out=today + timedelta(days=5),  # INVALID
                adults_count=2
            )

        # Verify no orphan or partial reservation was committed
        assert Reservation.query.count() == initial_reservation_count


def test_database_integrity_unique_email(app):
    """Test that the database enforces unique email constraints on guests."""
    with app.app_context():
        g1 = Guest(
            first_name='Unique',
            last_name='One',
            email='integrity_unique@test.com',
            phone='+91 9876543210'
        )
        db.session.add(g1)
        db.session.commit()

        g2 = Guest(
            first_name='Unique',
            last_name='Two',
            email='integrity_unique@test.com',  # Duplicate email
            phone='+91 9876543211'
        )
        db.session.add(g2)
        with pytest.raises(Exception):
            db.session.commit()
        db.session.rollback()
