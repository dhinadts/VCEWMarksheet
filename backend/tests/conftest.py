import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["SECRET_KEY"] = "test-secret-key-that-is-long-enough-for-tests"
os.environ["DEMO_DEFAULT_PASSWORD"] = "Qwerty@123"
os.environ["DOCUMENT_STORAGE_BACKEND"] = "local"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import create_app
from app.models.models import User
from scripts.seed import seed


@pytest.fixture()
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    seed(session)
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as test_client:
        yield test_client


def login(client, username="ADMIN02"):
    response = client.post("/api/v1/auth/login", json={"username": username, "password": "Qwerty@123"})
    assert response.status_code == 200
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin_headers(client): return login(client)


@pytest.fixture()
def professor_headers(client): return login(client, "PROF01")


@pytest.fixture()
def student_headers(db):
    user = db.query(User).filter(User.username == "VCEW1001").one()
    return {"Authorization": f"Bearer {create_access_token(str(user.id), user.user_type.value)}"}
