from app.extensions import db
from app.utils.datetime_utils import utcnow, india_datetime_iso


class AuditLog(db.Model):
    """System-wide audit trail for sensitive hotel operations and compliance."""
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    action = db.Column(db.String(50), nullable=False, index=True)  # e.g., 'CREATE_RESERVATION', 'CHECK_IN'
    entity_type = db.Column(db.String(50), nullable=False, index=True)  # e.g., 'Reservation', 'Room', 'Payment'
    entity_id = db.Column(db.String(50), nullable=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    timestamp = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)

    user = db.relationship('User', back_populates='audit_logs')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else 'System / Guest Self-Booking',
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'details': self.details,
            'ip_address': self.ip_address,
            'timestamp': india_datetime_iso(self.timestamp)
        }

    def __repr__(self):
        return f'<AuditLog {self.action} on {self.entity_type}:{self.entity_id} at {self.timestamp}>'
