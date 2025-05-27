import json
import os

from dotenv import load_dotenv
from fastapi import Depends, Response, APIRouter
from fastapi.security import HTTPBasicCredentials, HTTPBasic
import bcrypt

from typing import Annotated

from pydantic import BaseModel, Field

from src.db import (
    create_user,
    get_user_from_email,
    update_user_with_id,
    SQLModel,
    Session,
    check_connection
)
from sqlmodel import create_engine
from src.models.user import User

router = APIRouter()
security = HTTPBasic()


load_dotenv(f"{os.getenv('ENV')}.env")

if not os.getenv("CONN_STRING"):
    raise ValueError("CONN_STRING environment variable is not set. Please set it in the .env file.")

def get_db():
    """
    Dependency to get the database session.
    """
    engine = create_engine(os.getenv("CONN_STRING"))
    SQLModel.metadata.create_all(bind=engine, checkfirst=True)
    local_session = Session(engine)
    try:
        yield local_session
    finally:
        local_session.close()


class UpdateRequest(BaseModel):
    """
    Request body for updating user information.
    """

    password: str | None = Field(min_length=8, default=None)
    last_name: str | None = Field(min_length=1, default=None)
    first_name: str | None = Field(min_length=1, default=None)


@router.get("/healthz")
async def health_check(session: Session = Depends(get_db)):
    """
    Health check endpoint.
    """
    res = check_connection(session)
    if res:
        return Response(status_code=200)
    return Response(status_code=503)


@router.post("/signup/")
async def signup(new_user: User, session: Session = Depends(get_db)):
    """
    Sign up a new user.
    """
    new_user.password = bcrypt.hashpw(
        new_user.password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")
    res = create_user(new_user, session)
    if res:
        return Response(status_code=201)
    return Response(status_code=503)


@router.get("/login/")
async def login(credentials: Annotated[HTTPBasicCredentials, Depends(security)], session: Session = Depends(get_db)):
    """
    Log in a user.
    """
    user = get_user_from_email(credentials.username, session)
    if user is not None:
        if bcrypt.checkpw(
            credentials.password.encode("utf-8"), user.password.encode("utf-8")
        ):
            return Response(status_code=200)
    return Response(status_code=401, headers={"WWW-Authenticate": "Basic"})


@router.get("/me")
async def get_current_user(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
    session: Session = Depends(get_db)
):
    """
    Get the current user.
    """
    user = get_user_from_email(credentials.username, session)
    if user is not None and bcrypt.checkpw(
        credentials.password.encode("utf-8"), user.password.encode("utf-8")
    ):
        return Response(status_code=200, content=json.dumps(user.safe_dict()))
    return Response(status_code=401, headers={"WWW-Authenticate": "Basic"})


@router.put("/me")
async def update_user(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
    new_user: UpdateRequest,
    session: Session = Depends(get_db)
):
    """
    Update the current user.
    """
    user_from_db = get_user_from_email(credentials.username, session)
    if user_from_db is not None and bcrypt.checkpw(
        credentials.password.encode("utf-8"), user_from_db.password.encode("utf-8")
    ):
        res = update_user_with_id(
            user_from_db.id,
            User(
                first_name=(
                    new_user.first_name
                    if new_user.first_name
                    else user_from_db.first_name
                ),
                last_name=(
                    new_user.last_name if new_user.last_name else user_from_db.last_name
                ),
                password=(
                    bcrypt.hashpw(
                        new_user.password.encode("utf-8"), bcrypt.gensalt()
                    ).decode("utf-8")
                    if new_user.password
                    else user_from_db.password
                ),
            ),
            session
        )
        if res:
            return Response(status_code=200)
    return Response(status_code=401, headers={"WWW-Authenticate": "Basic"})
