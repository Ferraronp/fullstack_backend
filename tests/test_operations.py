import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.database import Base, get_db
from main import app
import os
from dotenv import load_dotenv
from datetime import date, timedelta

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


def create_test_category(client, token, name="Food", color="#FF0000"):
    """Создает тестовую категорию и возвращает ее ID"""
    response = client.post(
        "/categories/",
        json={"name": name, "color": color},
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.json()["id"]


def test_create_operation(client):
    token = create_test_user(client)
    category_id = create_test_category(client, token)
    
    response = client.post(
        "/operations/",
        json={
            "date": str(date.today()),
            "amount": 100.50,
            "comment": "Test operation",
            "category_id": category_id
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == 100.50
    assert data["comment"] == "Test operation"
    assert data["category_id"] == category_id
    assert "id" in data


def test_create_operation_without_comment(client):
    token = create_test_user(client)
    category_id = create_test_category(client, token)
    
    response = client.post(
        "/operations/",
        json={
            "date": str(date.today()),
            "amount": 50.25,
            "category_id": category_id
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == 50.25
    assert data["comment"] is None


def test_get_operations(client):
    token = create_test_user(client)
    category_id = create_test_category(client, token)
    
    # Создаем несколько операций
    client.post(
        "/operations/",
        json={
            "date": str(date.today()),
            "amount": 100.00,
            "category_id": category_id
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    client.post(
        "/operations/",
        json={
            "date": str(date.today() - timedelta(days=1)),
            "amount": 50.00,
            "category_id": category_id
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    response = client.get(
        "/operations/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_operations_with_date_filter(client):
    token = create_test_user(client)
    category_id = create_test_category(client, token)
    
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    # Создаем операции за разные даты
    client.post(
        "/operations/",
        json={
            "date": str(today),
            "amount": 100.00,
            "category_id": category_id
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    client.post(
        "/operations/",
        json={
            "date": str(yesterday),
            "amount": 50.00,
            "category_id": category_id
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Запрашиваем только сегодняшние операции
    response = client.get(
        f"/operations/?start_date={today}&end_date={today}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["amount"] == 100.00


def test_get_operation_by_id(client):
    token = create_test_user(client)
    category_id = create_test_category(client, token)
    
    create_response = client.post(
        "/operations/",
        json={
            "date": str(date.today()),
            "amount": 75.50,
            "comment": "Test operation",
            "category_id": category_id
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    operation_id = create_response.json()["id"]
    
    response = client.get(
        f"/operations/{operation_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == 75.50
    assert data["comment"] == "Test operation"


def test_update_operation(client):
    token = create_test_user(client)
    category_id = create_test_category(client, token)
    
    create_response = client.post(
        "/operations/",
        json={
            "date": str(date.today()),
            "amount": 50.00,
            "comment": "Original comment",
            "category_id": category_id
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    operation_id = create_response.json()["id"]
    
    response = client.put(
        f"/operations/{operation_id}",
        json={
            "date": str(date.today()),
            "amount": 75.00,
            "comment": "Updated comment",
            "category_id": category_id
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == 75.00
    assert data["comment"] == "Updated comment"


def test_delete_operation(client):
    token = create_test_user(client)
    category_id = create_test_category(client, token)
    
    create_response = client.post(
        "/operations/",
        json={
            "date": str(date.today()),
            "amount": 100.00,
            "category_id": category_id
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    operation_id = create_response.json()["id"]
    
    response = client.delete(
        f"/operations/{operation_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

def test_get_total_balance(client):
    token = create_test_user(client)
    category_id = create_test_category(client, token)
    
    # Создаем несколько операций с разными суммами
    client.post(
        "/operations/",
        json={
            "date": str(date.today()),
            "amount": 100.00,
            "category_id": category_id
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    client.post(
        "/operations/",
        json={
            "date": str(date.today()),
            "amount": 50.00,
            "category_id": category_id
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    response = client.get(
        "/operations/balance/total",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["balance"] == 150.00
    assert data["currency"] == "$"


def test_access_operations_without_auth(client):
    response = client.get("/operations/")
    assert response.status_code == 401


def test_create_operation_without_auth(client):
    response = client.post(
        "/operations/",
        json={
            "date": str(date.today()),
            "amount": 100.00,
            "category_id": 1
        }
    )
    assert response.status_code == 401


def test_get_nonexistent_operation(client):
    token = create_test_user(client)
    response = client.get(
        "/operations/999",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404