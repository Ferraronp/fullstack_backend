import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.database import Base, get_db
from main import app
import os
from dotenv import load_dotenv

load_dotenv()

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)


def create_test_user(client, email="test@example.com", password="test123"):
    """Создает тестового пользователя и возвращает токен"""
    client.post(
        "/auth/register",
        json={"email": email, "password": password, "currency": "$"}
    )
    response = client.post(
        "/auth/login",
        json={"email": email, "password": password}
    )
    return response.json()["access_token"]


def test_create_category(client):
    token = create_test_user(client)
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
    token = create_test_user(client)
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
    token = create_test_user(client)
    client.post(
        "/categories/",
        json={"name": "Food", "color": "#FF0000"},
        headers={"Authorization": f"Bearer {token}"}
    )
    response = client.post(
        "/categories/",
        json={"name": "Food", "color": "#00FF00"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400


def test_get_categories(client):
    token = create_test_user(client)
    client.post(
        "/categories/",
        json={"name": "Food", "color": "#FF0000"},
        headers={"Authorization": f"Bearer {token}"}
    )
    client.post(
        "/categories/",
        json={"name": "Transport"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    response = client.get(
        "/categories/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Food"
    assert data[1]["name"] == "Transport"


def test_get_category_by_id(client):
    token = create_test_user(client)
    create_response = client.post(
        "/categories/",
        json={"name": "Food", "color": "#FF0000"},
        headers={"Authorization": f"Bearer {token}"}
    )
    category_id = create_response.json()["id"]
    
    response = client.get(
        f"/categories/{category_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Food"
    assert data["color"] == "#FF0000"


def test_get_nonexistent_category(client):
    token = create_test_user(client)
    response = client.get(
        "/categories/999",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


def test_update_category(client):
    token = create_test_user(client)
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
    token = create_test_user(client)
    create_response = client.post(
        "/categories/",
        json={"name": "Food", "color": "#FF0000"},
        headers={"Authorization": f"Bearer {token}"}
    )
    category_id = create_response.json()["id"]
    
    response = client.delete(
        f"/categories/{category_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

def test_access_categories_without_auth(client):
    response = client.get("/categories/")
    assert response.status_code == 401


def test_create_category_without_auth(client):
    response = client.post(
        "/categories/",
        json={"name": "Food", "color": "#FF0000"}
    )
    assert response.status_code == 401