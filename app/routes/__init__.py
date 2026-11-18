from app.routes.public import public_bp
from app.routes.auth import auth_bp
from app.routes.dashboard import dashboard_bp
from app.routes.rooms import rooms_bp
from app.routes.guests import guests_bp
from app.routes.reservations import reservations_bp
from app.routes.payments import payments_bp
from app.routes.reports import reports_bp
from app.routes.admin import admin_bp
from app.routes.api import api_bp
from app.routes.account import account_bp

__all__ = [
    'public_bp',
    'auth_bp',
    'dashboard_bp',
    'rooms_bp',
    'guests_bp',
    'reservations_bp',
    'payments_bp',
    'reports_bp',
    'admin_bp',
    'api_bp',
    'account_bp',
]
