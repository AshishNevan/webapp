from sqlmodel import SQLModel, Session, select, text

import logging
from datetime import datetime, timezone

from src.models.user import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_connection(session: Session) -> bool:
    """
    Test the database connection.
    """
    res = False
    with session:
        try:
            # Execute a simple query to test the connection
            result = session.exec(text("SELECT 1"))
            if result.scalar() == 1:
                logger.info("Database connection successful.")
                res = True
            else:
                logger.error("Database connection failed.")
        except Exception as e:
            logger.error(f"Error testing database connection: {e}")
    return res


def bootstrap(session: Session) -> bool:
    """
    Bootstrap the database.
    """
    # Create a new SQLAlchemy engine instance
    res = False
    try:
        with session:
            SQLModel.metadata.create_all(bind=session.bind)
            logger.info("Database bootstrapped successfully.")
            res = True
    except Exception as e:
        logger.error(f"Failed to bootstrap the database.: {e}")
    return res


def create_user(new_user: User, session: Session) -> bool:
    """
    Create a new user in the database.
    """
    res = False
    try:
        with session:
            session.add(new_user)
            session.commit()
        res = True
        logger.info("User created successfully.")
    except Exception as e:
        logger.error(f"Error creating user: {e}")
    return res


def get_user_from_email(email: str, session: Session) -> User | None:
    """
    Get a user from the database by email.
    """
    res = None
    with session:
        try:
            # Query the user by email
            user = session.exec(select(User).where(User.email == email)).first()
            if user is not None:
                res = user
                logger.info(f"User found: {res}")
            else:
                logger.info("User not found.")
        except Exception as e:
            logger.error(f"Error getting user from email: {e}")
    return res


def update_user_with_id(user_id: int, user: User , session: Session) -> User | None:
    """
    Update a user in the database by ID.
    """
    res = None
    with session:
        try:
            existing_user = session.get(User, user_id)
            if existing_user is not None:
                fields_to_update = ['first_name', 'last_name', 'password']
                for field in fields_to_update:
                    new_value = getattr(user, field, getattr(existing_user, field))
                    setattr(existing_user, field, new_value)
                existing_user.account_updated = datetime.now(timezone.utc)
                session.commit()
                session.refresh(existing_user)
                res = existing_user
                logger.info(f"User updated successfully: {existing_user}")
            else:
                logger.info("User not found.")
        except Exception as e:
            logger.error(f"Error updating user: {e}")
    return res
