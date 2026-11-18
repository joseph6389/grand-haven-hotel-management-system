import csv
import io
from flask import Blueprint, render_template, Response, request
from flask_login import login_required
from app.models.reservation import Reservation
from app.models.payment import Payment
from app.services.report_service import (
    get_dashboard_kpis,
    get_monthly_revenue_trend,
    get_reservation_status_distribution,
    get_room_type_performance,
    get_unpaid_reservations_report
)
from app.routes.auth_helpers import role_required
from app.utils.datetime_utils import format_india_date, format_india_datetime

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


@reports_bp.route('/')
@login_required
@role_required('Admin', 'Receptionist')
def index():
    """Reporting center with financial and occupancy metrics."""
    kpis = get_dashboard_kpis()
    room_perf = get_room_type_performance()
    unpaid = get_unpaid_reservations_report()

    # Calculate cancellation rate
    total_res = kpis['total_reservations']
    cancelled_count = Reservation.query.filter_by(status='cancelled').count()
    cancellation_rate = (cancelled_count / total_res * 100) if total_res > 0 else 0.0

    return render_template(
        'reports/index.html',
        kpis=kpis,
        room_performance=room_perf,
        unpaid_reservations=unpaid,
        cancellation_rate=round(cancellation_rate, 1)
    )


@reports_bp.route('/export-csv')
@login_required
@role_required('Admin', 'Receptionist')
def export_csv():
    """Generate and stream a CSV file containing reservation and revenue data."""
    report_type = request.args.get('type', 'reservations')

    output = io.StringIO()
    writer = csv.writer(output)

    if report_type == 'payments':
        writer.writerow([
            'Payment Reference', 'Confirmation Number', 'Guest Name',
            'Amount (₹)', 'Currency', 'Method', 'Status', 'Date'
        ])
        payments = Payment.query.order_by(Payment.created_at.desc()).all()
        for p in payments:
            writer.writerow([
                p.payment_reference,
                p.reservation.confirmation_number if p.reservation else 'N/A',
                p.reservation.guest.full_name if p.reservation and p.reservation.guest else 'Guest',
                float(p.amount),
                p.currency,
                p.payment_method,
                p.payment_status,
                format_india_datetime(p.created_at)
            ])
        filename = "grand_haven_payments.csv"

    else:
        writer.writerow([
            'Confirmation #', 'Guest Name', 'Email', 'Check-In', 'Check-Out',
            'Nights', 'Rooms', 'Room Charges (₹)', 'Tax (₹)', 'Total (₹)',
            'Paid (₹)', 'Balance (₹)', 'Status', 'Booked On'
        ])
        reservations = Reservation.query.order_by(Reservation.created_at.desc()).all()
        for r in reservations:
            room_str = ", ".join([alloc.room.room_number for alloc in r.room_allocations if alloc.room])
            writer.writerow([
                r.confirmation_number,
                r.guest.full_name if r.guest else 'Guest',
                r.guest.email if r.guest else '',
                format_india_date(r.check_in_date),
                format_india_date(r.check_out_date),
                r.total_nights,
                room_str,
                float(r.room_charges),
                float(r.tax_amount),
                float(r.total_amount),
                float(r.paid_amount),
                float(r.outstanding_balance),
                r.status,
                format_india_datetime(r.created_at)
            ])
        filename = "grand_haven_reservations.csv"

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )
