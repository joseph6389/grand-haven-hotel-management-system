from datetime import timedelta
from decimal import Decimal
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from app.extensions import db
from app.models.reservation import Reservation, ReservationRoom
from app.models.room import Room, RoomType
from app.models.guest import Guest
from app.models.payment import Payment
from app.services.availability_service import get_available_rooms, parse_date
from app.services.reservation_service import (
    create_reservation,
    edit_reservation,
    cancel_reservation,
    update_reservation_status,
    calculate_pricing
)
from app.routes.auth_helpers import role_required
from app.utils.india import normalize_indian_phone
from app.utils.datetime_utils import india_today

reservations_bp = Blueprint('reservations', __name__, url_prefix='/reservations')


def _parse_guest_count(value, label, minimum):
    raw = '' if value is None else str(value).strip()
    if not raw:
        raise ValueError(f'{label} is required.')
    try:
        count = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f'{label} must be a whole number.') from exc
    if count < minimum:
        if label == 'Adults':
            raise ValueError('At least one adult is required.')
        raise ValueError('Children count cannot be negative.')
    return count


@reservations_bp.route('/')
@login_required
@role_required('Admin', 'Receptionist')
def index():
    """List hotel reservations with status, search, and date filters."""
    status = request.args.get('status', '').strip()
    search = request.args.get('search', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()

    query = Reservation.query

    if status:
        query = query.filter(Reservation.status == status)

    if search:
        query = query.join(Guest).filter(
            (Reservation.confirmation_number.ilike(f'%{search}%')) |
            (Guest.first_name.ilike(f'%{search}%')) |
            (Guest.last_name.ilike(f'%{search}%')) |
            (Guest.email.ilike(f'%{search}%'))
        )

    if date_from:
        try:
            d_from = parse_date(date_from)
            query = query.filter(Reservation.check_in_date >= d_from)
        except ValueError:
            pass

    if date_to:
        try:
            d_to = parse_date(date_to)
            query = query.filter(Reservation.check_out_date <= d_to)
        except ValueError:
            pass

    reservations = query.order_by(Reservation.created_at.desc()).all()

    # Pre-calculated status summary counts for filter pills
    status_counts = {
        'all': Reservation.query.count(),
        'confirmed': Reservation.query.filter_by(status='confirmed').count(),
        'checked_in': Reservation.query.filter_by(status='checked_in').count(),
        'checked_out': Reservation.query.filter_by(status='checked_out').count(),
        'cancelled': Reservation.query.filter_by(status='cancelled').count(),
    }

    return render_template(
        'reservations/index.html',
        reservations=reservations,
        selected_status=status,
        search_query=search,
        date_from=date_from,
        date_to=date_to,
        status_counts=status_counts
    )


@reservations_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Receptionist')
def create():
    """Step-by-step reservation creation wizard for front-desk staff."""
    today = india_today()
    default_checkin = today + timedelta(days=1)
    default_checkout = today + timedelta(days=3)

    if request.method == 'POST':
        guest_option = request.form.get('guest_option')  # 'existing' or 'new'
        check_in_str = request.form.get('check_in')
        check_out_str = request.form.get('check_out')
        room_ids = request.form.getlist('room_ids', type=int)
        adults_raw = request.form.get('adults', '1')
        children_raw = request.form.get('children', '0')
        special_requests = request.form.get('special_requests', '').strip()
        initial_payment = request.form.get('initial_payment', type=float)
        payment_method = request.form.get('payment_method', 'simulation')

        try:
            adults = _parse_guest_count(adults_raw, 'Adults', 1)
            children = _parse_guest_count(children_raw, 'Children', 0)
            check_in = parse_date(check_in_str)
            check_out = parse_date(check_out_str)

            # Resolve guest
            if guest_option == 'existing':
                guest_id = request.form.get('guest_id', type=int)
                guest = db.session.get(Guest, guest_id)
                if not guest:
                    flash('Selected guest could not be found.', 'danger')
                    return redirect(url_for('reservations.create'))
            else:
                first_name = request.form.get('first_name', '').strip()
                last_name = request.form.get('last_name', '').strip()
                email = request.form.get('email', '').strip().lower()
                phone = request.form.get('phone', '').strip()

                if not first_name or not last_name or not email or not phone:
                    flash('Please complete all required new guest fields.', 'warning')
                    return redirect(url_for('reservations.create'))

                # Check if email exists
                guest = Guest.query.filter_by(email=email).first()
                if not guest:
                    guest = Guest(
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        phone=phone
                    )
                    db.session.add(guest)
                    db.session.flush()

            # Execute transactional booking
            init_pay_dec = Decimal(str(initial_payment)) if initial_payment and initial_payment > 0 else None
            reservation = create_reservation(
                guest_id=guest.id,
                room_ids=room_ids,
                check_in=check_in,
                check_out=check_out,
                adults_count=adults,
                children_count=children,
                special_requests=special_requests,
                created_by_id=current_user.id,
                initial_payment_amount=init_pay_dec,
                payment_method=payment_method,
                ip_address=request.remote_addr
            )

            flash(f'Reservation {reservation.confirmation_number} created successfully!', 'success')
            return redirect(url_for('reservations.detail', reservation_id=reservation.id))

        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), 'warning')
        except Exception:
            db.session.rollback()
            current_app.logger.exception('Staff reservation booking failed')
            flash('Reservation could not be completed. Please review the details and try again.', 'danger')

    guests = Guest.query.order_by(Guest.first_name.asc()).all()
    room_types = RoomType.query.all()

    return render_template(
        'reservations/create.html',
        guests=guests,
        room_types=room_types,
        default_checkin=default_checkin.isoformat(),
        default_checkout=default_checkout.isoformat()
    )


@reservations_bp.route('/<int:reservation_id>')
@login_required
@role_required('Admin', 'Receptionist')
def detail(reservation_id):
    """View full reservation folio, room allocations, payment history, and audit log."""
    reservation = db.get_or_404(Reservation, reservation_id)
    payments = reservation.payments.order_by(Payment.created_at.desc()).all()
    status_history = reservation.status_history

    return render_template(
        'reservations/detail.html',
        reservation=reservation,
        payments=payments,
        status_history=status_history
    )


@reservations_bp.route('/<int:reservation_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Receptionist')
def edit(reservation_id):
    """Edit a future reservation while preserving its guest and payment ledger."""
    reservation = db.get_or_404(Reservation, reservation_id)
    if reservation.status not in ('pending', 'confirmed'):
        flash('Only pending or confirmed reservations can be edited.', 'warning')
        return redirect(url_for('reservations.detail', reservation_id=reservation.id))

    form_values = {
        'check_in': reservation.check_in_date.isoformat(),
        'check_out': reservation.check_out_date.isoformat(),
        'adults': str(reservation.adults_count),
        'children': str(reservation.children_count),
    }
    selected_room_ids = {allocation.room_id for allocation in reservation.room_allocations}
    error_message = None

    if request.method == 'POST':
        form_values = {
            'check_in': request.form.get('check_in', '').strip(),
            'check_out': request.form.get('check_out', '').strip(),
            'adults': request.form.get('adults', ''),
            'children': request.form.get('children', ''),
        }
        selected_room_ids = set(request.form.getlist('room_ids', type=int))
        try:
            adults = _parse_guest_count(form_values['adults'], 'Adults', 1)
            children = _parse_guest_count(form_values['children'], 'Children', 0)
            result = edit_reservation(
                reservation_id=reservation.id,
                room_ids=sorted(selected_room_ids),
                check_in=parse_date(form_values['check_in']),
                check_out=parse_date(form_values['check_out']),
                adults_count=adults,
                children_count=children,
                changed_by_id=current_user.id,
                ip_address=request.remote_addr,
            )
            flash(f'Reservation {result.confirmation_number} updated successfully.', 'success')
            return redirect(url_for('reservations.detail', reservation_id=result.id))
        except ValueError as exc:
            db.session.rollback()
            error_message = str(exc)
        except Exception:
            db.session.rollback()
            current_app.logger.exception('Reservation edit failed for %s', reservation.id)
            error_message = 'Reservation could not be updated. Please review the details and try again.'

    try:
        query_check_in = parse_date(form_values['check_in'])
        query_check_out = parse_date(form_values['check_out'])
        if query_check_out <= query_check_in:
            raise ValueError('Invalid stay range.')
    except ValueError:
        query_check_in = reservation.check_in_date
        query_check_out = reservation.check_out_date

    room_map = {room.id: room for room in get_available_rooms(query_check_in, query_check_out)}
    room_map.update({room.id: room for room in reservation.assigned_rooms})
    rooms = sorted(room_map.values(), key=lambda room: room.room_number)
    return render_template(
        'reservations/edit.html',
        reservation=reservation,
        rooms=rooms,
        form_values=form_values,
        selected_room_ids=selected_room_ids,
        error_message=error_message,
    )


@reservations_bp.route('/<int:reservation_id>/check-in', methods=['POST'])
@login_required
@role_required('Admin', 'Receptionist')
def check_in(reservation_id):
    """Check in guest upon arrival at hotel."""
    try:
        reservation = update_reservation_status(
            reservation_id=reservation_id,
            new_status='checked_in',
            changed_by_id=current_user.id,
            reason="Guest checked in at front desk.",
            ip_address=request.remote_addr
        )
        flash(f'Guest checked in successfully for reservation {reservation.confirmation_number}.', 'success')
    except ValueError as exc:
        flash(str(exc), 'warning')
    except Exception:
        current_app.logger.exception('Check-in failed for reservation %s', reservation_id)
        flash('Check-in could not be completed. Please retry or contact an administrator.', 'danger')

    return redirect(url_for('reservations.detail', reservation_id=reservation_id))


@reservations_bp.route('/<int:reservation_id>/check-out', methods=['POST'])
@login_required
@role_required('Admin', 'Receptionist')
def check_out(reservation_id):
    """Check out guest at departure and settle billing."""
    reservation = db.get_or_404(Reservation, reservation_id)
    if reservation.outstanding_balance > Decimal('0.00'):
        flash(
            f'Warning: Reservation has an outstanding balance of ₹{reservation.outstanding_balance}. '
            'Please settle payment before final departure.',
            'warning'
        )

    try:
        reservation = update_reservation_status(
            reservation_id=reservation_id,
            new_status='checked_out',
            changed_by_id=current_user.id,
            reason="Guest checked out at front desk.",
            ip_address=request.remote_addr
        )
        flash(f'Guest checked out successfully for reservation {reservation.confirmation_number}.', 'success')
    except ValueError as exc:
        flash(str(exc), 'warning')
    except Exception:
        current_app.logger.exception('Check-out failed for reservation %s', reservation_id)
        flash('Check-out could not be completed. Please retry or contact an administrator.', 'danger')

    return redirect(url_for('reservations.detail', reservation_id=reservation_id))


@reservations_bp.route('/<int:reservation_id>/cancel', methods=['POST'])
@login_required
@role_required('Admin', 'Receptionist')
def cancel(reservation_id):
    """Cancel a phone request after checking multiple guest details."""
    reservation = db.get_or_404(Reservation, reservation_id)
    confirmation = request.form.get('confirmation_number', '').strip().upper()
    guest_name = request.form.get('verified_guest_name', '').strip()
    guest_email = request.form.get('verified_guest_email', '').strip().lower()
    guest_phone = normalize_indian_phone(request.form.get('verified_guest_phone', ''))
    stored_phone = normalize_indian_phone(reservation.guest.phone)
    reason = request.form.get('reason', '').strip()
    if (
        confirmation != reservation.confirmation_number
        or guest_name.casefold() != reservation.guest.full_name.casefold()
        or guest_email != reservation.guest.email.casefold()
        or not guest_phone or guest_phone != stored_phone
    ):
        flash('Cancellation not completed. Guest details did not match; verify the caller.', 'warning')
        return redirect(url_for('reservations.detail', reservation_id=reservation_id))
    try:
        reservation = cancel_reservation(
            reservation.id,
            request_source='phone',
            requested_by_guest_id=reservation.guest_id,
            processed_by_user_id=current_user.id,
            reason=reason,
            ip_address=request.remote_addr
        )
        flash(f'Reservation {reservation.confirmation_number} cancelled. The fee and refund-review status are recorded in the folio; no external payout is confirmed.', 'info')
    except ValueError as exc:
        flash(f'Cancellation not completed: {exc}', 'warning')
    except Exception:
        current_app.logger.exception('Phone cancellation failed for reservation %s', reservation_id)
        flash('Cancellation could not be completed. Please retry or contact an administrator.', 'danger')

    return redirect(url_for('reservations.detail', reservation_id=reservation_id))


@reservations_bp.route('/<int:reservation_id>/voucher')
@login_required
@role_required('Admin', 'Receptionist')
def voucher(reservation_id):
    """Luxury print-ready booking confirmation voucher."""
    reservation = db.get_or_404(Reservation, reservation_id)
    from app.models.setting import HotelSetting
    return render_template(
        'reservations/voucher.html',
        reservation=reservation,
        cancellation_policy=HotelSetting.get_val('CANCELLATION_POLICY', 'Contact reception for cancellation and refund information.'),
        default_checkin_time=HotelSetting.get_val('DEFAULT_CHECKIN_TIME', '15:00'),
        default_checkout_time=HotelSetting.get_val('DEFAULT_CHECKOUT_TIME', '11:00'),
    )
