from decimal import Decimal
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import case, func, literal, select
from app.extensions import db
from app.utils.datetime_utils import utcnow, india_datetime_iso


class Reservation(db.Model):
    """Core hotel reservation record."""
    __tablename__ = 'reservations'

    id = db.Column(db.Integer, primary_key=True)
    confirmation_number = db.Column(db.String(32), unique=True, nullable=False, index=True)
    guest_id = db.Column(db.Integer, db.ForeignKey('guests.id', ondelete='RESTRICT'), nullable=False, index=True)

    # Stay schedule
    check_in_date = db.Column(db.Date, nullable=False, index=True)
    check_out_date = db.Column(db.Date, nullable=False, index=True)
    adults_count = db.Column(db.Integer, nullable=False, default=1)
    children_count = db.Column(db.Integer, nullable=False, default=0)

    # Financial inputs retained as historical transaction snapshots.
    tax_amount = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal('0.00'))
    discount_amount = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal('0.00'))

    # Reservation state lifecycle: 'pending', 'confirmed', 'checked_in', 'checked_out', 'cancelled'
    status = db.Column(
        db.Enum('pending', 'confirmed', 'checked_in', 'checked_out', 'cancelled',
                name='reservation_status', native_enum=True),
        nullable=False, default='confirmed', index=True
    )
    special_requests = db.Column(db.Text, nullable=True)

    # Audit trail
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    guest = db.relationship('Guest', back_populates='reservations')
    created_by = db.relationship('User', back_populates='reservations_created', foreign_keys=[created_by_id])
    room_allocations = db.relationship('ReservationRoom', back_populates='reservation', cascade='all, delete-orphan', lazy='joined')
    payments = db.relationship('Payment', back_populates='reservation', cascade='all, delete-orphan', lazy='dynamic')
    services = db.relationship('ReservationService', back_populates='reservation', cascade='all, delete-orphan', lazy='dynamic')
    status_history = db.relationship('ReservationStatusHistory', back_populates='reservation', cascade='all, delete-orphan', order_by='ReservationStatusHistory.changed_at.desc()')

    # Status transitions allowed
    ALLOWED_TRANSITIONS = {
        'pending': ['confirmed', 'cancelled'],
        'confirmed': ['checked_in', 'cancelled'],
        'checked_in': ['checked_out'],
        'checked_out': [],
        'cancelled': []
    }

    @hybrid_property
    def total_nights(self) -> int:
        if self.check_in_date is None or self.check_out_date is None:
            return 0
        return max((self.check_out_date - self.check_in_date).days, 0)

    @total_nights.expression
    def total_nights(cls):
        return func.datediff(cls.check_out_date, cls.check_in_date)

    @hybrid_property
    def room_charges(self) -> Decimal:
        return sum((allocation.subtotal for allocation in self.room_allocations), Decimal('0.00'))

    @room_charges.expression
    def room_charges(cls):
        from app.models.reservation import ReservationRoom
        return (
            select(func.coalesce(func.sum(ReservationRoom.nightly_rate * ReservationRoom.nights), 0))
            .where(ReservationRoom.reservation_id == cls.id)
            .correlate(cls)
            .scalar_subquery()
        )

    @hybrid_property
    def total_amount(self) -> Decimal:
        amount = Decimal(str(self.room_charges or 0)) + Decimal(str(self.tax_amount or 0)) - Decimal(str(self.discount_amount or 0))
        return max(Decimal('0.00'), amount.quantize(Decimal('0.01')))

    @total_amount.expression
    def total_amount(cls):
        amount = cls.room_charges + cls.tax_amount - cls.discount_amount
        return case((amount < 0, literal(0)), else_=amount)

    @hybrid_property
    def paid_amount(self) -> Decimal:
        return sum((payment.amount - payment.refunded_amount for payment in self.payments
                    if payment.payment_status in ('paid', 'partially_refunded')), Decimal('0.00'))

    @paid_amount.expression
    def paid_amount(cls):
        from app.models.payment import Payment
        return (
            select(func.coalesce(func.sum(Payment.amount - Payment.refunded_amount), 0))
            .where(
                Payment.reservation_id == cls.id,
                Payment.payment_status.in_(('paid', 'partially_refunded')),
            )
            .correlate(cls)
            .scalar_subquery()
        )

    @property
    def outstanding_balance(self) -> Decimal:
        diff = Decimal(str(self.total_amount)) - Decimal(str(self.paid_amount))
        return max(Decimal('0.00'), diff)

    @property
    def is_fully_paid(self) -> bool:
        return Decimal(str(self.paid_amount)) >= Decimal(str(self.total_amount))

    @property
    def payment_status(self) -> str:
        paid = Decimal(str(self.paid_amount))
        total = Decimal(str(self.total_amount))
        if paid >= total and total > 0:
            return 'paid'
        elif paid > 0:
            return 'partially_paid'
        else:
            return 'unpaid'

    @property
    def assigned_rooms(self):
        return [alloc.room for alloc in self.room_allocations if alloc.room]

    def can_transition_to(self, new_status: str) -> bool:
        return new_status in self.ALLOWED_TRANSITIONS.get(self.status, [])

    def to_dict(self):
        return {
            'id': self.id,
            'confirmation_number': self.confirmation_number,
            'guest_id': self.guest_id,
            'guest_name': self.guest.full_name if self.guest else 'Unknown',
            'guest_email': self.guest.email if self.guest else '',
            'guest_phone': self.guest.phone if self.guest else '',
            'check_in_date': self.check_in_date.isoformat(),
            'check_out_date': self.check_out_date.isoformat(),
            'adults_count': self.adults_count,
            'children_count': self.children_count,
            'total_nights': self.total_nights,
            'room_charges': float(self.room_charges),
            'tax_amount': float(self.tax_amount),
            'discount_amount': float(self.discount_amount),
            'total_amount': float(self.total_amount),
            'paid_amount': float(self.paid_amount),
            'outstanding_balance': float(self.outstanding_balance),
            'status': self.status,
            'payment_status': self.payment_status,
            'special_requests': self.special_requests,
            'rooms': [alloc.to_dict() for alloc in self.room_allocations],
            'created_at': india_datetime_iso(self.created_at)
        }

    def __repr__(self):
        return f'<Reservation {self.confirmation_number} - {self.status}>'


class ReservationRoom(db.Model):
    """Bridge table allocating specific hotel rooms to reservations with historical rate snapshots."""
    __tablename__ = 'reservation_rooms'

    id = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservations.id', ondelete='CASCADE'), nullable=False, index=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id', ondelete='RESTRICT'), nullable=False, index=True)
    nightly_rate = db.Column(db.Numeric(10, 2), nullable=False)
    nights = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('reservation_id', 'room_id', name='uq_reservation_room'),
    )

    reservation = db.relationship('Reservation', back_populates='room_allocations')
    room = db.relationship('Room', back_populates='reservation_allocations')

    @hybrid_property
    def subtotal(self) -> Decimal:
        return (Decimal(str(self.nightly_rate or 0)) * Decimal(int(self.nights or 0))).quantize(Decimal('0.01'))

    @subtotal.expression
    def subtotal(cls):
        return cls.nightly_rate * cls.nights

    def to_dict(self):
        return {
            'id': self.id,
            'room_id': self.room_id,
            'room_number': self.room.room_number if self.room else None,
            'room_type': self.room.room_type.name if self.room and self.room.room_type else None,
            'nightly_rate': float(self.nightly_rate),
            'nights': self.nights,
            'subtotal': float(self.subtotal)
        }

    def __repr__(self):
        return f'<ReservationRoom Res:{self.reservation_id} Room:{self.room_id}>'


class ReservationStatusHistory(db.Model):
    """Audit log tracking reservation status progression over time."""
    __tablename__ = 'reservation_status_history'

    id = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservations.id', ondelete='CASCADE'), nullable=False, index=True)
    previous_status = db.Column(db.String(20), nullable=True)
    new_status = db.Column(db.String(20), nullable=False)
    changed_by_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    reason = db.Column(db.String(255), nullable=True)
    request_source = db.Column(db.String(20), nullable=True)
    requested_by_guest_id = db.Column(db.Integer, db.ForeignKey('guests.id', ondelete='SET NULL'), nullable=True, index=True)
    cancellation_fee = db.Column(db.Numeric(10, 2), nullable=True)
    refund_status = db.Column(db.String(30), nullable=True)
    changed_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    reservation = db.relationship('Reservation', back_populates='status_history')
    changed_by = db.relationship('User')
    requested_by_guest = db.relationship('Guest')

    def __repr__(self):
        return f'<StatusHistory Res:{self.reservation_id} {self.previous_status}->{self.new_status}>'
