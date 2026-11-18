from decimal import Decimal
from app.extensions import db
from app.utils.datetime_utils import utcnow, india_datetime_iso


class Payment(db.Model):
    """Payment record linked to a guest reservation."""
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(
        db.Integer,
        db.ForeignKey('reservations.id', ondelete='RESTRICT'),
        nullable=False,
        index=True
    )
    payment_reference = db.Column(
        db.String(40), unique=True, nullable=False, index=True
    )
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    refunded_amount = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=Decimal('0.00'),
        server_default='0.00'
    )
    currency = db.Column(db.String(3), nullable=False, default='INR')
    payment_method = db.Column(
        db.String(30), nullable=False, default='credit_card'
    )
    payment_status = db.Column(
        db.Enum('paid', 'partially_refunded', 'refunded', 'failed',
                name='payment_status', native_enum=True),
        nullable=False, default='paid', index=True
    )  # paid, partially_refunded, refunded, failed
    transaction_reference = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.String(255), nullable=True)
    processed_by_id = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True
    )
    created_at = db.Column(
        db.DateTime, default=utcnow, nullable=False, index=True
    )

    # Relationships
    reservation = db.relationship('Reservation', back_populates='payments')
    processed_by = db.relationship('User')

    @property
    def formatted_amount(self) -> str:
        return f"₹{float(self.amount):,.2f}"

    def to_dict(self):
        return {
            'id': self.id,
            'reservation_id': self.reservation_id,
            'confirmation_number': self.reservation.confirmation_number if self.reservation else None,
            'guest_name': self.reservation.guest.full_name if self.reservation and self.reservation.guest else 'Guest',
            'payment_reference': self.payment_reference,
            'amount': float(self.amount),
            'refunded_amount': float(self.refunded_amount or 0),
            'formatted_amount': self.formatted_amount,
            'currency': self.currency,
            'payment_method': self.payment_method,
            'payment_status': self.payment_status,
            'transaction_reference': self.transaction_reference,
            'notes': self.notes,
            'processed_by': self.processed_by.full_name if self.processed_by else 'System Simulation',
            'created_at': india_datetime_iso(self.created_at)
        }

    def __repr__(self):
        return f'<Payment {self.payment_reference}: ₹{self.amount} ({self.payment_status})>'
