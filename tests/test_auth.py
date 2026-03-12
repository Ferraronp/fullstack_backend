from tests.conftest import register_and_login


def test_register_user(client):
    response = client.post(
        "/auth/register",
        json={"username": "testuser", "password": "test123", "currency": "$"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert "id" in data


def test_register_duplicate_username(client):
    client.post("/auth/register", json={"username": "dupuser", "password": "test123"})
    response = client.post("/auth/register", json={"username": "dupuser", "password": "test123"})
    assert response.status_code == 400


def test_login_returns_both_tokens(client):
    client.post("/auth/register", json={"username": "loginuser", "password": "test123"})
    response = client.post("/auth/login", data={"username": "loginuser", "password": "test123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client):
    response = client.post("/auth/login", data={"username": "nobody", "password": "wrong"})
    assert response.status_code == 401


def test_get_current_user(client):
    tokens = register_and_login(client, "meuser")
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert response.status_code == 200
    assert response.json()["username"] == "meuser"


def test_get_current_user_without_token(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_refresh_token_returns_new_tokens(client):
    tokens = register_and_login(client, "refreshuser")
    response = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    # новый refresh token должен отличаться от старого (ротация)
    assert data["refresh_token"] != tokens["refresh_token"]


def test_refresh_token_rotation_invalidates_old(client):
    tokens = register_and_login(client, "rotateuser")
    client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    # повторное использование старого токена должно вернуть 401
    response = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 401


def test_invalid_refresh_token(client):
    response = client.post("/auth/refresh", json={"refresh_token": "fake_token"})
    assert response.status_code == 401


def test_logout(client):
    tokens = register_and_login(client, "logoutuser")
    response = client.post(
        "/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert response.status_code == 200


def test_logout_blocks_refresh(client):
    tokens = register_and_login(client, "logoutrefresh")
    client.post(
        "/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    response = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 401


def test_logout_blocks_access_token(client):
    tokens = register_and_login(client, "logoutaccess")
    client.post(
        "/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert response.status_code == 401
