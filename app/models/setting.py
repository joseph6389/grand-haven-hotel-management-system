from app.extensions import db
from app.utils.datetime_utils import utcnow, india_datetime_iso


class HotelSetting(db.Model):
    """Dynamic key-value settings store for property configuration."""
    __tablename__ = 'hotel_settings'

    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(50), unique=True, nullable=False, index=True)
    setting_value = db.Column(db.Text, nullable=False)
    setting_type = db.Column(db.String(20), nullable=False, default='string')  # 'string', 'int', 'float', 'bool'
    description = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    @classmethod
    def get_val(cls, key: str, default=None):
        record = cls.query.filter_by(setting_key=key).first()
        if not record:
            return default
        if record.setting_type == 'int':
            return int(record.setting_value)
        elif record.setting_type == 'float':
            return float(record.setting_value)
        elif record.setting_type == 'bool':
            return record.setting_value.lower() in ('true', '1', 'yes')
        return record.setting_value

    @classmethod
    def set_val(cls, key: str, value, val_type='string', description=None):
        record = cls.query.filter_by(setting_key=key).first()
        if not record:
            record = cls(setting_key=key, setting_value=str(value), setting_type=val_type, description=description)
            db.session.add(record)
        else:
            record.setting_value = str(value)
            record.setting_type = val_type
            if description:
                record.description = description
        return record

    def to_dict(self):
        return {
            'key': self.setting_key,
            'value': self.setting_value,
            'type': self.setting_type,
            'description': self.description,
            'updated_at': india_datetime_iso(self.updated_at)
        }

    def __repr__(self):
        return f'<HotelSetting {self.setting_key}={self.setting_value}>'
