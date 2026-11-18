from decimal import Decimal
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.extensions import db
from app.models.payment import Payment
from app.models.reservation import Reservation
from app.services.payment_service import process_payment, process_refund
from app.routes.auth_helpers import role_required

payments_bp = Blueprint('payments', __name__, url_prefix='/payments')


@payments_bp.route('/')
@login_required
@role_required('Admin', 'Receptionist')
def index():
    """Display comprehensive hotel payment ledger."""
    status = request.args.get('status', '').strip()
    method = request.args.get('method', '').strip()
    search = request.args.get('search', '').strip()

    query = Payment.query

    if status:
        query = query.filter(Payment.payment_status == status)
    if method:
        query = query.filter(Payment.payment_method == method)
    if search:
        query = query.join(Reservation).filter(
            (Payment.payment_reference.ilike(f'%{search}%')) |
            (Reservation.confirmation_number.ilike(f'%{search}%'))
        )

    payments = query.order_by(Payment.created_at.desc()).all()

    # Calculate summary financial stats
    ledger_statuses = ('paid', 'partially_refunded', 'refunded')
    net_payment_expression = Payment.amount - db.func.coalesce(Payment.refunded_amount, 0)
    total_paid = db.session.query(db.func.sum(net_payment_expression)).filter(
        Payment.payment_status.in_(ledger_statuses)
    ).scalar() or Decimal('0.00')
    total_refunded = db.session.query(db.func.sum(db.func.coalesce(Payment.refunded_amount, 0))).filter(
        Payment.payment_status.in_(('partially_refunded', 'refunded'))
    ).scalar() or Decimal('0.00')

    # Pending reservations with outstanding balance
    unpaid_reservations = Reservation.query.filter(
        Reservation.status.in_(['confirmed', 'checked_in']),
        Reservation.paid_amount < Reservation.total_amount
    ).all()

    return render_template(
        'payments/index.html',
        payments=payments,
        unpaid_reservations=unpaid_reservations,
        total_paid=float(total_paid),
        total_refunded=float(total_refunded),
        selected_status=status,
        selected_method=method,
        search_query=search
    )


@payments_bp.route('/process', methods=['POST'])
@login_required
@role_required('Admin', 'Receptionist')
def process():
    """Record an incoming payment against a reservation (simulated gateway)."""
    reservation_id = request.form.get('reservation_id', type=int)
    amount = request.form.get('amount', type=float)
    payment_method = request.form.get('payment_method', 'credit_card')
    notes = request.form.get('notes', '').strip()

    if not reservation_id or not amount:
        flash('Reservation and payment amount are required.', 'warning')
        return redirect(url_for('payments.index'))

    try:
        amt_dec = Decimal(str(amount))
        payment = process_payment(
            reservation_id=reservation_id,
            amount=amt_dec,
            payment_method=payment_method,
            notes=notes,
            processed_by_id=current_user.id,
            ip_address=request.remote_addr
        )
        flash(f'Payment of ₹{payment.amount} recorded successfully ({payment.payment_reference}).', 'success')
        return redirect(url_for('payments.receipt', payment_id=payment.id))
    except ValueError as exc:
        flash(str(exc), 'warning')
        return redirect(url_for('payments.index'))
    except Exception:
        current_app.logger.exception('Payment processing failed')
        flash('Payment could not be processed. Please retry or contact an administrator.', 'danger')
        return redirect(url_for('payments.index'))


@payments_bp.route('/<int:payment_id>/receipt')
@login_required
@role_required('Admin', 'Receptionist')
def receipt(payment_id):
    """Printable payment receipt."""
    payment = db.get_or_404(Payment, payment_id)
    return render_template('payments/receipt.html', payment=payment)


@payments_bp.route('/<int:payment_id>/refund', methods=['POST'])
@login_required
@role_required('Admin', 'Receptionist')
def refund(payment_id):
    """Refund an existing payment."""
    reason = request.form.get('reason', 'Guest requested cancellation/refund.').strip()
    try:
        payment = process_refund(
            payment_id=payment_id,
            reason=reason,
            processed_by_id=current_user.id,
            ip_address=request.remote_addr
        )
        flash(
            f'₹{payment.refunded_amount} in refunds is recorded in the hotel ledger for '
            f'{payment.payment_reference}. This does not confirm an external payout.', 'info'
        )
    except ValueError as exc:
        flash(str(exc), 'warning')
    except Exception:
        current_app.logger.exception('Refund processing failed for payment %s', payment_id)
        flash('Refund could not be processed. Please retry or contact an administrator.', 'danger')

    return redirect(url_for('payments.index'))
