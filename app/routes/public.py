from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
import re
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app, session, abort
from flask_login import current_user
from app.extensions import db
from app.models.room import Room, RoomType, Amenity
from app.models.guest import Guest
from app.models.reservation import Reservation
from app.models.setting import HotelSetting
from app.services.availability_service import get_available_rooms, get_room_availability_summary, parse_date
from app.services.reservation_service import create_reservation
from app.utils.datetime_utils import india_today, format_india_date
from app.utils.india import normalize_indian_phone

public_bp = Blueprint('public', __name__)
EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')


@public_bp.route('/')
def index():
    """Public luxury hotel homepage with live availability search and room gallery."""
    room_types = RoomType.query.all()
    amenities = Amenity.query.limit(8).all()

    # Defaults for booking search widget
    today = india_today()
    default_checkin = today + timedelta(days=1)
    default_checkout = today + timedelta(days=3)

    return render_template(
        'public/index.html',
        room_types=room_types,
        amenities=amenities,
        default_checkin=default_checkin.isoformat(),
        default_checkout=default_checkout.isoformat()
    )


@public_bp.route('/search-availability', methods=['GET', 'POST'])
def search_availability():
    """Live room search for public visitors and guests."""
    check_in_str = request.args.get('check_in') or request.form.get('check_in')
    check_out_str = request.args.get('check_out') or request.form.get('check_out')
    try:
        adults = int(request.args.get('adults') or request.form.get('adults') or 1)
        children = int(request.args.get('children') or request.form.get('children') or 0)
    except (TypeError, ValueError):
        flash('Enter valid guest counts.', 'warning')
        return redirect(url_for('public.index'))
    if adults < 1 or children < 0 or adults + children > 20:
        flash('Guest counts are outside the supported range.', 'warning')
        return redirect(url_for('public.index'))
    room_type_id = request.args.get('room_type_id') or request.form.get('room_type_id')

    if not check_in_str or not check_out_str:
        today = india_today()
        check_in = today + timedelta(days=1)
        check_out = today + timedelta(days=3)
    else:
        try:
            check_in = parse_date(check_in_str)
            check_out = parse_date(check_out_str)
        except ValueError:
            flash('Invalid date format provided.', 'danger')
            return redirect(url_for('public.index'))

    if check_out <= check_in:
        flash('Check-out date must be strictly after check-in date.', 'warning')
        return redirect(url_for('public.index'))

    rt_id = int(room_type_id) if room_type_id and room_type_id.isdigit() else None
    available_rooms = get_available_rooms(
        check_in=check_in,
        check_out=check_out,
        room_type_id=rt_id,
        min_capacity=adults + children
    )

    nights = (check_out - check_in).days
    room_types = RoomType.query.all()

    # Calculate all displayed prices with Decimal to avoid Decimal/float errors.
    tax_rate = Decimal(str(current_app.config.get('HOTEL_TAX_RATE', '0.12')))
    money_quantum = Decimal('0.01')
    room_quotes = {}
    for room in available_rooms:
        nightly_rate = Decimal(str(room.price_per_night))
        subtotal = (nightly_rate * Decimal(nights)).quantize(
            money_quantum, rounding=ROUND_HALF_UP
        )
        tax = (subtotal * tax_rate).quantize(
            money_quantum, rounding=ROUND_HALF_UP
        )
        room_quotes[room.id] = {
            'nightly_rate': nightly_rate.quantize(money_quantum, rounding=ROUND_HALF_UP),
            'subtotal': subtotal,
            'tax': tax,
            'total': subtotal + tax,
        }

    return render_template(
        'public/search_results.html',
        check_in=check_in.isoformat(),
        check_out=check_out.isoformat(),
        check_in_display=format_india_date(check_in),
        check_out_display=format_india_date(check_out),
        nights=nights,
        adults=adults,
        children=children,
        available_rooms=available_rooms,
        room_quotes=room_quotes,
        tax_percent=tax_rate * Decimal('100'),
        room_types=room_types,
        selected_room_type=rt_id,
        cancellation_policy=HotelSetting.get_val(
            'CANCELLATION_POLICY', 'Contact reception for cancellation and refund information.'
        )
    )


@public_bp.route('/book-now', methods=['POST'])
def book_now():
    """Create a reservation for an account guest or a new walk-in profile."""
    guest = None
    if current_user.is_authenticated and current_user.is_guest:
        guest = current_user.guest_profile
        first_name = guest.first_name if guest else ''
        last_name = guest.last_name if guest else ''
        email = guest.email if guest else ''
        phone = guest.phone if guest else ''
    else:
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = normalize_indian_phone(request.form.get('phone', '').strip())
    room_id = request.form.get('room_id')
    check_in_str = request.form.get('check_in')
    check_out_str = request.form.get('check_out')
    special_requests = request.form.get('special_requests', '').strip()

    missing_guest_details = not current_user.is_authenticated or not current_user.is_guest
    if (
        (missing_guest_details and (
            not first_name or len(first_name) > 60 or not last_name or len(last_name) > 60
            or not EMAIL_RE.fullmatch(email) or not phone
        ))
        or (current_user.is_authenticated and current_user.is_guest and guest is None)
        or len(special_requests) > 1000
        or not all([room_id, check_in_str, check_out_str])
    ):
        flash('Please fill in all required guest and booking information.', 'danger')
        return redirect(url_for('public.index'))

    try:
        adults = int(request.form.get('adults', 1))
        children = int(request.form.get('children', 0))
        if adults < 1 or children < 0 or adults + children > 20:
            raise ValueError('Guest counts are outside the supported range.')
        check_in = parse_date(check_in_str)
        check_out = parse_date(check_out_str)
        room_id_int = int(room_id)

        # Authenticated bookings use the account-linked profile; anonymous
        # bookings validate and create the submitted guest profile.
        if guest is None:
            existing_guest = Guest.query.filter(db.func.lower(Guest.email) == email).first()
            if existing_guest:
                flash('This email is already linked to a hotel guest profile. Sign in or contact reception to verify the profile before booking.', 'warning')
                return redirect(url_for('public.index'))
            guest = Guest(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                country='India',
            )
            db.session.add(guest)
            db.session.flush()

        # Atomic reservation creation
        reservation = create_reservation(
            guest_id=guest.id,
            room_ids=[room_id_int],
            check_in=check_in,
            check_out=check_out,
            adults_count=adults,
            children_count=children,
            special_requests=special_requests,
            created_by_id=None,  # Guest self-booking
            initial_payment_amount=None,
            ip_address=request.remote_addr
        )

        flash(f'Your reservation has been confirmed! Confirmation number: {reservation.confirmation_number}', 'success')
        if not current_user.is_authenticated:
            session['booking_confirmation'] = reservation.confirmation_number
        return redirect(url_for('public.confirmation', conf_number=reservation.confirmation_number))

    except ValueError as exc:
        flash(str(exc), 'warning')
        return redirect(url_for('public.index'))
    except Exception:
        current_app.logger.exception('Public reservation booking failed')
        flash('The reservation could not be completed. Please review the dates and try again.', 'danger')
        return redirect(url_for('public.index'))


@public_bp.route('/confirmation/<conf_number>')
def confirmation(conf_number):
    """Show a confirmation only to its guest account or the booking session."""
    reservation = Reservation.query.filter_by(confirmation_number=conf_number).first_or_404()
    is_owner = (
        current_user.is_authenticated
        and current_user.is_guest
        and current_user.guest_profile_id == reservation.guest_id
    )
    has_booking_session = session.get('booking_confirmation') == reservation.confirmation_number
    if not (is_owner or has_booking_session):
        abort(404)
    return render_template(
        'public/confirmation.html',
        reservation=reservation,
        cancellation_policy=HotelSetting.get_val('CANCELLATION_POLICY', 'Contact reception for cancellation and refund information.'),
        default_checkin_time=HotelSetting.get_val('DEFAULT_CHECKIN_TIME', '15:00'),
        default_checkout_time=HotelSetting.get_val('DEFAULT_CHECKOUT_TIME', '11:00'),
    )
