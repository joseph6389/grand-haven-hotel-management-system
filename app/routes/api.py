from datetime import date
from decimal import Decimal
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.room import Room, RoomType
from app.models.guest import Guest
from app.models.reservation import Reservation
from app.models.payment import Payment
from app.services.availability_service import get_available_rooms, parse_date
from app.services.reservation_service import (
    create_reservation,
    cancel_reservation,
    update_reservation_status,
    calculate_pricing
)
from app.services.payment_service import process_payment
from app.services.report_service import (
    get_dashboard_kpis,
    get_monthly_revenue_trend,
    get_reservation_status_distribution,
    get_room_type_performance
)
from app.routes.auth_helpers import role_required
from app.utils.india import normalize_indian_phone
from app.models.audit import AuditLog
from app.utils.datetime_utils import format_india_datetime

api_bp = Blueprint('api', __name__, url_prefix='/api')

EVENT_LABELS = {
    'CREATE_RESERVATION': 'Reservation created',
    'GUEST_SELF_CANCEL': 'Guest cancelled a reservation',
    'PHONE_CANCELLATION': 'Reception processed a phone cancellation',
    'TRANSITION_CHECKED_IN': 'Guest checked in',
    'TRANSITION_CHECKED_OUT': 'Guest checked out',
    'RECORD_PAYMENT': 'Payment recorded',
    'PROCESS_REFUND': 'Refund processed',
    'GUEST_REGISTER': 'Guest account registered',
    'GUEST_PROFILE_UPDATE': 'Guest profile updated',
    'GUEST_LOGOUT': 'Guest signed out',
    'CREATE_GUEST': 'Guest record created',
    'UPDATE_GUEST': 'Guest record updated',
    'CREATE_USER': 'Staff account created',
    'TOGGLE_USER_STATUS': 'Staff access changed',
    'UPDATE_SETTINGS': 'Hotel settings changed',
    'CREATE_ROOM': 'Room added to inventory',
    'UPDATE_ROOM': 'Room information changed',
    'ROOM_STATUS_CHANGE': 'Room status changed',
}


@api_bp.route('/admin/events')
@login_required
@role_required('Admin')
def admin_events():
    """Return a PII-minimized, admin-only audit cursor for dashboard polling."""
    after_id = max(0, request.args.get('after', default=0, type=int))
    logs = AuditLog.query.filter(AuditLog.id > after_id).order_by(AuditLog.id.asc()).limit(50).all()
    return jsonify({
        'events': [{
            'id': item.id,
            'label': EVENT_LABELS.get(item.action, 'Hotel activity recorded'),
            'timestamp': format_india_datetime(item.timestamp),
        } for item in logs],
        'cursor': logs[-1].id if logs else after_id,
    })


@api_bp.route('/staff/events')
@login_required
@role_required('Admin', 'Receptionist')
def staff_events():
    """Return safe hotel-operation events for authorized staff dashboards."""
    after_id = max(0, request.args.get('after', default=0, type=int))
    logs = AuditLog.query.filter(AuditLog.id > after_id).order_by(AuditLog.id.asc()).limit(50).all()
    return jsonify({
        'events': [{
            'id': item.id,
            'label': EVENT_LABELS.get(item.action, 'Hotel activity recorded'),
            'timestamp': format_india_datetime(item.timestamp),
        } for item in logs],
        'cursor': logs[-1].id if logs else after_id,
    })

@api_bp.route('/available-rooms')
def available_rooms():
    """Live room availability query."""
    check_in_str = request.args.get('check_in')
    check_out_str = request.args.get('check_out')
    room_type_id = request.args.get('room_type_id', type=int)
    capacity = request.args.get('capacity', type=int)

    if not check_in_str or not check_out_str:
        return jsonify({'error': 'check_in and check_out are required'}), 400

    try:
        check_in = parse_date(check_in_str)
        check_out = parse_date(check_out_str)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    if check_out <= check_in:
        return jsonify({'error': 'check_out must be after check_in'}), 400

    rooms = get_available_rooms(
        check_in=check_in,
        check_out=check_out,
        room_type_id=room_type_id,
        min_capacity=capacity
    )

    nights = (check_out - check_in).days
    return jsonify({
        'check_in': check_in.isoformat(),
        'check_out': check_out.isoformat(),
        'nights': nights,
        'count': len(rooms),
        'rooms': [r.to_dict() for r in rooms]
    })


@api_bp.route('/pricing-quote')
def pricing_quote():
    """Server-side price quote calculations for selected rooms and dates."""
    check_in_str = request.args.get('check_in')
    check_out_str = request.args.get('check_out')
    room_ids = request.args.getlist('room_ids', type=int)

    if not check_in_str or not check_out_str or not room_ids:
        return jsonify({'error': 'check_in, check_out, and room_ids are required'}), 400

    try:
        check_in = parse_date(check_in_str)
        check_out = parse_date(check_out_str)
        nights, room_charges, tax, total, breakdown = calculate_pricing(room_ids, check_in, check_out)

        return jsonify({
            'nights': nights,
            'room_charges': float(room_charges),
            'tax_amount': float(tax),
            'total_amount': float(total),
            'rooms': [
                {
                    'room_id': b['room'].id,
                    'room_number': b['room'].room_number,
                    'nightly_rate': float(b['nightly_rate']),
                    'subtotal': float(b['subtotal'])
                }
                for b in breakdown
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@api_bp.route('/dashboard/stats')
@login_required
@role_required('Admin', 'Receptionist')
def dashboard_stats():
    """Live JSON endpoint for management dashboard widgets."""
    return jsonify(get_dashboard_kpis())


@api_bp.route('/dashboard/revenue-trend')
@login_required
@role_required('Admin', 'Receptionist')
def revenue_trend():
    """Live JSON endpoint for monthly revenue Chart.js visualization."""
    return jsonify(get_monthly_revenue_trend())


@api_bp.route('/dashboard/status-distribution')
@login_required
@role_required('Admin', 'Receptionist')
def status_distribution():
    """Live JSON endpoint for reservation status doughnut Chart.js visualization."""
    return jsonify(get_reservation_status_distribution())


@api_bp.route('/rooms')
@login_required
@role_required('Admin', 'Receptionist')
def rooms_list():
    rooms = Room.query.all()
    return jsonify([r.to_dict() for r in rooms])


@api_bp.route('/rooms/<int:room_id>')
@login_required
@role_required('Admin', 'Receptionist')
def room_detail(room_id):
    room = db.get_or_404(Room, room_id)
    return jsonify(room.to_dict())


@api_bp.route('/guests')
@login_required
@role_required('Admin', 'Receptionist')
def guests_list():
    search = request.args.get('search', '').strip()
    query = Guest.query
    if search:
        query = query.filter(
            (Guest.first_name.ilike(f'%{search}%')) |
            (Guest.last_name.ilike(f'%{search}%')) |
            (Guest.email.ilike(f'%{search}%'))
        )
    guests = query.limit(50).all()
    return jsonify([g.to_dict() for g in guests])


@api_bp.route('/reservations')
@login_required
@role_required('Admin', 'Receptionist')
def reservations_list():
    reservations = Reservation.query.order_by(Reservation.created_at.desc()).limit(100).all()
    return jsonify([r.to_dict() for r in reservations])


@api_bp.route('/reservations/<int:reservation_id>')
@login_required
@role_required('Admin', 'Receptionist')
def reservation_detail(reservation_id):
    reservation = db.get_or_404(Reservation, reservation_id)
    return jsonify(reservation.to_dict())


@api_bp.route('/reservations/<int:reservation_id>/check-in', methods=['PATCH'])
@login_required
@role_required('Admin', 'Receptionist')
def api_check_in(reservation_id):
    try:
        res = update_reservation_status(
            reservation_id, 'checked_in', current_user.id, "API check-in", request.remote_addr
        )
        return jsonify({'success': True, 'reservation': res.to_dict()})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@api_bp.route('/reservations/<int:reservation_id>/check-out', methods=['PATCH'])
@login_required
@role_required('Admin', 'Receptionist')
def api_check_out(reservation_id):
    try:
        res = update_reservation_status(
            reservation_id, 'checked_out', current_user.id, "API check-out", request.remote_addr
        )
        return jsonify({'success': True, 'reservation': res.to_dict()})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@api_bp.route('/reservations/<int:reservation_id>/cancel', methods=['PATCH'])
@login_required
@role_required('Admin', 'Receptionist')
def api_cancel(reservation_id):
    try:
        data = request.get_json(silent=True) or {}
        reservation = db.get_or_404(Reservation, reservation_id)
        if (
            str(data.get('confirmation_number', '')).strip().upper() != reservation.confirmation_number
            or str(data.get('guest_name', '')).strip().casefold() != reservation.guest.full_name.casefold()
            or str(data.get('guest_email', '')).strip().lower() != reservation.guest.email.casefold()
            or normalize_indian_phone(str(data.get('guest_phone', ''))) != normalize_indian_phone(reservation.guest.phone)
        ):
            return jsonify({'error': 'Caller verification did not match the guest record.'}), 403
        res = cancel_reservation(
            reservation.id,
            request_source='phone',
            requested_by_guest_id=reservation.guest_id,
            processed_by_user_id=current_user.id,
            reason=str(data.get('reason', '')).strip(),
            ip_address=request.remote_addr,
        )
        return jsonify({'success': True, 'reservation': res.to_dict()})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
