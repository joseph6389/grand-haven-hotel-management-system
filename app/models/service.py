from decimal import Decimal
from sqlalchemy.ext.hybrid import hybrid_property
from app.extensions import db
from app.utils.datetime_utils import utcdate, utcnow


class Service(db.Model):
    """Hotel extra services available to guests (e.g., Airport Transfer, Spa, Buffet)."""
    __tablename__ = 'services'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255), nullable=True)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal('0.00'))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    reservation_services = db.relationship('ReservationService', back_populates='service', lazy='dynamic')

    @property
    def formatted_price(self) -> str:
        return f"₹{float(self.unit_price):,.2f}"

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'unit_price': float(self.unit_price),
            'formatted_price': self.formatted_price,
            'is_active': self.is_active
        }

    def __repr__(self):
        return f'<Service {self.name}: ₹{self.unit_price}>'


class ReservationService(db.Model):
    """Line item for an extra service consumed during a reservation."""
    __tablename__ = 'reservation_services'

    id = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservations.id', ondelete='CASCADE'), nullable=False, index=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id', ondelete='RESTRICT'), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    service_date = db.Column(db.Date, nullable=False, default=utcdate)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    reservation = db.relationship('Reservation', back_populates='services')
    service = db.relationship('Service', back_populates='reservation_services')

    @hybrid_property
    def total_price(self) -> Decimal:
        return (Decimal(int(self.quantity or 0)) * Decimal(str(self.unit_price or 0))).quantize(Decimal('0.01'))

    @total_price.expression
    def total_price(cls):
        return cls.quantity * cls.unit_price

    def to_dict(self):
        return {
            'id': self.id,
            'reservation_id': self.reservation_id,
            'service_id': self.service_id,
            'service_name': self.service.name if self.service else 'Service',
            'quantity': self.quantity,
            'unit_price': float(self.unit_price),
            'total_price': float(self.total_price),
            'service_date': self.service_date.isoformat()
        }

    def __repr__(self):
        return f'<ReservationService Res:{self.reservation_id} Svc:{self.service_id} x{self.quantity}>'
