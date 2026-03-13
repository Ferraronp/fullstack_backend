from datetime import date, timedelta
from tests.conftest import register_and_login


def create_test_category(client, tokens, name="Food", color="#FF0000"):
    response = client.post(
        "/categories/",
        json={"name": name, "color": color},
        headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    return response.json()["id"]


def test_create_operation(client):
    tokens = register_and_login(client, "opuser1")
    category_id = create_test_category(client, tokens)

    response = client.post(
        "/operations/",
        json={"date": str(date.today()), "amount": 100.50, "comment": "Test operation", "category_id": category_id},
        headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == 100.50
    assert data["comment"] == "Test operation"
    assert data["category_id"] == category_id
    assert "id" in data


def test_create_operation_without_comment(client):
    tokens = register_and_login(client, "opuser2")
    category_id = create_test_category(client, tokens)

    response = client.post(
        "/operations/",
        json={"date": str(date.today()), "amount": 50.25, "category_id": category_id},
        headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert response.status_code == 200
    assert response.json()["comment"] is None


def test_get_operations(client):
    tokens = register_and_login(client, "opuser3")
    category_id = create_test_category(client, tokens)

    client.post("/operations/", json={"date": str(date.today()), "amount": 100.00, "category_id": category_id}, headers={"Authorization": f"Bearer {tokens['access_token']}"})
    client.post("/operations/", json={"date": str(date.today() - timedelta(days=1)), "amount": 50.00, "category_id": category_id}, headers={"Authorization": f"Bearer {tokens['access_token']}"})

    response = client.get("/operations/", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert response.status_code == 200
    assert response.json()["total"] == 2


def test_get_operations_with_date_filter(client):
    tokens = register_and_login(client, "opuser4")
    category_id = create_test_category(client, tokens)
    today = date.today()
    yesterday = today - timedelta(days=1)

    client.post("/operations/", json={"date": str(today), "amount": 100.00, "category_id": category_id}, headers={"Authorization": f"Bearer {tokens['access_token']}"})
    client.post("/operations/", json={"date": str(yesterday), "amount": 50.00, "category_id": category_id}, headers={"Authorization": f"Bearer {tokens['access_token']}"})

    response = client.get(f"/operations/?start_date={today}&end_date={today}", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["amount"] == 100.00


def test_get_operation_by_id(client):
    tokens = register_and_login(client, "opuser5")
    category_id = create_test_category(client, tokens)

    create_response = client.post(
        "/operations/",
        json={"date": str(date.today()), "amount": 75.50, "comment": "Test", "category_id": category_id},
        headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    operation_id = create_response.json()["id"]

    response = client.get(f"/operations/{operation_id}", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == 75.50
    assert data["comment"] == "Test"


def test_update_operation(client):
    tokens = register_and_login(client, "opuser6")
    category_id = create_test_category(client, tokens)

    create_response = client.post(
        "/operations/",
        json={"date": str(date.today()), "amount": 50.00, "comment": "Original", "category_id": category_id},
        headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    operation_id = create_response.json()["id"]

    response = client.put(
        f"/operations/{operation_id}",
        json={"date": str(date.today()), "amount": 75.00, "comment": "Updated", "category_id": category_id},
        headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == 75.00
    assert data["comment"] == "Updated"


def test_delete_operation(client):
    tokens = register_and_login(client, "opuser7")
    category_id = create_test_category(client, tokens)

    create_response = client.post(
        "/operations/",
        json={"date": str(date.today()), "amount": 100.00, "category_id": category_id},
        headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    operation_id = create_response.json()["id"]

    response = client.delete(f"/operations/{operation_id}", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert response.status_code == 200


def test_get_total_balance(client):
    tokens = register_and_login(client, "opuser8")
    category_id = create_test_category(client, tokens)

    client.post("/operations/", json={"date": str(date.today()), "amount": 100.00, "category_id": category_id}, headers={"Authorization": f"Bearer {tokens['access_token']}"})
    client.post("/operations/", json={"date": str(date.today()), "amount": 50.00, "category_id": category_id}, headers={"Authorization": f"Bearer {tokens['access_token']}"})

    response = client.get("/operations/balance/total", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert response.status_code == 200
    data = response.json()
    assert data["balance"] == 150.00
    assert data["currency"] == "$"


def test_access_operations_without_auth(client):
    response = client.get("/operations/")
    assert response.status_code == 401


def test_create_operation_without_auth(client):
    response = client.post("/operations/", json={"date": str(date.today()), "amount": 100.00, "category_id": 1})
    assert response.status_code == 401


def test_get_nonexistent_operation(client):
    tokens = register_and_login(client, "opuser9")
    response = client.get("/operations/999", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert response.status_code == 404
