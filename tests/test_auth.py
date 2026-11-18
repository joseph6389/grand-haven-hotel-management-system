def test_homepage_loads(client):
    """Test public homepage loads successfully."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Grand Haven Hotel" in response.data
    assert b"Where Coastal Elegance" in response.data


def test_login_page_renders(client):
    """Test login page loads."""
    response = client.get('/login')
    assert response.status_code == 200
    assert b"Log in to your account" in response.data
    assert b"admin / Admin@123" in response.data


def test_login_success_and_logout(client, auth):
    """Test successful authentication and session termination."""
    response = auth.login('admin_test', 'AdminTest@123')
    assert response.status_code == 200
    assert b"Executive Management Dashboard" in response.data
    assert b"admin_test" in response.data

    logout_response = auth.logout()
    assert logout_response.status_code == 200
    assert b"Log in to your account" in logout_response.data


def test_login_invalid_credentials(client, auth):
    """Test rejection on bad password."""
    response = auth.login('admin_test', 'WrongPassword!')
    assert b"Invalid username or password" in response.data


def test_login_inactive_user_rejected(client, auth):
    """Test that deactivated accounts cannot log in."""
    response = auth.login('inactive_test', 'Inactive@123')
    assert b"This staff account has been deactivated" in response.data


def test_unauthorized_redirect(client):
    """Test that protected routes redirect unauthenticated users to login."""
    response = client.get('/dashboard', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers['Location']



def test_login_rejects_external_next_redirect(client):
    """Ensure login rejects external redirect destinations."""
    response = client.post(
        '/login?next=%2F%2Fexample.com',
        data={
            'username': 'admin_test',
            'password': 'AdminTest@123'
        },
        follow_redirects=False
    )

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/dashboard')
    assert not response.headers['Location'].startswith('//')
    assert 'example.com' not in response.headers['Location']
