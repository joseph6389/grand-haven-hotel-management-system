from app.models.setting import HotelSetting


def test_admin_settings_rejects_invalid_tax_and_contact_data(app, client, auth):
    auth.login('admin_test', 'AdminTest@123')
    response = client.post('/admin/settings', data={
        'hotel_name': 'Grand Haven Hotel',
        'hotel_email': 'reservations@example.com',
        'hotel_phone': '+1 555 0100',
        'hotel_currency': 'USD',
        'hotel_tax_rate': 'NaN',
        'default_checkin_time': '15:00',
        'default_checkout_time': '11:00',
        'cancellation_policy': 'Contact reception for cancellation details.',
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Review the hotel name' in response.data
    with app.app_context():
        assert HotelSetting.get_val('HOTEL_CURRENCY') is None


def test_admin_settings_accepts_inr_and_optional_unset_phone(app, client, auth):
    auth.login('admin_test', 'AdminTest@123')
    response = client.post('/admin/settings', data={
        'hotel_name': 'Grand Haven Hotel',
        'hotel_email': 'reservations@example.com',
        'hotel_phone': '',
        'hotel_currency': 'USD',
        'hotel_tax_rate': '0.12',
        'default_checkin_time': '15:00',
        'default_checkout_time': '11:00',
        'cancellation_policy': 'Contact reception for cancellation details.',
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'settings updated successfully' in response.data
    with app.app_context():
        assert HotelSetting.get_val('HOTEL_CURRENCY') == 'INR'
        assert HotelSetting.get_val('HOTEL_PHONE') == ''
