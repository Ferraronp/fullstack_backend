import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.database import Base, get_db
from main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_shared.db"

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


def register_and_login(client, username, password="test123", role="user"):
    """Регистрирует пользователя и возвращает токен."""
    client.post(
        "/auth/register",
        json={"username": username, "password": password, "currency": "$", "role": role}
    )
    response = client.post(
        "/auth/login",
        data={"username": username, "password": password}
    )
    return response.json()["access_token"]
