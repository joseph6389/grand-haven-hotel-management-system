from decimal import Decimal
from app.extensions import db
from app.utils.datetime_utils import utcnow


# Association table for normalized Many-to-Many relationship between Rooms and Amenities
room_amenities = db.Table(
    'room_amenities',
    db.Column('room_id', db.Integer, db.ForeignKey('rooms.id', ondelete='CASCADE'), primary_key=True),
    db.Column('amenity_id', db.Integer, db.ForeignKey('amenities.id', ondelete='CASCADE'), primary_key=True)
)


class Amenity(db.Model):
    """Amenity entity for hotel features (e.g., Ocean View, High-Speed Wi-Fi, Jacuzzi)."""
    __tablename__ = 'amenities'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False, index=True)
    icon = db.Column(db.String(50), nullable=True, default='bi-check-circle')  # Bootstrap Icon name
    category = db.Column(db.String(50), nullable=True, default='General')  # e.g., Bathroom, Comfort, View

    rooms = db.relationship('Room', secondary=room_amenities, back_populates='amenities')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'icon': self.icon,
            'category': self.category
        }

    def __repr__(self):
        return f'<Amenity {self.name}>'


class RoomType(db.Model):
    """Room category classification with base pricing, capacity, and bed configuration."""
    __tablename__ = 'room_types'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)  # e.g., 'STD', 'DLX', 'STE', 'PRE'
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    base_price = db.Column(db.Numeric(10, 2), nullable=False)  # Decimal-safe monetary representation
    default_capacity = db.Column(db.Integer, nullable=False, default=2)
    max_capacity = db.Column(db.Integer, nullable=False, default=4)
    bed_type = db.Column(db.String(80), nullable=False, default='1 King Bed')  # e.g., '1 King Bed', '2 Queen Beds'
    image_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    rooms = db.relationship('Room', back_populates='room_type', lazy='dynamic')

    @property
    def formatted_base_price(self) -> str:
        return f"₹{float(self.base_price):,.2f}"

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'base_price': float(self.base_price),
            'formatted_base_price': self.formatted_base_price,
            'default_capacity': self.default_capacity,
            'max_capacity': self.max_capacity,
            'bed_type': self.bed_type,
            'image_url': self.image_url,
            'room_count': self.rooms.count()
        }

    def __repr__(self):
        return f'<RoomType {self.code} - {self.name}>'


class Room(db.Model):
    """Physical hotel room unit."""
    __tablename__ = 'rooms'

    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    room_type_id = db.Column(db.Integer, db.ForeignKey('room_types.id', ondelete='RESTRICT'), nullable=False, index=True)
    floor = db.Column(db.Integer, nullable=False, default=1)
    capacity = db.Column(db.Integer, nullable=False, default=2)
    operational_status = db.Column(
        db.Enum('operational', 'maintenance', 'out_of_order',
                name='room_operational_status', native_enum=True),
        nullable=False,
        default='operational',
        index=True
    )  # 'operational', 'maintenance', 'out_of_order'
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    room_type = db.relationship('RoomType', back_populates='rooms')
    amenities = db.relationship('Amenity', secondary=room_amenities, back_populates='rooms')
    reservation_allocations = db.relationship('ReservationRoom', back_populates='room', lazy='dynamic')

    @property
    def price_per_night(self) -> Decimal:
        """Inherited base price from the associated room type."""
        return self.room_type.base_price if self.room_type else Decimal('0.00')

    @property
    def formatted_price(self) -> str:
        return f"₹{float(self.price_per_night):,.2f}"

    @property
    def is_operational(self) -> bool:
        return self.is_active and self.operational_status == 'operational'

    def to_dict(self):
        return {
            'id': self.id,
            'room_number': self.room_number,
            'room_type_id': self.room_type_id,
            'room_type_name': self.room_type.name if self.room_type else None,
            'room_type_code': self.room_type.code if self.room_type else None,
            'floor': self.floor,
            'capacity': self.capacity,
            'price_per_night': float(self.price_per_night),
            'formatted_price': self.formatted_price,
            'bed_type': self.room_type.bed_type if self.room_type else None,
            'operational_status': self.operational_status,
            'is_active': self.is_active,
            'is_operational': self.is_operational,
            'image_url': self.room_type.image_url if self.room_type else None,
            'amenities': [a.to_dict() for a in self.amenities],
            'notes': self.notes
        }

    def __repr__(self):
        return f'<Room {self.room_number} ({self.operational_status})>'
