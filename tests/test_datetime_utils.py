from datetime import date, datetime, timezone

from app.models.service import ReservationService
from app.utils.datetime_utils import india_today, india_local_to_utc_naive, india_datetime_iso, format_india_date, format_india_datetime, utcdate, utcnow


def test_utcnow_returns_timezone_naive_utc():
    value = utcnow()

    assert value.tzinfo is None
    expected = datetime.now(timezone.utc).replace(tzinfo=None)
    assert abs((expected - value).total_seconds()) < 2


def test_utcdate_returns_a_date():
    assert isinstance(utcdate(), date)


def test_india_formatting_uses_day_first_and_converts_utc_timestamp():
    assert format_india_date(date(2026, 10, 26)) == '26/10/2026'
    assert format_india_datetime(datetime(2026, 10, 25, 18, 30)) == '26/10/2026 00:00'
    assert isinstance(india_today(), date)
    assert india_local_to_utc_naive(datetime(2026, 3, 1)) == datetime(2026, 2, 28, 18, 30)
    assert india_datetime_iso(datetime(2026, 10, 25, 18, 30)) == '2026-10-26T00:00:00+05:30'


def test_service_date_default_is_evaluated_at_insert_time():
    assert callable(ReservationService.__table__.c.service_date.default.arg)
