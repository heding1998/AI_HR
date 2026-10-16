from app.config import settings


def _login(client, username: str, password: str):
    return client.post("/api/auth/login", json={"username": username, "password": password})


def test_login_success_returns_token(client):
    resp = _login(client, settings.admin_username, settings.admin_password)
    assert resp.status_code == 200
    data = resp.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]


def test_login_wrong_password_returns_401(client):
    resp = _login(client, settings.admin_username, "wrong-password")
    assert resp.status_code == 401


def test_login_unknown_user_returns_401(client):
    resp = _login(client, "no-such-user", "whatever")
    assert resp.status_code == 401


def test_me_without_token_returns_401(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_with_valid_token_returns_user(client):
    login = _login(client, settings.admin_username, settings.admin_password).json()
    resp = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {login['access_token']}"}
    )
    assert resp.status_code == 200
    assert resp.json()["username"] == settings.admin_username
