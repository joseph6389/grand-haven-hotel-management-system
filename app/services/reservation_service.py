import uuid
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any
from flask import current_app
from app.extensions import db
from app.models.reservation import Reservation, ReservationRoom, ReservationStatusHistory
from app.models.room import Room
from app.models.guest import Guest
from app.models.payment import Payment
from app.models.audit import AuditLog
from app.models.setting import HotelSetting
from app.services.availability_service import parse_date, is_room_available
from app.utils.datetime_utils import utcnow, india_today, india_now
import json


def generate_confirmation_number() -> str:
    """Generate a unique luxury booking confirmation code (e.g. GH-20261016-8F2A)."""
    today_str = india_today().strftime('%Y%m%d')
    suffix = uuid.uuid4().hex[:4].upper()
    return f"GH-{today_str}-{suffix}"


def calculate_pricing(
    room_ids: List[int],
    check_in: date,
    check_out: date,
    discount_amount: Decimal = Decimal('0.00')
) -> Tuple[int, Decimal, Decimal, Decimal, List[Dict[str, Any]]]:
    """
    Perform server-side price calculation. Never trust client pricing.
    Returns: (nights, room_charges, tax_amount, total_amount, room_breakdown)
    """
    check_in = parse_date(check_in)
    check_out = parse_date(check_out)

    if check_out <= check_in:
        raise ValueError("Check-out date must be after check-in date.")

    nights = (check_out - check_in).days
    if nights <= 0:
        raise ValueError("Reservation must be for at least one night.")

    # Tax rate from settings or default
    tax_rate = Decimal(str(HotelSetting.get_val('HOTEL_TAX_RATE', current_app.config.get('HOTEL_TAX_RATE', 0.12))))

    total_room_charges = Decimal('0.00')
    room_breakdown = []

    for rid in room_ids:
        room = db.session.get(Room, rid)
        if not room:
            raise ValueError(f"Room with ID {rid} does not exist.")
        rate = Decimal(str(room.price_per_night))
        subtotal = rate * Decimal(nights)
        total_room_charges += subtotal
        room_breakdown.append({
            'room': room,
            'nightly_rate': rate,
            'nights': nights,
            'subtotal': subtotal
        })

    tax_amount = (total_room_charges * tax_rate).quantize(Decimal('0.01'))
    discount = Decimal(str(discount_amount)).quantize(Decimal('0.01'))
    total_amount = max(Decimal('0.00'), (total_room_charges + tax_amount - discount).quantize(Decimal('0.01')))

    return nights, total_room_charges, tax_amount, total_amount, room_breakdown


def create_reservation(
    guest_id: int,
    room_ids: List[int],
    check_in: date,
    check_out: date,
    adults_count: int = 1,
    children_count: int = 0,
    special_requests: Optional[str] = None,
    created_by_id: Optional[int] = None,
    initial_payment_amount: Optional[Decimal] = None,
    payment_method: str = 'simulation',
    ip_address: Optional[str] = None
) -> Reservation:
    """
    Atomic transaction:
    1. Validates inputs & guest existence.
    2. Re-verifies room availability with lock.
    3. Calculates exact server charges.
    4. Creates Reservation & ReservationRoom records.
    5. Optionally records initial payment.
    6. Writes status history & audit log.
    7. Commits or rolls back atomically.
    """
    check_in = parse_date(check_in)
    check_out = parse_date(check_out)

    if check_out <= check_in:
        raise ValueError("Check-out date must be strictly after check-in date.")

    if not isinstance(adults_count, int) or adults_count < 1:
        raise ValueError("At least one adult is required.")
    if not isinstance(children_count, int) or children_count < 0:
        raise ValueError("Children count cannot be negative.")
    if initial_payment_amount is not None and Decimal(str(initial_payment_amount)) < 0:
        raise ValueError("Initial payment amount cannot be negative.")

    guest = db.session.get(Guest, guest_id)
    if not guest:
        raise ValueError("Guest profile does not exist.")

    if not room_ids:
        raise ValueError("At least one room must be selected for the reservation.")
    if len(room_ids) != len(set(room_ids)):
        raise ValueError("A room can only be selected once per reservation.")

    try:
        # Step 1: Lock selected room rows in a consistent order before checking
        # availability. MySQL/InnoDB holds these locks until commit/rollback, so
        # concurrent bookings for the same room serialize before the overlap check.
        total_capacity = 0
        locked_rooms = {}
        for rid in sorted(room_ids):
            room = db.session.execute(
                db.select(Room).where(Room.id == rid).with_for_update().execution_options(populate_existing=True)
            ).scalar_one_or_none()
            locked_rooms[rid] = room

        for rid in room_ids:
            room = locked_rooms[rid]
            if not room:
                raise ValueError(f"Room ID {rid} not found.")
            if not room.is_operational:
                raise ValueError(f"Room {room.room_number} is currently {room.operational_status} and unavailable.")
            if not is_room_available(rid, check_in, check_out, lock_conflicts=True):
                raise ValueError(f"Room {room.room_number} has just been booked by another guest for these dates.")
            total_capacity += room.capacity

        if (adults_count + children_count) > total_capacity:
            raise ValueError(f"Selected rooms have capacity for {total_capacity} guests, but {adults_count + children_count} were requested.")

        # Step 2: Price calculations
        nights, room_charges, tax_amount, total_amount, breakdown = calculate_pricing(
            room_ids, check_in, check_out
        )

        # Step 3: Instantiate Reservation
        confirmation_num = generate_confirmation_number()
        reservation = Reservation(
            confirmation_number=confirmation_num,
            guest_id=guest_id,
            check_in_date=check_in,
            check_out_date=check_out,
            adults_count=adults_count,
            children_count=children_count,
            tax_amount=tax_amount,
            discount_amount=Decimal('0.00'),
            status='confirmed',
            special_requests=special_requests,
            created_by_id=created_by_id
        )
        db.session.add(reservation)
        db.session.flush()  # Generates reservation.id

        # Step 4: Add room allocations
        for item in breakdown:
            alloc = ReservationRoom(
                reservation_id=reservation.id,
                room_id=item['room'].id,
                nightly_rate=item['nightly_rate'],
                nights=item['nights'],
            )
            db.session.add(alloc)

        # Step 5: Initial Status History
        history = ReservationStatusHistory(
            reservation_id=reservation.id,
            previous_status=None,
            new_status='confirmed',
            changed_by_id=created_by_id,
            reason="Initial reservation booking"
        )
        db.session.add(history)

        # Step 6: Initial Payment (if provided)
        if initial_payment_amount and initial_payment_amount > 0:
            pay_amt = min(Decimal(str(initial_payment_amount)), total_amount)
            payment = Payment(
                reservation_id=reservation.id,
                payment_reference=f"PAY-{confirmation_num.replace('GH-', '')}-1",
                amount=pay_amt,
                currency=current_app.config.get('HOTEL_CURRENCY', 'INR'),
                payment_method=payment_method,
                payment_status='paid',
                transaction_reference=f"SIM-TXN-{uuid.uuid4().hex[:8].upper()}",
                notes="Initial booking payment",
                processed_by_id=created_by_id
            )
            db.session.add(payment)

        # Step 7: System Audit Log
        audit = AuditLog(
            user_id=created_by_id,
            action='CREATE_RESERVATION',
            entity_type='Reservation',
            entity_id=str(reservation.id),
            details=f"Created booking {confirmation_num} for guest {guest.full_name}. Rooms: {[b['room'].room_number for b in breakdown]}. Total: ₹{total_amount}",
            ip_address=ip_address
        )
        db.session.add(audit)

        # Commit all changes atomically
        db.session.commit()
        return reservation

    except Exception as exc:
        db.session.rollback()
        raise exc


def edit_reservation(
    reservation_id: int,
    room_ids: List[int],
    check_in: date,
    check_out: date,
    adults_count: int,
    children_count: int = 0,
    changed_by_id: Optional[int] = None,
    ip_address: Optional[str] = None,
) -> Reservation:
    """Update a future reservation without changing its guest or payment ledger."""
    check_in = parse_date(check_in)
    check_out = parse_date(check_out)
    if check_out <= check_in:
        raise ValueError("Check-out date must be strictly after check-in date.")
    if not isinstance(adults_count, int) or adults_count < 1:
        raise ValueError("At least one adult is required.")
    if not isinstance(children_count, int) or children_count < 0:
        raise ValueError("Children count cannot be negative.")
    if not room_ids:
        raise ValueError("At least one room must be selected for the reservation.")
    if len(room_ids) != len(set(room_ids)):
        raise ValueError("A room can only be selected once per reservation.")

    try:
        reservation = db.session.execute(
            db.select(Reservation)
            .where(Reservation.id == reservation_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        ).unique().scalar_one_or_none()
        if not reservation:
            raise ValueError("Reservation not found.")
        if reservation.status not in ('pending', 'confirmed'):
            raise ValueError("Only pending or confirmed reservations can be edited.")
        if not db.session.get(Guest, reservation.guest_id):
            raise ValueError("The reservation guest profile could not be found.")

        locked_rooms = {}
        for room_id in sorted(room_ids):
            locked_rooms[room_id] = db.session.execute(
                db.select(Room).where(Room.id == room_id).with_for_update()
            ).scalar_one_or_none()

        capacity = 0
        for room_id in room_ids:
            room = locked_rooms[room_id]
            if not room:
                raise ValueError(f"Room ID {room_id} not found.")
            if not room.is_operational:
                raise ValueError(f"Room {room.room_number} is currently {room.operational_status} and unavailable.")
            if not is_room_available(
                room_id, check_in, check_out,
                exclude_reservation_id=reservation.id,
                lock_conflicts=True,
            ):
                raise ValueError(f"Room {room.room_number} has been booked by another guest for these dates.")
            capacity += room.capacity

        guest_count = adults_count + children_count
        if guest_count > capacity:
            raise ValueError(f"Selected rooms have capacity for {capacity} guests, but {guest_count} were requested.")

        nights, room_charges, tax_amount, total_amount, breakdown = calculate_pricing(
            room_ids, check_in, check_out
        )
        paid_amount = Decimal(str(reservation.paid_amount or '0.00'))
        if total_amount < paid_amount:
            raise ValueError("The revised total cannot be less than payments already recorded.")

        old_values = {
            'check_in': reservation.check_in_date.isoformat(),
            'check_out': reservation.check_out_date.isoformat(),
            'adults': reservation.adults_count,
            'children': reservation.children_count,
            'room_ids': sorted(room.room_id for room in reservation.room_allocations),
        }
        allocations_by_room = {allocation.room_id: allocation for allocation in reservation.room_allocations}
        selected_ids = set(room_ids)
        for room_id, allocation in allocations_by_room.items():
            if room_id not in selected_ids:
                db.session.delete(allocation)

        for item in breakdown:
            allocation = allocations_by_room.get(item['room'].id)
            if allocation is None:
                allocation = ReservationRoom(reservation_id=reservation.id, room_id=item['room'].id)
                db.session.add(allocation)
            allocation.nightly_rate = item['nightly_rate']
            allocation.nights = item['nights']

        reservation.check_in_date = check_in
        reservation.check_out_date = check_out
        reservation.adults_count = adults_count
        reservation.children_count = children_count
        reservation.tax_amount = tax_amount
        reservation.updated_at = utcnow()

        db.session.add(AuditLog(
            user_id=changed_by_id,
            action='UPDATE_RESERVATION',
            entity_type='Reservation',
            entity_id=str(reservation.id),
            details=json.dumps({
                'previous': old_values,
                'updated': {
                    'check_in': check_in.isoformat(),
                    'check_out': check_out.isoformat(),
                    'adults': adults_count,
                    'children': children_count,
                    'room_ids': sorted(selected_ids),
                    'total_amount': str(total_amount),
                },
            }, separators=(',', ':')),
            ip_address=ip_address,
        ))
        db.session.commit()
        return reservation
    except Exception:
        db.session.rollback()
        raise


def update_reservation_status(
    reservation_id: int,
    new_status: str,
    changed_by_id: Optional[int] = None,
    reason: Optional[str] = None,
    ip_address: Optional[str] = None
) -> Reservation:
    """Safely transitions a reservation through its allowed lifecycle states."""
    reservation = db.session.execute(
        db.select(Reservation)
        .where(Reservation.id == reservation_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    ).unique().scalar_one_or_none()
    if not reservation:
        raise ValueError("Reservation not found.")

    if not reservation.can_transition_to(new_status):
        raise ValueError(
            f"Cannot transition reservation status from '{reservation.status}' to '{new_status}'. "
            f"Allowed transitions: {reservation.ALLOWED_TRANSITIONS.get(reservation.status, [])}"
        )

    try:
        prev_status = reservation.status
        reservation.status = new_status
        reservation.updated_at = utcnow()

        history = ReservationStatusHistory(
            reservation_id=reservation.id,
            previous_status=prev_status,
            new_status=new_status,
            changed_by_id=changed_by_id,
            reason=reason or f"Status transitioned to {new_status}"
        )
        db.session.add(history)

        audit = AuditLog(
            user_id=changed_by_id,
            action=f"TRANSITION_{new_status.upper()}",
            entity_type='Reservation',
            entity_id=str(reservation.id),
            details=f"Reservation {reservation.confirmation_number} changed from {prev_status} to {new_status}. Reason: {reason}",
            ip_address=ip_address
        )
        db.session.add(audit)

        db.session.commit()
        return reservation
    except Exception as exc:
        db.session.rollback()
        raise exc


def cancel_reservation(
    reservation_id: int,
    *,
    request_source: str,
    requested_by_guest_id: int,
    reason: str,
    processed_by_user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
) -> Reservation:
    """Cancel through one locked transaction and retain requester/processor attribution."""
    if request_source not in ('guest_account', 'phone'):
        raise ValueError('Unsupported cancellation request source.')
    if not reason or not reason.strip() or len(reason.strip()) > 255:
        raise ValueError('Please provide a cancellation reason of at most 255 characters.')
    if request_source == 'guest_account' and processed_by_user_id is not None:
        raise ValueError('Guest self-service cancellation cannot be processed as staff.')
    if request_source == 'phone' and processed_by_user_id is None:
        raise ValueError('A receptionist account is required to process a phone request.')

    reservation = db.session.execute(
        db.select(Reservation).where(Reservation.id == reservation_id).with_for_update().execution_options(populate_existing=True)
    ).unique().scalar_one_or_none()
    if not reservation:
        raise ValueError('Reservation not found.')
    if reservation.guest_id != requested_by_guest_id:
        db.session.rollback()
        raise ValueError('The verified guest does not match this reservation.')
    if processed_by_user_id is not None:
        from app.models.user import User
        processor = db.session.get(User, processed_by_user_id)
        if not processor or not processor.is_receptionist:
            db.session.rollback()
            raise ValueError('Only authorized hotel staff may process a phone cancellation.')
    if not reservation.can_transition_to('cancelled'):
        db.session.rollback()
        raise ValueError(f"Reservation cannot be cancelled from status '{reservation.status}'.")

    previous_status = reservation.status
    paid_amount = max(Decimal('0.00'), Decimal(str(reservation.paid_amount or '0.00'))).quantize(Decimal('0.01'))

    now_local = india_now()
    configured_checkin_time = HotelSetting.get_val(
        'DEFAULT_CHECKIN_TIME', current_app.config.get('DEFAULT_CHECKIN_TIME', '15:00')
    )
    try:
        checkin_time = time.fromisoformat(str(configured_checkin_time))
    except (TypeError, ValueError) as exc:
        db.session.rollback()
        raise ValueError('The configured hotel check-in time is invalid; cancellation was not completed.') from exc
    checkin_boundary = datetime.combine(reservation.check_in_date, checkin_time, tzinfo=now_local.tzinfo)
    time_until_checkin = checkin_boundary - now_local
    if time_until_checkin < timedelta(0):
        db.session.rollback()
        raise ValueError('The configured check-in time has passed; this reservation cannot be cancelled.')

    cancellation_fee = min(Decimal('500.00'), paid_amount) if time_until_checkin <= timedelta(hours=48) else None
    potential_refund = max(Decimal('0.00'), paid_amount - cancellation_fee) if cancellation_fee is not None else None
    refund_status = (
        'pending_review'
        if paid_amount > 0 and (potential_refund is None or potential_refund > 0)
        else 'not_applicable'
    )
    try:
        reservation.status = 'cancelled'
        reservation.updated_at = utcnow()
        history = ReservationStatusHistory(
            reservation_id=reservation.id,
            previous_status=previous_status,
            new_status='cancelled',
            changed_by_id=processed_by_user_id,
            requested_by_guest_id=requested_by_guest_id,
            request_source=request_source,
            cancellation_fee=cancellation_fee,
            refund_status=refund_status,
            reason=reason.strip(),
        )
        db.session.add(history)
        db.session.add(AuditLog(
            user_id=processed_by_user_id,
            action='GUEST_SELF_CANCEL' if request_source == 'guest_account' else 'PHONE_CANCELLATION',
            entity_type='Reservation',
            entity_id=str(reservation.id),
            details=json.dumps({
                'previous_status': previous_status,
                'resulting_status': 'cancelled',
                'request_source': request_source,
                'requested_by_guest_id': requested_by_guest_id,
                'processed_by_user_id': processed_by_user_id,
                'reason': reason.strip(),
                'cancellation_fee': str(cancellation_fee) if cancellation_fee is not None else None,
                'paid_amount_at_cancellation': str(paid_amount),
                'potential_refund_amount': str(potential_refund) if potential_refund is not None else None,
                'refund_status': refund_status,
            }, separators=(',', ':')),
            ip_address=ip_address,
        ))
        db.session.commit()
        return reservation
    except Exception:
        db.session.rollback()
        raise
