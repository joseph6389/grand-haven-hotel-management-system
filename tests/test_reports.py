from app.services.report_service import (
    get_dashboard_kpis,
    get_monthly_revenue_trend,
    get_reservation_status_distribution,
    get_room_type_performance
)


def test_reports_and_csv_export(client, auth):
    """Test reporting services and streaming CSV exports."""
    auth.login()

    # Reports page loads
    res = client.get('/reports')
    assert res.status_code == 200
    assert b"Financial & Occupancy Reports" in res.data
    assert b"Room Classification Performance" in res.data

    # Export Reservations CSV
    csv_res = client.get('/reports/export-csv?type=reservations')
    assert csv_res.status_code == 200
    assert csv_res.mimetype == 'text/csv'
    assert b"Confirmation #" in csv_res.data

    # Export Payments CSV
    csv_pay_res = client.get('/reports/export-csv?type=payments')
    assert csv_pay_res.status_code == 200
    assert csv_pay_res.mimetype == 'text/csv'
    assert b"Payment Reference" in csv_pay_res.data


def test_dashboard_api_stats(client, auth):
    """Test JSON endpoints for Chart.js and widgets."""
    auth.login()

    stats_res = client.get('/api/dashboard/stats')
    assert stats_res.status_code == 200
    json_data = stats_res.get_json()
    assert 'total_rooms' in json_data
    assert 'available_rooms' in json_data
    assert 'occupancy_rate' in json_data

    rev_res = client.get('/api/dashboard/revenue-trend')
    assert rev_res.status_code == 200
    assert 'labels' in rev_res.get_json()
    assert 'data' in rev_res.get_json()
