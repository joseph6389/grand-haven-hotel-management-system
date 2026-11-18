from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login_manager
from app.utils.datetime_utils import utcnow, india_datetime_iso


class Role(db.Model):
    """User security and permission role."""
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    users = db.relationship('User', back_populates='role', lazy='dynamic')

    def __repr__(self):
        return f'<Role {self.name}>'


class User(UserMixin, db.Model):
    """Staff user entity for hotel staff and administrators."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id', ondelete='RESTRICT'), nullable=False)
    guest_profile_id = db.Column(
        db.Integer, db.ForeignKey('guests.id', ondelete='SET NULL'),
        unique=True, nullable=True, index=True
    )
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    role = db.relationship('Role', back_populates='users')
    guest_profile = db.relationship('Guest', back_populates='user', uselist=False)
    reservations_created = db.relationship('Reservation', back_populates='created_by', foreign_keys='Reservation.created_by_id', lazy='dynamic')
    audit_logs = db.relationship('AuditLog', back_populates='user', lazy='dynamic')

    def set_password(self, password: str):
        """Hash and store the password using Werkzeug's secure hashing."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify the password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self) -> bool:
        return bool(self.role and self.role.name.lower() == 'admin')

    @property
    def is_receptionist(self) -> bool:
        return bool(self.role and self.role.name.lower() in ('receptionist', 'admin'))

    @property
    def is_guest(self) -> bool:
        return bool(self.role and self.role.name.lower() == 'guest' and self.guest_profile_id)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'phone': self.phone,
            'role': self.role.name if self.role else None,
            'is_active': self.is_active,
            'last_login': india_datetime_iso(self.last_login),
            'created_at': india_datetime_iso(self.created_at)
        }

    def __repr__(self):
        return f'<User {self.username} ({self.role.name if self.role else "No Role"})>'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
