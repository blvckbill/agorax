
from datetime import date, time

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, select, func, Date, Time, Enum
from sqlalchemy.orm import relationship

from src.todolist.database.core import Base
from src.todolist.models import TimeStampMixin, NameStr, Pagination
from src.todolist.auth.models import TodolistUser, ToDoListBase

from src.todolist.database.core import DbSession


class Todolist(Base, TimeStampMixin):
    """SQLAlchemy model for the relationship between users and tasks"""

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("todolist_user.id"), nullable=False)
    title = Column(String, nullable=False)

    user = relationship("TodolistUser", back_populates="todolist")
    task = relationship("TodolistTask", back_populates="todolist", cascade="all, delete-orphan")
    members = relationship("TodolistMembers", back_populates="todolist")


class TodolistTask(Base, TimeStampMixin):
    """SQLAlchemy model that links tasks to a list"""

    id = Column(Integer, primary_key=True)
    list_id = Column(Integer, ForeignKey("todolist.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("todolist_user.id"), nullable=False)
    task_title = Column(String, nullable=False)
    task_details = Column(Text, nullable=True)
    due_date = Column(Date, nullable=True)
    start_time = Column(Time, nullable=True)
    is_completed = Column(Boolean, default=False)
    is_starred = Column(Boolean, default=False)

    user = relationship("TodolistUser", back_populates="task")
    todolist = relationship("Todolist", back_populates="task")

class TodolistMembers(Base, TimeStampMixin):
    """SQLAlchemy model that allows multiple users access to a Todolist"""

    id = Column(Integer, primary_key=True)
    list_id = Column(Integer, ForeignKey("todolist.id"))
    user_id = Column(Integer, ForeignKey("todolist_user.id"))
    role = Column(Enum("owner", "viewer", "editor", name="role_enum"), default="editor")

    todolist = relationship("Todolist", back_populates="members")
    user = relationship("TodolistUser", back_populates="memberships")

class TodolistCreate(ToDoListBase):
    """Pydaantic model for user todolist"""

    title: str

class TodolistRead(ToDoListBase):
    """Pydantic model to read a Todolist"""

    id: int
    title: str
    user_role: str

class TodolistUpdate(ToDoListBase):
    """Pydantic model to update a list"""

    title: str


class TodotaskCreate(ToDoListBase):
    """Pydantic model for creating tasks"""

    task_title: str
    task_details: str | None = None
    due_date: str | None = None
    start_time: str | None = None


class TodotaskRead(ToDoListBase):
    """Pydantic model to read a Todotask"""

    id: int
    list_id: int
    task_title: str
    task_details: str | None = None
    due_date: str | None = None
    start_time: str | None = None
    is_completed: bool
    is_starred: bool


class TodotaskUpdate(ToDoListBase):
    """Pydabtic modek to update a Todotask"""
    task_title: str | None = None
    task_details: str | None = None
    due_date: str | None = None
    start_time: str | None = None
    is_completed: bool| None = None
    is_starred: bool | None = None

class TodolistWithRole(TodolistRead):
    user_role: str | None = "viewer"

class TodolistPagination(Pagination):
    """Pydantic model for paginated todolist results."""

    items: list[TodolistWithRole] = []


class TodotaskPagination(Pagination):
    """Pydantic model for paginated todotask results."""

    items: list[TodotaskRead] = []

class InviteUserPayload(ToDoListBase):
    invitee_id: int
    role: str

class RemoveUserPayload(ToDoListBase):
    user_id: int

class UserSummary(ToDoListBase):
    id: int
    email: str
    first_name: str
    last_name: str

class ListMemberResponse(ToDoListBase):
    id: int | None = None 
    user_id: int
    list_id: int
    role: str
    user: UserSummary 
