from urllib.parse import urlsplit
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models.user import User
from app.models.audit import AuditLog
from app.utils.datetime_utils import utcnow
from app.routes.auth_helpers import role_required

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Staff authentication portal with password security and demo credentials notice."""
    if current_user.is_authenticated:
        return redirect(url_for('public.index') if current_user.is_guest else url_for('dashboard.index'))

    if request.method == 'POST':
        login_input = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        if not login_input or not password:
            flash('Please enter both your username/email and password.', 'warning')
            return render_template('auth/login.html')

        # Allow login via username or email
        user = User.query.filter(
            (User.username == login_input) | (User.email == login_input)
        ).first()

        # Guest accounts must sign in with their registered username. Staff may
        # continue using the username or email behavior they already had.
        if user and user.is_guest and user.username != login_input:
            user = None

        if user and user.check_password(password):
            if not user.is_active:
                flash('This staff account has been deactivated. Please contact an administrator.', 'danger')
                return render_template('auth/login.html')

            user.last_login = utcnow()
            db.session.add(
                AuditLog(
                    user_id=user.id,
                    action='LOGIN_SUCCESS',
                    entity_type='User',
                    entity_id=str(user.id),
                    details=f"User {user.username} logged in successfully.",
                    ip_address=request.remote_addr
                )
            )
            db.session.commit()
            login_user(user, remember=remember)

            flash(f'Welcome back, {user.full_name} ({user.role.name}).', 'success')

            next_page = request.args.get('next')

            if user.is_guest:
                return redirect(url_for('public.index'))

            if next_page:
                parsed_next = urlsplit(next_page)

                if (
                    next_page.startswith('/')
                    and not next_page.startswith('//')
                    and '\\' not in next_page
                    and parsed_next.scheme == ''
                    and parsed_next.netloc == ''
                ):
                    return redirect(next_page)

            return redirect(url_for('dashboard.index'))

        else:
            # Audit failed attempt
            db.session.add(
                AuditLog(
                    user_id=None,
                    action='LOGIN_FAILED',
                    entity_type='User',
                    entity_id=login_input,
                    details=f"Failed login attempt for identifier: {login_input}",
                    ip_address=request.remote_addr
                )
            )
            db.session.commit()
            flash('Invalid username or password. Please check your credentials.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout', methods=['POST'])
@login_required
@role_required('Admin', 'Receptionist')
def logout():
    """Terminate current user session."""
    user_id = current_user.id
    user_name = current_user.username
    logout_user()

    db.session.add(
        AuditLog(
            user_id=user_id,
            action='LOGOUT',
            entity_type='User',
            entity_id=str(user_id),
            details=f"User {user_name} logged out.",
            ip_address=request.remote_addr
        )
    )
    db.session.commit()

    flash('You have been securely logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Receptionist')
def profile():
    """User profile management and password change."""
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'update_info':
            current_user.full_name = request.form.get('full_name', current_user.full_name).strip()
            current_user.phone = request.form.get('phone', current_user.phone).strip()
            db.session.commit()
            flash('Profile details updated successfully.', 'success')
        elif action == 'change_password':
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')

            if not current_user.check_password(current_password):
                flash('Current password is incorrect.', 'danger')
            elif len(new_password) < 6:
                flash('New password must be at least 6 characters long.', 'warning')
            elif new_password != confirm_password:
                flash('New passwords do not match.', 'warning')
            else:
                current_user.set_password(new_password)
                db.session.commit()
                flash('Password changed successfully.', 'success')

    return render_template('auth/profile.html', user=current_user)
