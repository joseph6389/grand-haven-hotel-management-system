import uuid
from decimal import Decimal
from typing import Optional
from flask import current_app
from app.extensions import db
from app.models.reservation import Reservation, ReservationStatusHistory
from app.models.payment import Payment
from app.models.audit import AuditLog


def process_payment(
    reservation_id: int,
    amount: Decimal,
    payment_method: str = 'simulation',
    notes: Optional[str] = None,
    processed_by_id: Optional[int] = None,
    ip_address: Optional[str] = None
) -> Payment:
    """
    Atomic payment processing service:
    Validates balance and records the payment as the source of truth for the reservation balance.
    """
    reservation = db.session.execute(
        db.select(Reservation).where(Reservation.id == reservation_id).with_for_update().execution_options(populate_existing=True)
    ).unique().scalar_one_or_none()
    if not reservation:
        raise ValueError("Reservation does not exist.")

    amount = Decimal(str(amount)).quantize(Decimal('0.01'))
    if amount <= Decimal('0.00'):
        raise ValueError("Payment amount must be greater than zero.")

    outstanding = reservation.outstanding_balance
    if amount > outstanding:
        raise ValueError(f"Payment amount (₹{amount}) exceeds outstanding balance of ₹{outstanding}.")

    try:
        payment_count = reservation.payments.count() + 1
        ref = f"PAY-{reservation.confirmation_number.replace('GH-', '')}-{payment_count}"
        txn_ref = f"SIM-{uuid.uuid4().hex[:10].upper()}"

        payment = Payment(
            reservation_id=reservation.id,
            payment_reference=ref,
            amount=amount,
            currency=current_app.config.get('HOTEL_CURRENCY', 'INR'),
            payment_method=payment_method,
            payment_status='paid',
            transaction_reference=txn_ref,
            notes=notes or "Payment received via simulated gateway",
            processed_by_id=processed_by_id
        )
        db.session.add(payment)

        # Audit log
        audit = AuditLog(
            user_id=processed_by_id,
            action='RECORD_PAYMENT',
            entity_type='Payment',
            entity_id=ref,
            details=f"Payment of ₹{amount} recorded for reservation {reservation.confirmation_number}. Method: {payment_method}.",
            ip_address=ip_address
        )
        db.session.add(audit)

        db.session.commit()
        return payment
    except Exception as exc:
        db.session.rollback()
        raise exc



def process_refund(
    payment_id: int,
    refund_amount: Optional[Decimal] = None,
    reason: Optional[str] = None,
    processed_by_id: Optional[int] = None,
    ip_address: Optional[str] = None
) -> Payment:
    """Record a full or partial refund in the hotel ledger; no provider payout is verified."""
    original_payment = db.session.execute(
        db.select(Payment).where(Payment.id == payment_id).with_for_update().execution_options(populate_existing=True)
    ).scalar_one_or_none()
    if not original_payment:
        raise ValueError("Payment record not found.")

    if original_payment.payment_status not in ('paid', 'partially_refunded'):
        raise ValueError("This payment cannot be refunded.")

    payment_amount = Decimal(str(original_payment.amount)).quantize(
        Decimal('0.01')
    )
    already_refunded = Decimal(
        str(original_payment.refunded_amount or '0.00')
    ).quantize(Decimal('0.01'))

    remaining_refundable = payment_amount - already_refunded

    if remaining_refundable <= Decimal('0.00'):
        raise ValueError("This payment has already been fully refunded.")

    amt = (
        remaining_refundable
        if refund_amount is None
        else Decimal(str(refund_amount)).quantize(Decimal('0.01'))
    )

    if amt <= Decimal('0.00') or amt > remaining_refundable:
        raise ValueError(
            f"Refund amount must be between ₹0.01 and ₹{remaining_refundable}."
        )

    reservation = db.session.execute(
        db.select(Reservation)
        .where(Reservation.id == original_payment.reservation_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    ).unique().scalar_one()

    try:
        original_payment.refunded_amount = already_refunded + amt

        if original_payment.refunded_amount >= payment_amount:
            original_payment.payment_status = 'refunded'
        else:
            original_payment.payment_status = 'partially_refunded'

        original_payment.notes = (
            f"{original_payment.notes or ''} "
            f"[REFUND ₹{amt}: {reason or 'Requested by guest'}]"
        ).strip()

        cancellation_history = db.session.execute(
            db.select(ReservationStatusHistory)
            .where(
                ReservationStatusHistory.reservation_id == reservation.id,
                ReservationStatusHistory.new_status == 'cancelled',
                ReservationStatusHistory.refund_status == 'pending_review',
            )
            .order_by(ReservationStatusHistory.changed_at.desc(), ReservationStatusHistory.id.desc())
            .with_for_update()
        ).scalars().first()
        if cancellation_history:
            cancellation_history.refund_status = 'recorded'

        audit = AuditLog(
            user_id=processed_by_id,
            action='PROCESS_REFUND',
            entity_type='Payment',
            entity_id=original_payment.payment_reference,
            details=(
                f"Refund of ₹{amt} recorded in the hotel ledger for "
                f"{original_payment.payment_reference} on reservation "
                f"{reservation.confirmation_number}. External payout was not verified. "
                f"Reason: {reason}"
            ),
            ip_address=ip_address
        )
        db.session.add(audit)
        db.session.commit()
        return original_payment

    except Exception:
        db.session.rollback()
        raise
