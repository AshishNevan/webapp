import pytest
from sqlmodel import create_engine, Session, SQLModel

from src.db import check_connection, create_user, get_user_from_email, update_user_with_id
from src.models.user import User

@pytest.fixture
def get_user():
    return User(email="email@email.com", password="hashedsupersecretpassword", first_name="Test", last_name="User")

@pytest.fixture
def get_db():
    """
    Fixture to create a database engine for testing.
    """
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    session = Session(engine, autoflush=False)
    yield session
    session.close()
    SQLModel.metadata.drop_all(engine)

@pytest.fixture
def get_db_user(get_user, get_db):
    """
    Fixture to create a user in the database for testing.
    """
    user = get_user
    get_db.add(user)
    get_db.commit()
    return user


def test_db_connection(get_db):
    """
    Test the database connection.
    """
    res = check_connection(get_db)
    assert res


def test_create_user(get_db, get_user):
    """
    Test creating a user in the database.
    """
    res = create_user(get_user, get_db)
    assert res

def test_create_user_failure(get_user, get_db):
    """
    Test creating a user with existing email in the database.
    """
    user_dict = get_user.model_dump()
    res = create_user(get_user, get_db)
    assert res

    same_user = User(**user_dict)
    res = create_user(same_user, get_db)
    assert not res

def test_get_user_from_email(get_db, get_db_user):
    """
    Test getting a user from the database by email.
    """
    user = get_user_from_email(get_db_user.email, get_db)
    assert user is not None
    assert user.email == get_db_user.email


def test_update_user_with_id(get_db, get_db_user):
    """Test updating a user in the database by ID."""
    update_user = User(
        id=get_db_user.id,
        email=get_db_user.email,
        password="newhashedpassword",
        first_name="UpdatedFirstName",
        last_name="UpdatedLastName"
    )
    updated_user = update_user_with_id(get_db_user.id, update_user, get_db)
    assert updated_user.first_name == update_user.first_name
    assert updated_user.last_name == update_user.last_name
    assert updated_user.password == update_user.password
