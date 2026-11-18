from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import and_, or_
from app.extensions import db
from app.models.room import Room, RoomType
from app.models.reservation import Reservation, ReservationRoom


def parse_date(d) -> date:
    """Parse date from date object or YYYY-MM-DD string."""
    if isinstance(d, datetime):
        return d.date()
    elif isinstance(d, date):
        return d
    elif isinstance(d, str):
        return datetime.strptime(d.strip(), '%Y-%m-%d').date()
    raise ValueError(f"Invalid date format: {d}")


def is_room_available(
    room_id: int,
    check_in: date,
    check_out: date,
    exclude_reservation_id: Optional[int] = None,
    lock_conflicts: bool = False,
) -> bool:
    """
    Verify if a specific room is available for the given date range.
    Overlapping condition:
    Two reservations overlap if: res.check_in < req_out AND res.check_out > req_in.
    """
    check_in = parse_date(check_in)
    check_out = parse_date(check_out)

    if check_out <= check_in:
        return False

    room = db.session.get(Room, room_id)
    if not room or not room.is_operational:
        return False

    # Query conflicting reservations
    query = db.session.query(ReservationRoom.id)\
        .join(Reservation, ReservationRoom.reservation_id == Reservation.id)\
        .filter(
            ReservationRoom.room_id == room_id,
            Reservation.status.in_(['confirmed', 'checked_in']),
            Reservation.check_in_date < check_out,
            Reservation.check_out_date > check_in
        )

    if exclude_reservation_id:
        query = query.filter(Reservation.id != exclude_reservation_id)

    if lock_conflicts:
        # A locking read sees the latest committed MySQL rows even when the
        # transaction began earlier under InnoDB REPEATABLE READ.
        query = query.with_for_update()

    conflict = query.first()
    return conflict is None


def get_available_rooms(
    check_in: date,
    check_out: date,
    room_type_id: Optional[int] = None,
    min_capacity: Optional[int] = None,
    floor: Optional[int] = None
) -> List[Room]:
    """
    Retrieve all operational rooms that have no overlapping active reservations for the date range.
    """
    check_in = parse_date(check_in)
    check_out = parse_date(check_out)

    if check_out <= check_in:
        return []

    # Subquery for rooms with conflicting bookings
    conflicting_room_ids = db.session.query(ReservationRoom.room_id)\
        .join(Reservation, ReservationRoom.reservation_id == Reservation.id)\
        .filter(
            Reservation.status.in_(['confirmed', 'checked_in']),
            Reservation.check_in_date < check_out,
            Reservation.check_out_date > check_in
        ).subquery()

    # Query operational rooms that are NOT in the conflicting subquery
    query = Room.query.filter(
        Room.is_active.is_(True),
        Room.operational_status == 'operational',
        ~Room.id.in_(db.select(conflicting_room_ids.c.room_id))
    )

    if room_type_id:
        query = query.filter(Room.room_type_id == room_type_id)
    if min_capacity:
        query = query.filter(Room.capacity >= min_capacity)
    if floor:
        query = query.filter(Room.floor == floor)

    return query.order_by(Room.room_number.asc()).all()


def get_room_availability_summary(check_in: date, check_out: date) -> dict:
    """
    Provides a high-level summary of availability categorized by RoomType.
    """
    check_in = parse_date(check_in)
    check_out = parse_date(check_out)

    available_rooms = get_available_rooms(check_in, check_out)
    all_room_types = RoomType.query.all()

    summary = []
    for rt in all_room_types:
        rooms_of_type = [r for r in available_rooms if r.room_type_id == rt.id]
        total_rooms_of_type = Room.query.filter_by(room_type_id=rt.id, is_active=True).count()
        summary.append({
            'room_type': rt.to_dict(),
            'available_count': len(rooms_of_type),
            'total_count': total_rooms_of_type,
            'is_sold_out': len(rooms_of_type) == 0,
            'rooms': [r.to_dict() for r in rooms_of_type]
        })

    return {
        'check_in': check_in.isoformat(),
        'check_out': check_out.isoformat(),
        'total_available_rooms': len(available_rooms),
        'categories': summary
    }
