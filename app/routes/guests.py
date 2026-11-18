from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.guest import Guest
from app.models.audit import AuditLog
from app.routes.auth_helpers import role_required

guests_bp = Blueprint('guests', __name__, url_prefix='/guests')



@guests_bp.route('/')
@login_required
@role_required('Admin', 'Receptionist')
def index():
    """List hotel guests with search functionality."""
    search = request.args.get('search', '').strip()
    query = Guest.query

    if search:
        search_terms = search.split()

        for term in search_terms:
            query = query.filter(
                (Guest.first_name.ilike(f'%{term}%')) |
                (Guest.last_name.ilike(f'%{term}%')) |
                (Guest.email.ilike(f'%{term}%')) |
                (Guest.phone.ilike(f'%{term}%'))
            )

    guests = query.order_by(Guest.created_at.desc()).all()
    return render_template(
        'guests/index.html',
        guests=guests,
        search_query=search
    )



@guests_bp.route('/create', methods=['POST'])
@login_required
@role_required('Admin', 'Receptionist')
def create():
    """Register a new guest profile."""
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    email = request.form.get('email', '').strip().lower()
    phone = request.form.get('phone', '').strip()
    address = request.form.get('address', '').strip()
    city = request.form.get('city', '').strip()
    country = request.form.get('country', '').strip()
    id_type = request.form.get('identification_type', 'Passport')
    id_num = request.form.get('identification_number', '').strip()
    notes = request.form.get('notes', '').strip()

    if not first_name or not last_name or not email or not phone:
        flash('First name, last name, email, and phone are mandatory.', 'warning')
        return redirect(url_for('guests.index'))

    existing = Guest.query.filter_by(email=email).first()
    if existing:
        flash(f'A guest with email "{email}" already exists.', 'danger')
        return redirect(url_for('guests.index'))

    guest = Guest(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        address=address,
        city=city,
        country=country,
        identification_type=id_type,
        identification_number=id_num,
        notes=notes
    )
    db.session.add(guest)
    db.session.flush()

    audit = AuditLog(
        user_id=current_user.id,
        action='CREATE_GUEST',
        entity_type='Guest',
        entity_id=str(guest.id),
        details=f"Registered guest {guest.full_name} ({guest.email}).",
        ip_address=request.remote_addr
    )
    db.session.add(audit)
    db.session.commit()

    flash(f'Guest {guest.full_name} registered successfully.', 'success')
    return redirect(url_for('guests.index'))


@guests_bp.route('/<int:guest_id>')
@login_required
@role_required('Admin', 'Receptionist')
def detail(guest_id):
    """View guest profile and comprehensive reservation history."""
    guest = db.get_or_404(Guest, guest_id)
    reservations = guest.reservations.order_by('created_at').all()
    return render_template('guests/detail.html', guest=guest, reservations=reservations)


@guests_bp.route('/<int:guest_id>/edit', methods=['POST'])
@login_required
@role_required('Admin', 'Receptionist')
def edit(guest_id):
    """Update guest profile details."""
    guest = db.get_or_404(Guest, guest_id)
    email = request.form.get('email', '').strip().lower()

    conflict = Guest.query.filter(Guest.email == email, Guest.id != guest.id).first()
    if conflict:
        flash(f'Email "{email}" is already in use by another guest.', 'danger')
        return redirect(url_for('guests.detail', guest_id=guest.id))

    guest.first_name = request.form.get('first_name', guest.first_name).strip()
    guest.last_name = request.form.get('last_name', guest.last_name).strip()
    guest.email = email
    guest.phone = request.form.get('phone', guest.phone).strip()
    guest.address = request.form.get('address', guest.address).strip()
    guest.city = request.form.get('city', guest.city).strip()
    guest.country = request.form.get('country', guest.country).strip()
    guest.identification_type = request.form.get('identification_type', guest.identification_type)
    guest.identification_number = request.form.get('identification_number', guest.identification_number).strip()
    guest.notes = request.form.get('notes', guest.notes).strip()

    audit = AuditLog(
        user_id=current_user.id,
        action='UPDATE_GUEST',
        entity_type='Guest',
        entity_id=str(guest.id),
        details=f"Updated profile for guest {guest.full_name}.",
        ip_address=request.remote_addr
    )
    db.session.add(audit)
    db.session.commit()

    flash('Guest details updated successfully.', 'success')
    return redirect(url_for('guests.detail', guest_id=guest.id))
