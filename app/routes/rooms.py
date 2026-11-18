from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.extensions import db
from app.models.room import Room, RoomType, Amenity
from app.routes.auth_helpers import role_required
from app.models.audit import AuditLog

rooms_bp = Blueprint('rooms', __name__, url_prefix='/rooms')


@rooms_bp.route('/')
@login_required
@role_required('Admin', 'Receptionist')
def index():
    """List and manage all hotel rooms."""
    room_type_id = request.args.get('room_type_id', type=int)
    status = request.args.get('status', '').strip()
    search = request.args.get('search', '').strip()
    floor = request.args.get('floor', type=int)

    query = Room.query

    if room_type_id:
        query = query.filter(Room.room_type_id == room_type_id)
    if status:
        query = query.filter(Room.operational_status == status)
    if floor:
        query = query.filter(Room.floor == floor)
    if search:
        query = query.filter(Room.room_number.ilike(f'%{search}%'))

    rooms = query.order_by(Room.floor.asc(), Room.room_number.asc()).all()
    room_types = RoomType.query.all()
    amenities = Amenity.query.all()

    # Calculate status counts for filter badges
    total_count = Room.query.count()
    operational_count = Room.query.filter_by(operational_status='operational', is_active=True).count()
    maintenance_count = Room.query.filter_by(operational_status='maintenance').count()
    out_of_order_count = Room.query.filter_by(operational_status='out_of_order').count()

    return render_template(
        'rooms/index.html',
        rooms=rooms,
        room_types=room_types,
        amenities=amenities,
        selected_type=room_type_id,
        selected_status=status,
        selected_floor=floor,
        search_query=search,
        stats={
            'total': total_count,
            'operational': operational_count,
            'maintenance': maintenance_count,
            'out_of_order': out_of_order_count
        }
    )


@rooms_bp.route('/create', methods=['POST'])
@login_required
@role_required('Admin', 'Receptionist')
def create():
    """Add a new physical room to the hotel inventory."""
    room_number = request.form.get('room_number', '').strip().upper()
    room_type_id = request.form.get('room_type_id', type=int)
    floor = request.form.get('floor', type=int, default=1)
    capacity = request.form.get('capacity', type=int, default=2)
    operational_status = request.form.get('operational_status', 'operational')
    notes = request.form.get('notes', '').strip()
    amenity_ids = request.form.getlist('amenities', type=int)

    if not room_number or not room_type_id:
        flash('Room number and room type are mandatory.', 'warning')
        return redirect(url_for('rooms.index'))

    max_room_number_length = Room.__table__.c.room_number.type.length
    if len(room_number) > max_room_number_length:
        flash(f'Room number must be {max_room_number_length} characters or fewer.', 'warning')
        return redirect(url_for('rooms.index'))

    existing = Room.query.filter_by(room_number=room_number).first()
    if existing:
        flash(f'Room number "{room_number}" is already registered.', 'danger')
        return redirect(url_for('rooms.index'))

    room = Room(
        room_number=room_number,
        room_type_id=room_type_id,
        floor=floor,
        capacity=capacity,
        operational_status=operational_status,
        notes=notes,
        is_active=True
    )

    if amenity_ids:
        selected_amenities = Amenity.query.filter(Amenity.id.in_(amenity_ids)).all()
        room.amenities = selected_amenities

    db.session.add(room)
    db.session.flush()

    audit = AuditLog(
        user_id=current_user.id,
        action='CREATE_ROOM',
        entity_type='Room',
        entity_id=str(room.id),
        details=f"Room {room_number} created on Floor {floor} with status {operational_status}.",
        ip_address=request.remote_addr
    )
    db.session.add(audit)
    db.session.commit()

    flash(f'Room {room_number} added successfully.', 'success')
    return redirect(url_for('rooms.index'))


@rooms_bp.route('/<int:room_id>/edit', methods=['POST'])
@login_required
@role_required('Admin', 'Receptionist')
def edit(room_id):
    """Update room attributes and amenities."""
    room = db.get_or_404(Room, room_id)
    room_number = request.form.get('room_number', '').strip().upper()
    room_type_id = request.form.get('room_type_id', type=int)
    floor = request.form.get('floor', type=int)
    capacity = request.form.get('capacity', type=int)
    operational_status = request.form.get('operational_status')
    notes = request.form.get('notes', '').strip()
    amenity_ids = request.form.getlist('amenities', type=int)

    if not room_number:
        flash('Room number is mandatory.', 'warning')
        return redirect(url_for('rooms.index'))

    max_room_number_length = Room.__table__.c.room_number.type.length
    if len(room_number) > max_room_number_length:
        flash(f'Room number must be {max_room_number_length} characters or fewer.', 'warning')
        return redirect(url_for('rooms.index'))

    # Check for room number duplicate
    conflict = Room.query.filter(Room.room_number == room_number, Room.id != room.id).first()
    if conflict:
        flash(f'Room number "{room_number}" belongs to another room.', 'danger')
        return redirect(url_for('rooms.index'))

    room.room_number = room_number
    room.room_type_id = room_type_id
    room.floor = floor
    room.capacity = capacity
    room.operational_status = operational_status
    room.notes = notes

    if amenity_ids is not None:
        room.amenities = Amenity.query.filter(Amenity.id.in_(amenity_ids)).all()

    audit = AuditLog(
        user_id=current_user.id,
        action='UPDATE_ROOM',
        entity_type='Room',
        entity_id=str(room.id),
        details=f"Room {room_number} details updated.",
        ip_address=request.remote_addr
    )
    db.session.add(audit)
    db.session.commit()

    flash(f'Room {room.room_number} updated successfully.', 'success')
    return redirect(url_for('rooms.index'))


@rooms_bp.route('/<int:room_id>/status', methods=['POST'])
@login_required
@role_required('Admin', 'Receptionist')
def update_status(room_id):
    """Quick operational status transition for staff (e.g. Mark for Maintenance)."""
    room = db.get_or_404(Room, room_id)
    new_status = request.form.get('operational_status', 'operational')

    if new_status in ['operational', 'maintenance', 'out_of_order']:
        prev = room.operational_status
        room.operational_status = new_status
        db.session.add(
            AuditLog(
                user_id=current_user.id,
                action='ROOM_STATUS_CHANGE',
                entity_type='Room',
                entity_id=str(room.id),
                details=f"Room {room.room_number} status changed from {prev} to {new_status}.",
                ip_address=request.remote_addr
            )
        )
        db.session.commit()
        flash(f'Room {room.room_number} status changed to {new_status.replace("_", " ").title()}.', 'info')
    else:
        flash('Invalid room status.', 'warning')

    return redirect(url_for('rooms.index'))
