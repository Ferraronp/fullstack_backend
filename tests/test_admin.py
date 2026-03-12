from tests.conftest import register_and_login


def test_admin_can_list_users(client):
    admin_tokens = register_and_login(client, "adminuser", role="admin")
    register_and_login(client, "regularuser")

    response = client.get("/admin/users", headers={"Authorization": f"Bearer {admin_tokens['access_token']}"})
    assert response.status_code == 200
    usernames = [u["username"] for u in response.json()]
    assert "adminuser" in usernames
    assert "regularuser" in usernames


def test_regular_user_cannot_list_users(client):
    user_tokens = register_and_login(client, "regularuser")
    response = client.get("/admin/users", headers={"Authorization": f"Bearer {user_tokens['access_token']}"})
    assert response.status_code == 403


def test_unauthenticated_cannot_list_users(client):
    response = client.get("/admin/users")
    assert response.status_code == 401


def test_admin_can_change_user_role(client):
    admin_tokens = register_and_login(client, "adminuser", role="admin")
    register_and_login(client, "targetuser")

    users = client.get("/admin/users", headers={"Authorization": f"Bearer {admin_tokens['access_token']}"}).json()
    target = next(u for u in users if u["username"] == "targetuser")

    response = client.put(
        f"/admin/users/{target['id']}/role",
        json={"role": "admin"},
        headers={"Authorization": f"Bearer {admin_tokens['access_token']}"}
    )
    assert response.status_code == 200
    assert response.json()["role"] == "admin"


def test_admin_cannot_set_invalid_role(client):
    admin_tokens = register_and_login(client, "adminuser", role="admin")
    register_and_login(client, "targetuser")

    users = client.get("/admin/users", headers={"Authorization": f"Bearer {admin_tokens['access_token']}"}).json()
    target = next(u for u in users if u["username"] == "targetuser")

    response = client.put(
        f"/admin/users/{target['id']}/role",
        json={"role": "superuser"},
        headers={"Authorization": f"Bearer {admin_tokens['access_token']}"}
    )
    assert response.status_code == 400


def test_admin_change_role_nonexistent_user(client):
    admin_tokens = register_and_login(client, "adminuser", role="admin")
    response = client.put("/admin/users/999/role", json={"role": "admin"}, headers={"Authorization": f"Bearer {admin_tokens['access_token']}"})
    assert response.status_code == 404


def test_regular_user_cannot_change_role(client):
    user_tokens = register_and_login(client, "regularuser")
    response = client.put("/admin/users/1/role", json={"role": "admin"}, headers={"Authorization": f"Bearer {user_tokens['access_token']}"})
    assert response.status_code == 403
