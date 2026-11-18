from flask import Blueprint, render_template
from flask_login import login_required
from app.models.reservation import Reservation
from app.models.room import Room
from app.models.guest import Guest
from app.models.audit import AuditLog
from app.extensions import db
from app.services.report_service import get_dashboard_kpis
from app.routes.auth_helpers import role_required
from app.utils.datetime_utils import india_today

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
@role_required('Admin', 'Receptionist')
def index():
    """Management dashboard displaying real-time hotel operational metrics and charts."""
    today = india_today()

    # Query metrics from DB
    kpis = get_dashboard_kpis()

    # Recent reservations
    recent_reservations = Reservation.query.order_by(
        Reservation.created_at.desc()
    ).limit(8).all()

    # Today's arrivals
    today_arrivals = Reservation.query.filter(
        Reservation.check_in_date == today,
        Reservation.status.in_(['confirmed', 'pending'])
    ).limit(6).all()

    # Today's departures
    today_departures = Reservation.query.filter(
        Reservation.check_out_date == today,
        Reservation.status == 'checked_in'
    ).limit(6).all()

    return render_template(
        'dashboard/index.html',
        kpis=kpis,
        recent_reservations=recent_reservations,
        today_arrivals=today_arrivals,
        today_departures=today_departures,
        today_date=today.strftime('%d/%m/%Y'),
        last_event_id=db.session.query(db.func.max(AuditLog.id)).scalar() or 0,
    )
