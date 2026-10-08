def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_register_returns_user_without_password(client):
    res = client.post(
        "/auth/register",
        json={"email": "New@Example.com", "full_name": "New User", "password": "secret123"},
    )
    assert res.status_code == 201
    body = res.json()
    assert body["email"] == "new@example.com"  # stored lower-case
    assert "password" not in body and "hashed_password" not in body


def test_register_duplicate_email_is_rejected(client):
    payload = {"email": "a@example.com", "full_name": "A", "password": "secret123"}
    assert client.post("/auth/register", json=payload).status_code == 201
    res = client.post("/auth/register", json=payload)
    assert res.status_code == 409


def test_register_validates_input(client):
    res = client.post(
        "/auth/register",
        json={"email": "not-an-email", "full_name": "A", "password": "short"},
    )
    assert res.status_code == 422


def test_login_and_me(client, auth_headers):
    res = client.get("/auth/me", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["email"] == "loyiso@example.com"


def test_login_wrong_password(client):
    client.post(
        "/auth/register",
        json={"email": "b@example.com", "full_name": "B", "password": "secret123"},
    )
    res = client.post("/auth/login", data={"username": "b@example.com", "password": "wrongpass"})
    assert res.status_code == 401


def test_protected_route_needs_token(client):
    assert client.get("/auth/me").status_code == 401
    assert client.get("/applications").status_code == 401


def test_invalid_token_is_rejected(client):
    res = client.get("/auth/me", headers={"Authorization": "Bearer not.a.real.token"})
    assert res.status_code == 401
