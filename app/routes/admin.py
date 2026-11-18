from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from decimal import Decimal, InvalidOperation
from datetime import time
import re
from app.extensions import db
from app.models.user import User, Role
from app.models.audit import AuditLog
from app.models.setting import HotelSetting
from app.routes.auth_helpers import admin_required
from app.utils.india import normalize_indian_contact
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """Staff user directory and role management."""
    staff_users = User.query.order_by(User.created_at.desc()).all()
    roles = Role.query.filter(func.lower(Role.name) != 'guest').all()
    return render_template('admin/users.html', users=staff_users, roles=roles)


@admin_bp.route('/users/create', methods=['POST'])
@login_required
@admin_required
def create_user():
    """Register a new staff member."""
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip().lower()
    full_name = request.form.get('full_name', '').strip()
    phone = request.form.get('phone', '').strip()
    role_id = request.form.get('role_id', type=int)
    password = request.form.get('password', '')

    if not all([username, email, full_name, role_id, password]):
        flash('All fields are required to register staff.', 'warning')
        return redirect(url_for('admin.users'))

    if User.query.filter_by(username=username).first():
        flash(f'Username "{username}" is already taken.', 'danger')
        return redirect(url_for('admin.users'))

    if User.query.filter_by(email=email).first():
        flash(f'Email "{email}" is already registered.', 'danger')
        return redirect(url_for('admin.users'))

    role = db.session.get(Role, role_id)
    if not role or role.name.lower() not in ('admin', 'receptionist'):
        flash('Staff accounts can only use Admin or Receptionist roles.', 'danger')
        return redirect(url_for('admin.users'))

    new_user = User(
        username=username,
        email=email,
        full_name=full_name,
        phone=phone,
        role_id=role_id,
        is_active=True
    )
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.flush()

    audit = AuditLog(
        user_id=current_user.id,
        action='CREATE_USER',
        entity_type='User',
        entity_id=str(new_user.id),
        details=f"Admin created staff user {username} ({new_user.role.name if new_user.role else 'Role'}).",
        ip_address=request.remote_addr
    )
    db.session.add(audit)
    db.session.commit()

    flash(f'Staff member {full_name} added successfully.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/toggle-active', methods=['POST'])
@login_required
@admin_required
def toggle_user_active(user_id):
    """Activate or deactivate staff login privileges."""
    if user_id == current_user.id:
        flash('You cannot deactivate your own account.', 'warning')
        return redirect(url_for('admin.users'))

    user = db.get_or_404(User, user_id)
    user.is_active = not user.is_active

    state = "activated" if user.is_active else "deactivated"
    db.session.add(
        AuditLog(
            user_id=current_user.id,
            action='TOGGLE_USER_STATUS',
            entity_type='User',
            entity_id=str(user.id),
            details=f"Staff user {user.username} was {state}.",
            ip_address=request.remote_addr
        )
    )
    db.session.commit()

    flash(f'User {user.username} has been {state}.', 'info')
    return redirect(url_for('admin.users'))


@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    """Configure property policies, currency, and tax parameters."""
    if request.method == 'POST':
        hotel_name = request.form.get('hotel_name', 'Grand Haven Hotel').strip()
        hotel_email = request.form.get('hotel_email', '').strip()
        phone_input = request.form.get('hotel_phone', '').strip()
        hotel_phone = normalize_indian_contact(phone_input) if phone_input else ''
        hotel_currency = 'INR'
        checkin_time = request.form.get('default_checkin_time', '15:00').strip()
        checkout_time = request.form.get('default_checkout_time', '11:00').strip()
        cancellation_policy = request.form.get('cancellation_policy', '').strip()

        try:
            tax_rate = Decimal(request.form.get('hotel_tax_rate', '0.12'))
            time.fromisoformat(checkin_time)
            time.fromisoformat(checkout_time)
        except (InvalidOperation, ValueError):
            flash('Enter a valid tax multiplier and check-in/check-out times.', 'warning')
            return redirect(url_for('admin.settings'))
        if (
            not hotel_name or len(hotel_name) > 100
            or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', hotel_email)
            or (phone_input and not hotel_phone)
            or not tax_rate.is_finite() or tax_rate < 0 or tax_rate > Decimal('0.50')
            or not cancellation_policy or len(cancellation_policy) > 2000
        ):
            flash('Review the hotel name, contact details, tax range (0–0.50), and cancellation policy.', 'warning')
            return redirect(url_for('admin.settings'))

        HotelSetting.set_val('HOTEL_NAME', hotel_name, 'string', 'Hotel property brand name')
        HotelSetting.set_val('HOTEL_EMAIL', hotel_email, 'string', 'General contact email')
        HotelSetting.set_val('HOTEL_PHONE', hotel_phone, 'string', 'Property front-desk phone')
        HotelSetting.set_val('HOTEL_CURRENCY', hotel_currency, 'string', 'Primary billing currency code')
        HotelSetting.set_val('HOTEL_TAX_RATE', float(tax_rate), 'float', 'Default tax multiplier')
        HotelSetting.set_val('DEFAULT_CHECKIN_TIME', checkin_time, 'string', 'Standard check-in time')
        HotelSetting.set_val('DEFAULT_CHECKOUT_TIME', checkout_time, 'string', 'Standard check-out time')
        HotelSetting.set_val('CANCELLATION_POLICY', cancellation_policy, 'string', 'Guest cancellation terms')

        db.session.add(
            AuditLog(
                user_id=current_user.id,
                action='UPDATE_SETTINGS',
                entity_type='HotelSetting',
                entity_id='GLOBAL',
                details="Updated system hotel settings and tax parameters.",
                ip_address=request.remote_addr
            )
        )
        db.session.commit()
        flash('Hotel settings updated successfully.', 'success')

    # Load current values
    settings_data = {
        'hotel_name': HotelSetting.get_val('HOTEL_NAME', 'Grand Haven Hotel'),
        'hotel_email': HotelSetting.get_val('HOTEL_EMAIL', 'reservations@grandhavenhotel.com'),
        'hotel_phone': HotelSetting.get_val('HOTEL_PHONE', ''),
        'hotel_currency': HotelSetting.get_val('HOTEL_CURRENCY', 'INR'),
        'hotel_tax_rate': HotelSetting.get_val('HOTEL_TAX_RATE', 0.12),
        'default_checkin_time': HotelSetting.get_val('DEFAULT_CHECKIN_TIME', '15:00'),
        'default_checkout_time': HotelSetting.get_val('DEFAULT_CHECKOUT_TIME', '11:00'),
        'cancellation_policy': HotelSetting.get_val('CANCELLATION_POLICY', 'A ₹500 fee applies at or within 48 hours before configured check-in time. Refund eligibility outside that period is subject to hotel policy and staff review.')
    }

    return render_template('admin/settings.html', settings=settings_data)


@admin_bp.route('/audit-logs')
@login_required
@admin_required
def audit_logs():
    """System activity trail for security and auditing."""
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(150).all()
    return render_template('admin/audit_logs.html', logs=logs)
