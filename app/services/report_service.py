from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List
from sqlalchemy import func, extract, and_, or_
from app.extensions import db
from app.models.room import Room, RoomType
from app.models.guest import Guest
from app.models.reservation import Reservation, ReservationRoom
from app.models.payment import Payment
from app.utils.datetime_utils import india_today, india_local_to_utc_naive


def get_dashboard_kpis() -> Dict[str, Any]:
    """Calculate executive dashboard metrics entirely from real database records."""
    today = india_today()

    total_rooms = Room.query.filter_by(is_active=True).count()
    maintenance_rooms = Room.query.filter(
        Room.is_active.is_(True),
        Room.operational_status.in_(['maintenance', 'out_of_order'])
    ).count()

    # Rooms currently occupied by checked_in guests today
    occupied_rooms_count = db.session.query(func.count(func.distinct(ReservationRoom.room_id)))\
        .join(Reservation, ReservationRoom.reservation_id == Reservation.id)\
        .filter(
            Reservation.status == 'checked_in',
            Reservation.check_in_date <= today,
            Reservation.check_out_date > today
        ).scalar() or 0

    available_rooms = max(0, total_rooms - maintenance_rooms - occupied_rooms_count)

    total_reservations = Reservation.query.count()
    confirmed_reservations = Reservation.query.filter_by(status='confirmed').count()

    # Today's arrivals and departures
    today_arrivals = Reservation.query.filter(
        Reservation.check_in_date == today,
        Reservation.status.in_(['confirmed', 'checked_in'])
    ).count()

    today_departures = Reservation.query.filter(
        Reservation.check_out_date == today,
        Reservation.status.in_(['confirmed', 'checked_in'])
    ).count()

    total_guests = Guest.query.count()

    # Current month revenue from completed payments
    month_start = india_local_to_utc_naive(datetime(today.year, today.month, 1))
    if today.month == 12:
        next_month = date(today.year + 1, 1, 1)
    else:
        next_month = date(today.year, today.month + 1, 1)
    next_month_start = india_local_to_utc_naive(datetime(next_month.year, next_month.month, 1))
    monthly_revenue = db.session.query(func.sum(Payment.amount))\
        .filter(
            Payment.payment_status == 'paid',
            Payment.created_at >= month_start,
            Payment.created_at < next_month_start
        ).scalar() or Decimal('0.00')

    # Total all-time revenue collected
    all_time_revenue = db.session.query(func.sum(Payment.amount))\
        .filter(Payment.payment_status == 'paid').scalar() or Decimal('0.00')

    # Occupancy rate calculation (operational rooms)
    operational_count = total_rooms - maintenance_rooms
    occupancy_rate = (occupied_rooms_count / operational_count * 100) if operational_count > 0 else 0.0

    return {
        'total_rooms': total_rooms,
        'available_rooms': available_rooms,
        'occupied_rooms': occupied_rooms_count,
        'maintenance_rooms': maintenance_rooms,
        'total_reservations': total_reservations,
        'confirmed_reservations': confirmed_reservations,
        'today_arrivals': today_arrivals,
        'today_departures': today_departures,
        'total_guests': total_guests,
        'monthly_revenue': float(monthly_revenue),
        'all_time_revenue': float(all_time_revenue),
        'occupancy_rate': round(occupancy_rate, 1)
    }


def get_monthly_revenue_trend(months_back: int = 6) -> Dict[str, Any]:
    """Retrieve actual monthly payment totals over the past N months."""
    today = india_today()
    labels = []
    data = []

    # Iterate back months
    for i in range(months_back - 1, -1, -1):
        # Month calculation
        year = today.year
        month = today.month - i
        while month <= 0:
            month += 12
            year -= 1

        start_dt = datetime(year, month, 1)
        if month == 12:
            end_dt = datetime(year + 1, 1, 1)
        else:
            end_dt = datetime(year, month + 1, 1)

        month_label = start_dt.strftime('%b %Y')
        start_utc = india_local_to_utc_naive(start_dt)
        end_utc = india_local_to_utc_naive(end_dt)
        total = db.session.query(func.sum(Payment.amount))\
            .filter(
                Payment.payment_status == 'paid',
                Payment.created_at >= start_utc,
                Payment.created_at < end_utc
            ).scalar() or Decimal('0.00')

        labels.append(month_label)
        data.append(float(total))

    return {'labels': labels, 'data': data}


def get_reservation_status_distribution() -> Dict[str, Any]:
    """Retrieve count breakdown of reservations by status."""
    statuses = ['confirmed', 'checked_in', 'checked_out', 'cancelled', 'pending']
    counts = []

    for s in statuses:
        c = Reservation.query.filter_by(status=s).count()
        counts.append(c)

    return {
        'labels': [s.replace('_', ' ').title() for s in statuses],
        'data': counts
    }


def get_room_type_performance() -> List[Dict[str, Any]]:
    """Performance statistics by room type."""
    results = []
    room_types = RoomType.query.all()

    for rt in room_types:
        # Count allocations
        stats = db.session.query(
            func.count(ReservationRoom.id),
            func.coalesce(func.sum(ReservationRoom.subtotal), Decimal('0.00')),
            func.coalesce(func.avg(ReservationRoom.nights), 0)
        ).join(Room, ReservationRoom.room_id == Room.id)\
         .join(Reservation, ReservationRoom.reservation_id == Reservation.id)\
         .filter(
             Room.room_type_id == rt.id,
             Reservation.status != 'cancelled'
         ).first()

        total_bookings = stats[0] or 0
        total_rev = stats[1] or Decimal('0.00')
        avg_nights = round(float(stats[2] or 0), 1)

        results.append({
            'code': rt.code,
            'name': rt.name,
            'base_price': float(rt.base_price),
            'total_bookings': total_bookings,
            'total_revenue': float(total_rev),
            'avg_stay_nights': avg_nights
        })

    return sorted(results, key=lambda x: x['total_revenue'], reverse=True)


def get_unpaid_reservations_report() -> List[Dict[str, Any]]:
    """Retrieve list of confirmed or checked-in reservations with outstanding balance."""
    reservations = Reservation.query.filter(
        Reservation.status.in_(['confirmed', 'checked_in']),
        Reservation.paid_amount < Reservation.total_amount
    ).order_by(Reservation.check_in_date.asc()).all()

    return [r.to_dict() for r in reservations]
