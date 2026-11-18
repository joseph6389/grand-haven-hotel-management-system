
def test_api_patch_rejects_missing_csrf_token(app, client):
    """Unsafe API requests must be rejected when CSRF protection is enabled."""
    app.config["WTF_CSRF_ENABLED"] = True

    response = client.patch("/api/reservations/1/check-in")

    assert response.status_code == 400
    assert b"The CSRF token is missing." in response.data

def test_api_patch_accepts_valid_csrf_token(app, client):
    """A valid CSRF token should pass CSRF validation."""
    import re

    app.config["WTF_CSRF_ENABLED"] = True

    login_page = client.get("/login")
    assert login_page.status_code == 200

    match = re.search(
        rb'name="csrf_token"\s+value="([^"]+)"',
        login_page.data,
    )
    assert match is not None, "Login page must provide a CSRF token"

    token = match.group(1).decode()

    response = client.patch(
        "/api/reservations/1/check-in",
        headers={"X-CSRFToken": token},
    )

    # CSRF validation should pass; login protection may redirect
    # this unauthenticated request to the login page.
    assert response.status_code != 400
