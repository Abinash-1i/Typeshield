from datetime import datetime
from typing import List, Optional

from sqlalchemy import JSON, Column, ForeignKey
from sqlmodel import Field, Relationship, SQLModel


class BehaviourTemplate(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    dwell_times: List[float] = Field(default_factory=list, sa_column=Column(JSON))
    flight_times: List[float] = Field(default_factory=list, sa_column=Column(JSON))
    total_time: float
    error_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional["User"] = Relationship(back_populates="behaviour_template")


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str

    behaviour_template: Optional[BehaviourTemplate] = Relationship(
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
        back_populates="user",
    )


class AuthAttempt(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    username: Optional[str] = Field(default=None, index=True)
    status: str
    score: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
