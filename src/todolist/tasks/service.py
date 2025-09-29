from fastapi import Depends


from sqlalchemy_filters import apply_pagination
from typing import Annotated

from .models import (
    Todolist,
    TodolistTask,
    TodolistCreate,
    TodotaskCreate,
    TodolistUpdate,
    TodotaskUpdate,
    TodolistMembers
)
def get(*, db_session, list_id: int) -> Todolist:
    """Returns a Todo list"""
    return db_session.query(Todolist).filter(Todolist.id == list_id)

def get_all(*, db_session, user_id: int):
    """Returns all todolist linked to a user"""
    return db_session.query(Todolist).filter(Todolist.user_id == user_id).all()

def get_tasks(*, db_session, list_id: int) -> TodolistTask | None:
    """Returns the tasks linked to a TodoList"""
    return db_session.query(TodolistTask).filter(TodolistTask.list_id == list_id).all()

def get_completed(*, db_session, list_id: int) -> TodolistTask:
    """Return a Todolist completed Tasks"""
    return db_session.query(TodolistTask).filter_by(list_id=list_id, is_completed=True).all()

def get_starred(*, db_session) -> TodolistTask:
    """Return starred tasks"""
    return db_session.query(TodolistTask).filter(TodolistTask.is_starred == True).all()

def create_list(*, db_session, list_in: TodolistCreate, current_user) -> Todolist:
    """Creates a Todolist"""
    todolist = Todolist(
        **list_in.model_dump(),
        user_id = current_user.id
    )
    
    db_session.add(todolist)
    db_session.commit()
    db_session.refresh(todolist)

    membership = TodolistMembers(
        list_id = todolist.id,
        user_id = current_user.id,
        role = "owner"
    )

    db_session.add(membership)
    db_session.commit()
    db_session.refresh(membership)
    
    return todolist

def add_task(*, db_session, task_in: TodotaskCreate, todolist) -> TodolistTask:
    """Creates a task and adds it to a Todolist"""
    task = TodolistTask(
        **task_in.model_dump(),
        list_id = todolist.id
    )

    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    return task

def update_list(*, db_session, todolist: Todolist, todolist_in: TodolistUpdate) -> Todolist:
    """Updates a list"""
    todolist_data = todolist.dict()

    update_data = todolist_in.model_dump()

    for field in todolist_data:
        if field in update_data:
            setattr(todolist, field, update_data[field])

    db_session.commit()
    return todolist

def update_task(*, db_session, task: TodolistTask, task_in: TodotaskUpdate) -> TodolistTask:
    """Updates a task"""
    task_data = task.dict()

    update_data = task_in.model_dump()

    for field in task_data:
        if field in update_data:
            setattr(task, field, update_data[field])

    db_session.commit()
    return task

def delete_lt(*, db_session, list_id: int):
    db_session.query(Todolist).filter(Todolist.id == list_id).delete()
    db_session.commit()


def delete_tk(*, db_session, task_id: int):
    db_session.query(TodolistTask).filter(TodolistTask.id == task_id).delete()
    db_session.commit()

def get_current_role(*, db_session, list_id: int):
