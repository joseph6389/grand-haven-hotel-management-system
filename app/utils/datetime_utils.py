"""UTC clock helpers matching the application's timezone-naive MySQL columns."""

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

try:
    INDIA_TZ = ZoneInfo('Asia/Kolkata')
except ZoneInfoNotFoundError:  # Windows Python may not ship the IANA database.
    # India has no daylight-saving transitions; retain the IANA identity in config
    # while using its fixed +05:30 offset when optional tzdata is unavailable.
    INDIA_TZ = timezone(timedelta(hours=5, minutes=30), name='Asia/Kolkata')


def utcnow() -> datetime:
    """Return the current UTC instant as a naive datetime for DATETIME columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def utcdate() -> date:
    """Return today's date in UTC, evaluated each time the default is used."""
    return datetime.now(timezone.utc).date()


def india_now() -> datetime:
    """Return the current aware India-local datetime for display/business defaults."""
    return datetime.now(INDIA_TZ)


def india_today() -> date:
    """Return the current date in the hotel's operating timezone."""
    return india_now().date()


def as_india_time(value: datetime | None) -> datetime | None:
    """Interpret stored naive datetimes as UTC, then convert to Asia/Kolkata."""
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(INDIA_TZ)


def india_local_to_utc_naive(value: datetime) -> datetime:
    """Convert an India-local boundary to naive UTC for legacy DATETIME queries."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=INDIA_TZ)
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def format_india_datetime(value: datetime | None, fmt: str = '%d/%m/%Y %H:%M') -> str:
    local_value = as_india_time(value)
    return local_value.strftime(fmt) if local_value else ''


def india_datetime_iso(value: datetime | None) -> str | None:
    """Return a timezone-aware ISO-8601 timestamp for API serialization."""
    local_value = as_india_time(value)
    return local_value.isoformat(timespec='seconds') if local_value else None


def format_india_date(value: date | None, fmt: str = '%d/%m/%Y') -> str:
    return value.strftime(fmt) if value else ''
