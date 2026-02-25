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


def test_register_user(client):
    response = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "test123", "currency": "$"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["currency"] == "$"
    assert "id" in data


def test_register_duplicate_email(client):
    client.post(
        "/auth/register",
        json={"email": "duplicate@example.com", "password": "test123"}
    )
    response = client.post(
        "/auth/register",
        json={"email": "duplicate@example.com", "password": "test123"}
    )
    assert response.status_code == 400


def test_login_user(client):
    client.post(
        "/auth/register",
        json={"email": "login@example.com", "password": "test123"}
    )
    response = client.post(
        "/auth/login",
        json={"email": "login@example.com", "password": "test123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client):
    response = client.post(
        "/auth/login",
        json={"email": "nonexistent@example.com", "password": "wrongpass"}
    )
    assert response.status_code == 401


def test_get_current_user(client):
    register_response = client.post(
        "/auth/register",
        json={"email": "current@example.com", "password": "test123"}
    )
    login_response = client.post(
        "/auth/login",
        json={"email": "current@example.com", "password": "test123"}
    )
    token = login_response.json()["access_token"]
    
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "current@example.com"


def test_get_current_user_without_token(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_logout_user(client):
    register_response = client.post(
        "/auth/register",
        json={"email": "logout@example.com", "password": "test123"}
    )
    login_response = client.post(
        "/auth/login",
        json={"email": "logout@example.com", "password": "test123"}
    )
    token = login_response.json()["access_token"]
    
    response = client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    # API возвращает пустой ответ при логауте, поэтому проверяем только статус код


def test_logout_twice(client):
    register_response = client.post(
        "/auth/register",
        json={"email": "logout2@example.com", "password": "test123"}
    )
    login_response = client.post(
        "/auth/login",
        json={"email": "logout2@example.com", "password": "test123"}
    )
    token = login_response.json()["access_token"]
    
    # Первый logout
    response1 = client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response1.status_code == 200
    
    # Второй logout - должен вернуть 401, так как токен отозван
    response2 = client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response2.status_code == 401