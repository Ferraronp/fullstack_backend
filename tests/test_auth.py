def test_register_user(client):
    response = client.post(
        "/auth/register",
        json={"username": "testuser", "password": "test123", "currency": "$"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["currency"] == "$"
    assert "id" in data


def test_register_duplicate_username(client):
    client.post("/auth/register", json={"username": "duplicateuser", "password": "test123"})
    response = client.post("/auth/register", json={"username": "duplicateuser", "password": "test123"})
    assert response.status_code == 400


def test_login_user(client):
    client.post("/auth/register", json={"username": "loginuser", "password": "test123"})
    response = client.post("/auth/login", data={"username": "loginuser", "password": "test123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client):
    response = client.post("/auth/login", data={"username": "nonexistent", "password": "wrongpass"})
    assert response.status_code == 401


def test_get_current_user(client):
    client.post("/auth/register", json={"username": "currentuser", "password": "test123"})
    login_response = client.post("/auth/login", data={"username": "currentuser", "password": "test123"})
    token = login_response.json()["access_token"]

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["username"] == "currentuser"


def test_get_current_user_without_token(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_logout_user(client):
    client.post("/auth/register", json={"username": "logoutuser", "password": "test123"})
    login_response = client.post("/auth/login", data={"username": "logoutuser", "password": "test123"})
    token = login_response.json()["access_token"]

    response = client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


def test_logout_twice(client):
    client.post("/auth/register", json={"username": "logoutuser2", "password": "test123"})
    login_response = client.post("/auth/login", data={"username": "logoutuser2", "password": "test123"})
    token = login_response.json()["access_token"]

    response1 = client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert response1.status_code == 200

    response2 = client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert response2.status_code == 401
