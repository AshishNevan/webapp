from typing import Optional
from sqlmodel import SQLModel, Field, String

from datetime import datetime, timezone


class User(SQLModel, table=True):

    id: Optional[int] = Field(primary_key=True, index=True)
    email: str = Field(String, unique=True, nullable=False)
    password: str = Field(String, nullable=False)
    first_name: Optional[str] = Field(String, nullable=False)
    last_name: Optional[str] = Field(String, nullable=False)
    account_created: Optional[datetime] = Field(default=datetime.now(timezone.utc))
    account_updated: Optional[datetime] = Field(default=datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"id={self.id!r}, email={self.email!r}, password={self.password!r}, first_name={self.first_name!r}, last_name={self.last_name!r}, account_created={self.account_created.__str__()!r}, account_updated={self.account_updated.__str__()!r}"

    def safe_dict(self):
        """
        Returns a dictionary representation of the user, excluding sensitive information.
        """
        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "account_created": self.account_created.isoformat(),
            "account_updated": self.account_updated.isoformat()
        }