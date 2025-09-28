
from datetime import date, time

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, select, func, Date, Time
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



class TodolistTask(Base, TimeStampMixin):
    """SQLAlchemy model that links tasks to a list"""

    id = Column(Integer, primary_key=True)
    list_id = Column(Integer, ForeignKey("todolist.id"), nullable=False)
    task_title = Column(String, nullable=False)
    task_details = Column(Text, nullable=True)
    due_date = Column(Date, nullable=True)
    start_time = Column(Time, nullable=True)
    is_completed = Column(Boolean, default=False)
    is_starred = Column(Boolean, default=False)

    todolist = relationship("Todolist", back_populates="task")

class TodolistCreate(ToDoListBase):
    """Pydaantic model for user todolist"""

    title: str

class TodolistRead(ToDoListBase):
    """Pydantic model to read a Todolist"""

    id: int
    title: str

class TodolistUpdate(ToDoListBase):
    """Pydantic model to update a list"""

    title: str


class TodotaskCreate(ToDoListBase):
    """Pydantic model for creating tasks"""

    task_title: str
    task_details: str | None = None
    due_date: date | None
    start_time: time | None


class TodotaskRead(ToDoListBase):
    """Pydantic model to read a Todotask"""

    id: int
    list_id: int
    task_title: str
    task_details: str | None = None
    due_date: date | None = None
    start_time: time | None = None
    is_completed: bool
    is_starred: bool


class TodotaskUpdate(ToDoListBase):
    """Pydabtic modek to update a Todotask"""
    task_title: str
    task_details: str
    due_date: date | None = None
    start_time: time | None = None
    is_completed: bool
    is_starred: bool


class TodolistPagination(Pagination):
    """Pydantic model for paginated todolist results."""

    items: list[TodolistRead] = []


class TodotaskPagination(Pagination):
    """Pydantic model for paginated todotask results."""

    items: list[TodotaskRead] = []