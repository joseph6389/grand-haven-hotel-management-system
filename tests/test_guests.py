
from app.models.guest import Guest


def test_guests_directory_and_crud(client, auth):
    """Test guest listing, search, creation, and duplicate email prevention."""
    auth.login()

    # View guest directory
    res = client.get('/guests')
    assert res.status_code == 200

    # Add new guest
    create_res = client.post('/guests/create', data={
        'first_name': 'Priya',
        'last_name': 'Nair',
        'email': 'priya.test@example.com',
        'phone': '+91 98765 43212',
        'city': 'Bengaluru',
        'country': 'India'
    }, follow_redirects=True)

    assert create_res.status_code == 200
    assert b"registered successfully" in create_res.data

    guest = Guest.query.filter_by(
        email='priya.test@example.com'
    ).first()
    assert guest is not None

    # Duplicate email rejection
    dup_res = client.post('/guests/create', data={
        'first_name': 'Duplicate',
        'last_name': 'Guest',
        'email': 'priya.test@example.com',
        'phone': '+91 98765 43213'
    }, follow_redirects=True)

    assert b"already exists" in dup_res.data

    # Search guest
    search_res = client.get('/guests?search=Priya')
    assert search_res.status_code == 200
    assert b"Priya Nair" in search_res.data
