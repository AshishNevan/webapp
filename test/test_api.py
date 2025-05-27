import os
from http import HTTPStatus
import json

from fastapi.testclient import TestClient
import pytest
from sqlmodel import StaticPool, create_engine

from src.db import SQLModel, Session
from src.api import get_db
from main import app
from src.models.user import User

client = TestClient(app)


def override_get_db():
    """
    Override the get_db dependency for testing.
    """
    engine = create_engine("sqlite:///:memory:", echo=True, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine, checkfirst=True)
    local_session = Session(engine)
    yield local_session
    local_session.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def get_user():
    """
    Fixture to create a user for testing.
    """
    return User(email="email@email.com", first_name="test_first_name", last_name="test_last_name", password="supersecretpassword")

def test_healthz_get():
    """
    Test the health check endpoint.
    """
    response = client.get("http://localhost:8000/healthz")
    assert response.status_code == 200

def test_healthz_post():
    """
    Test the health check endpoint with a POST request.
    """
    response = client.post("http://localhost:8000/healthz")
    assert response.status_code ==  405

def test_healthz_put():
    """
    Test the health check endpoint with a PUT request.
    """
    response = client.put("http://localhost:8000/healthz")
    assert response.status_code ==  405

def test_signup(get_user):
    """
    Test the signup endpoint.
    """
    response = client.post(
        "http://localhost:8000/signup/",
        json={
            "email": get_user.email,
            "first_name": get_user.first_name,
            "last_name": get_user.last_name,
            "password": get_user.password
        }
    )
    assert response.status_code == HTTPStatus.CREATED

def test_signup_existing_user(get_user):
    """
    Test the signup endpoint with an existing user.
    """
    user_dict = get_user.model_dump()

    def override_get_db_persist():
        """
        Override the get_db dependency for testing.
        """
        engine = create_engine("sqlite:///testing.db", echo=True, connect_args={"check_same_thread": False}, poolclass=StaticPool)
        SQLModel.metadata.create_all(engine, checkfirst=True)
        local_session = Session(engine)
        yield local_session
        local_session.close()

    app.dependency_overrides[get_db] = override_get_db_persist
    client = TestClient(app)
    response = client.post(
        "http://localhost:8000/signup/",
        json={
            "email": user_dict["email"],
            "first_name": user_dict["first_name"],
            "last_name": user_dict["last_name"],
            "password": user_dict["password"]
        }
    )
    assert response.status_code == 201
    # Try to create the same user again
    response = client.post(
        "http://localhost:8000/signup/",
        json={
            "email": user_dict["email"],
            "first_name": user_dict["first_name"],
            "last_name": user_dict["last_name"],
            "password": user_dict["password"]
        }
    )
    assert response.status_code == 503
    os.remove("./testing.db")

def test_login(get_user):
    """
    Test the login endpoint.
    """
    user_dict = get_user.model_dump()

    def override_get_db_persist():
        """
        Override the get_db dependency for testing.
        """
        engine = create_engine("sqlite:///testing.db", echo=True, connect_args={"check_same_thread": False}, poolclass=StaticPool)
        SQLModel.metadata.create_all(engine, checkfirst=True)
        local_session = Session(engine)
        yield local_session
        local_session.close()

    app.dependency_overrides[get_db] = override_get_db_persist
    client = TestClient(app)

    response = client.post(
        "http://localhost:8000/signup/",
        json={
            "email": user_dict["email"],
            "first_name": user_dict["first_name"],
            "last_name": user_dict["last_name"],
            "password": user_dict["password"]
        }
    )
    assert response.status_code == 201

    response = client.get(
        "http://localhost:8000/login/",
        auth=(user_dict["email"], user_dict["password"])
    )
    assert response.status_code == 200
    os.remove("./testing.db")

def test_login_invalid_credentials(get_user):
    """
    Test the login endpoint with invalid credentials.
    """
    user_dict = get_user.model_dump()

    def override_get_db_persist():
        """
        Override the get_db dependency for testing.
        """
        engine = create_engine("sqlite:///testing.db", echo=True, connect_args={"check_same_thread": False}, poolclass=StaticPool)
        SQLModel.metadata.create_all(engine, checkfirst=True)
        local_session = Session(engine)
        yield local_session
        local_session.close()

    app.dependency_overrides[get_db] = override_get_db_persist
    client = TestClient(app)

    response = client.post(
        "http://localhost:8000/signup/",
        json={
            "email": user_dict["email"],
            "first_name": user_dict["first_name"],
            "last_name": user_dict["last_name"],
            "password": user_dict["password"]
        }
    )
    assert response.status_code == 201

    response = client.get(
        "http://localhost:8000/login/",
        auth=(user_dict["email"], "wrongpassword")
    )
    assert response.status_code == 401
    os.remove("./testing.db")

def test_login_non_existent_user():
    """
    Test the login endpoint with a non-existent user.
    """
    response = client.get(
        "http://localhost:8000/login/",
        auth=("hacker", "hackerpassword")
    )
    assert response.status_code == 401

def test_current_user(get_user):
    """
    Test the current user endpoint.
    """
    user_dict = get_user.model_dump()

    def override_get_db_persist():
        """
        Override the get_db dependency for testing.
        """
        engine = create_engine("sqlite:///testing.db", echo=True, connect_args={"check_same_thread": False},
                               poolclass=StaticPool)
        SQLModel.metadata.create_all(engine, checkfirst=True)
        local_session = Session(engine)
        yield local_session
        local_session.close()

    app.dependency_overrides[get_db] = override_get_db_persist
    client = TestClient(app)

    try:

        response = client.post(
            "http://localhost:8000/signup/",
            json={
                "email": user_dict["email"],
                "first_name": user_dict["first_name"],
                "last_name": user_dict["last_name"],
                "password": user_dict["password"]
            }
        )
        assert response.status_code == 201

        response = client.get(
            "http://localhost:8000/me/",
            auth=(user_dict["email"], user_dict["password"])
        )
        assert response.status_code == 200
        response_json = json.loads(response.content)
        assert response_json["email"] == user_dict["email"]
        assert response_json["first_name"] == user_dict["first_name"]
        assert response_json["last_name"] == user_dict["last_name"]
        assert "password" not in response_json
    finally:
        os.remove("./testing.db")

def test_current_user_unauthenticated():
    """
    Test the current user endpoint without authentication.
    """
    response = client.get("http://localhost:8000/me/")
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Basic"

def test_update_user(get_user):
    """
    Test the update user endpoint.
    """
    user_dict = get_user.model_dump()

    def override_get_db_persist():
        """
        Override the get_db dependency for testing.
        """
        engine = create_engine("sqlite:///testing.db", echo=True, connect_args={"check_same_thread": False}, poolclass=StaticPool)
        SQLModel.metadata.create_all(engine, checkfirst=True)
        local_session = Session(engine)
        yield local_session
        local_session.close()

    app.dependency_overrides[get_db] = override_get_db_persist
    client = TestClient(app)

    try:
        response = client.post(
            "http://localhost:8000/signup/",
            json={
                "email": user_dict["email"],
                "first_name": user_dict["first_name"],
                "last_name": user_dict["last_name"],
                "password": user_dict["password"]
            }
        )
        assert response.status_code == 201

        response = client.put(
            "http://localhost:8000/me/",
            json={
                "first_name": "updated_first_name",
                "last_name": "updated_last_name",
                "password": "updatedpassword"
            },
            auth=(user_dict["email"], user_dict["password"])
        )
        assert response.status_code == 200

        response = client.get(
            "http://localhost:8000/me/",
            auth=(user_dict["email"], "updatedpassword")
        )
        assert response.status_code == 200
        response_json = json.loads(response.content)
        assert response_json["email"] == user_dict["email"]
        assert response_json["first_name"] == "updated_first_name"
        assert response_json["last_name"] == "updated_last_name"
    finally:
        os.remove("./testing.db")
