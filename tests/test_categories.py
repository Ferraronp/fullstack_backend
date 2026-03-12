from tests.conftest import register_and_login


def test_create_category(client):
    token = register_and_login(client, "catuser")
    response = client.post(
        "/categories/",
        json={"name": "Food", "color": "#FF0000"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Food"
    assert data["color"] == "#FF0000"
    assert "id" in data


def test_create_category_without_color(client):
    token = register_and_login(client, "catuser2")
    response = client.post(
        "/categories/",
        json={"name": "Transport"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Transport"
    assert data["color"] is None


def test_create_duplicate_category(client):
    token = register_and_login(client, "catuser3")
    client.post("/categories/", json={"name": "Food", "color": "#FF0000"}, headers={"Authorization": f"Bearer {token}"})
    response = client.post("/categories/", json={"name": "Food", "color": "#00FF00"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 400


def test_get_categories(client):
    token = register_and_login(client, "catuser4")
    client.post("/categories/", json={"name": "Food", "color": "#FF0000"}, headers={"Authorization": f"Bearer {token}"})
    client.post("/categories/", json={"name": "Transport"}, headers={"Authorization": f"Bearer {token}"})

    response = client.get("/categories/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_category_by_id(client):
    token = register_and_login(client, "catuser5")
    create_response = client.post(
        "/categories/",
        json={"name": "Food", "color": "#FF0000"},
        headers={"Authorization": f"Bearer {token}"}
    )
    category_id = create_response.json()["id"]

    response = client.get(f"/categories/{category_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Food"
    assert data["color"] == "#FF0000"


def test_get_nonexistent_category(client):
    token = register_and_login(client, "catuser6")
    response = client.get("/categories/999", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404


def test_update_category(client):
    token = register_and_login(client, "catuser7")
    create_response = client.post(
        "/categories/",
        json={"name": "Food", "color": "#FF0000"},
        headers={"Authorization": f"Bearer {token}"}
    )
    category_id = create_response.json()["id"]

    response = client.put(
        f"/categories/{category_id}",
        json={"name": "Groceries", "color": "#00FF00"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Groceries"
    assert data["color"] == "#00FF00"


def test_delete_category(client):
    token = register_and_login(client, "catuser8")
    create_response = client.post(
        "/categories/",
        json={"name": "Food", "color": "#FF0000"},
        headers={"Authorization": f"Bearer {token}"}
    )
    category_id = create_response.json()["id"]

    response = client.delete(f"/categories/{category_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


def test_access_categories_without_auth(client):
    response = client.get("/categories/")
    assert response.status_code == 401


def test_create_category_without_auth(client):
    response = client.post("/categories/", json={"name": "Food", "color": "#FF0000"})
    assert response.status_code == 401
