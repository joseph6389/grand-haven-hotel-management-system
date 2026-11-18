from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user


def role_required(*roles):
    """Decorator to enforce role-based authorization."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if not current_user.role or current_user.role.name.lower() not in [r.lower() for r in roles]:
                flash('Access denied: You do not possess the required staff clearance for this operation.', 'danger')
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """Enforce Administrator role."""
    return role_required('Admin')(f)


def staff_required(f):
    """Allow only hotel staff, never guest accounts, into the staff portal."""
    return role_required('Admin', 'Receptionist')(f)
