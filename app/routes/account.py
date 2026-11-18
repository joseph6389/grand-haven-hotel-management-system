import re
from decimal import Decimal

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, logout_user
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.audit import AuditLog
from app.models.guest import Guest
from app.models.reservation import Reservation
from app.models.payment import Payment
from app.models.setting import HotelSetting
from app.models.user import Role, User
from app.routes.auth_helpers import role_required
from app.services.reservation_service import cancel_reservation
from app.utils.india import normalize_indian_phone

account_bp = Blueprint('account', __name__)
EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')


def _guest_profile():
    profile = current_user.guest_profile
    if not profile:
        abort(403)
    return profile


@account_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('account.dashboard') if current_user.is_guest else url_for('dashboard.index'))
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone_digits = request.form.get('phone', '').strip()
        phone = f'+91{phone_digits}' if re.fullmatch(r'\d{10}', phone_digits) else None
        postal_code = request.form.get('postal_code', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        if not first_name or not last_name or len(first_name) > 60 or len(last_name) > 60:
            flash('Enter your first and last name (60 characters maximum).', 'warning')
        elif not username:
            flash('Enter a username.', 'warning')
        elif not EMAIL_RE.fullmatch(email):
            flash('Enter a valid email address.', 'warning')
        elif not phone:
            flash('Enter a phone number containing exactly 10 digits.', 'warning')
        elif postal_code and not re.fullmatch(r'\d{6}', postal_code):
            flash('Enter a valid six-digit Indian postal code or leave it blank.', 'warning')
        elif len(password) < 10 or password != confirm_password:
            flash('Use a password of at least 10 characters and confirm it correctly.', 'warning')
        elif User.query.filter(func.lower(User.email) == email).first():
            flash('That email already has an account. Sign in or contact reception for help.', 'warning')
        elif User.query.filter(func.lower(User.username) == username.lower()).first():
            flash('That username is already taken. Choose another username.', 'warning')
        elif Guest.query.filter(func.lower(Guest.email) == email).first():
            # Existing stay profiles are never linked by email/phone alone.
            flash('A hotel guest profile already uses that email. Contact reception to verify and link it safely.', 'warning')
        else:
            try:
                role = Role.query.filter(func.lower(Role.name) == 'guest').first()
                if not role:
                    role = Role(name='Guest', description='Guest self-service account')
                    db.session.add(role)
                    db.session.flush()
                guest = Guest(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=phone,
                    city=request.form.get('city', '').strip()[:100] or None,
                    state=request.form.get('state', '').strip()[:100] or None,
                    postal_code=postal_code or None,
                    country='India',
                )
                db.session.add(guest)
                db.session.flush()
                user = User(
                    username=username,
                    email=email,
                    full_name=f'{first_name} {last_name}',
                    phone=phone,
                    role_id=role.id,
                    guest_profile_id=guest.id,
                    is_active=True,
                )
                user.set_password(password)
                db.session.add(user)
                db.session.add(AuditLog(
                    action='GUEST_REGISTER', entity_type='Guest', entity_id=str(guest.id),
                    details='A new guest self-service account was created.', ip_address=request.remote_addr,
                ))
                db.session.commit()
                flash('Your account was created successfully. Please log in.', 'success')
                return redirect(url_for('auth.login'))
            except IntegrityError:
                db.session.rollback()
                flash('An account or guest profile with those details already exists.', 'warning')
            except Exception:
                db.session.rollback()
                current_app.logger.exception('Guest registration failed')
                flash('Registration could not be completed. Please try again.', 'danger')
    return render_template('account/register.html')


@account_bp.route('/account')
@login_required
@role_required('Guest')
def dashboard():
    guest = _guest_profile()
    reservations = guest.reservations.order_by(Reservation.created_at.desc()).all()
    return render_template('account/dashboard.html', guest=guest, reservations=reservations)


@account_bp.route('/account/profile', methods=['GET', 'POST'])
@login_required
@role_required('Guest')
def profile():
    guest = _guest_profile()
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        phone = normalize_indian_phone(request.form.get('phone', ''))
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        postal_code = request.form.get('postal_code', '').strip()
        if not first_name or not last_name or len(first_name) > 60 or len(last_name) > 60 or not phone:
            flash('Enter valid names and an Indian mobile number.', 'warning')
        elif new_password and (not current_user.check_password(current_password) or len(new_password) < 10 or new_password != confirm_password):
            flash('To change your password, enter your current password and confirm a new password of at least 10 characters.', 'warning')
        elif postal_code and not re.fullmatch(r'\d{6}', postal_code):
            flash('Enter a valid six-digit Indian postal code or leave it blank.', 'warning')
        else:
            guest.first_name = first_name
            guest.last_name = last_name
            guest.phone = phone
            guest.address = request.form.get('address', '').strip()[:255] or None
            guest.city = request.form.get('city', '').strip()[:100] or None
            guest.state = request.form.get('state', '').strip()[:100] or None
            guest.postal_code = postal_code or None
            current_user.full_name = f'{first_name} {last_name}'
            current_user.phone = phone
            if new_password:
                current_user.set_password(new_password)
            db.session.add(AuditLog(
                action='GUEST_PROFILE_UPDATE', entity_type='Guest', entity_id=str(guest.id),
                details='Guest updated their own profile.', ip_address=request.remote_addr,
            ))
            db.session.commit()
            flash('Your profile was updated.', 'success')
    return render_template('account/profile.html', guest=guest)


@account_bp.route('/account/reservations/<int:reservation_id>')
@login_required
@role_required('Guest')
def reservation_detail(reservation_id):
    guest = _guest_profile()
    reservation = Reservation.query.filter_by(id=reservation_id, guest_id=guest.id).first_or_404()
    payments = reservation.payments.order_by(Payment.created_at.desc()).all()
    policy = HotelSetting.get_val('CANCELLATION_POLICY', 'Contact the hotel for cancellation and refund review.')
    cancellation = next(
        (item for item in reservation.status_history if item.new_status == 'cancelled'),
        None,
    )
    return render_template(
        'account/reservation_detail.html', reservation=reservation,
        payments=payments, policy=policy, cancellation=cancellation,
    )


@account_bp.route('/account/reservations/<int:reservation_id>/cancel', methods=['POST'])
@login_required
@role_required('Guest')
def cancel(reservation_id):
    guest = _guest_profile()
    reservation = Reservation.query.filter_by(id=reservation_id, guest_id=guest.id).first_or_404()
    if not reservation.can_transition_to('cancelled'):
        flash('This reservation is no longer eligible for cancellation.', 'warning')
        return redirect(url_for('account.reservation_detail', reservation_id=reservation.id))
    if request.form.get('confirm_cancel') != 'yes':
        flash('Confirm the cancellation to continue.', 'warning')
        return redirect(url_for('account.reservation_detail', reservation_id=reservation.id))
    try:
        result = cancel_reservation(
            reservation.id,
            request_source='guest_account',
            requested_by_guest_id=guest.id,
            reason='Guest cancelled from their account.',
            ip_address=request.remote_addr,
        )
        flash(
            f'Reservation {result.confirmation_number} was cancelled. '
            'The fee and refund-review status are shown in your reservation details; no external payout is confirmed.',
            'info',
        )
    except ValueError as exc:
        flash(str(exc), 'warning')
    return redirect(url_for('account.reservation_detail', reservation_id=reservation.id))


@account_bp.route('/account/logout', methods=['POST'])
@login_required
@role_required('Guest')
def logout():
    user_id = current_user.id
    logout_user()
    db.session.add(AuditLog(
        user_id=user_id, action='GUEST_LOGOUT', entity_type='User', entity_id=str(user_id),
        details='Guest logged out.', ip_address=request.remote_addr,
    ))
    db.session.commit()
    flash('You have been signed out.', 'info')
    return redirect(url_for('public.index'))
