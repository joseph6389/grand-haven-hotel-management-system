from app.extensions import db
from app.utils.datetime_utils import utcnow, india_datetime_iso


class Guest(db.Model):
    """Guest profile entity."""
    __tablename__ = 'guests'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(60), nullable=False, index=True)
    last_name = db.Column(db.String(60), nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(30), nullable=False, index=True)
    address = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    postal_code = db.Column(db.String(20), nullable=True)
    country = db.Column(db.String(100), nullable=True, default='India', server_default='India')
    identification_type = db.Column(db.String(50), nullable=True)  # Passport, National ID, Driver's License
    identification_number = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    reservations = db.relationship('Reservation', back_populates='guest', lazy='dynamic', cascade='all, delete-orphan')
    user = db.relationship('User', back_populates='guest_profile', uselist=False)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def total_bookings(self) -> int:
        return self.reservations.count()

    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'city': self.city,
            'country': self.country,
            'identification_type': self.identification_type,
            'identification_number': self.identification_number,
            'total_bookings': self.total_bookings,
            'created_at': india_datetime_iso(self.created_at)
        }

    def __repr__(self):
        return f'<Guest {self.full_name} ({self.email})>'
