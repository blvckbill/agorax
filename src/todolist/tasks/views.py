
from fastapi import APIRouter, HTTPException, status

from starlette.responses import JSONResponse

from todolist.database.core import DbSession
from todolist.database.service import PaginationParameters, paginate
from todolist.auth.service import CurrentUser

from .models import (
    Todolist,
    TodolistTask,
    TodolistCreate,
    TodolistRead,
    TodotaskCreate,
    TodolistUpdate,
    TodotaskUpdate,
    TodotaskPagination,
    TodolistPagination
)

from .service import (
    get,
    get_all,
    get_completed,
    get_starred,
    get_tasks,
    create_list,
    add_task,
    update_list,
    update_task,
    delete_lt,
    delete_tk
)

task_router = APIRouter()


@task_router.get(
        "/{list_id}",
        response_model= TodolistRead
)
def get_list(
    db_session: DbSession,
    list_id:  int
):
    """Returns a todolist"""
    todolist = get(db_session=db_session, list_id=list_id)
    if not todolist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message":"List not found"}
        )
    return todolist


@task_router.get("/{list_id}/tasks", response_model=TodotaskPagination)
def get_all_tasks(list_id: int, commons: PaginationParameters):
    """Returns all tasks linked to a Todolist with pagination"""
    db_session = commons["db_session"]

    query = db_session.query(TodolistTask).filter(TodolistTask.list_id == list_id)

    return paginate(query, **commons)


@task_router.get("/{list_id}/tasks-completed", response_model=TodotaskPagination)
def get_completed_tasks(list_id: int, commons: PaginationParameters):
    """Returns tasks completed for a Todolist"""
    db_session = commons["db_session"]

    completed_tasks = db_session.query(TodolistTask).filter_by(list_id=list_id, is_completed=True)

    return paginate(completed_tasks, **commons)


@task_router.get("/{user_id}/todolists", response_model=TodolistPagination)
def get_all_todolists(user_id: int, commons: PaginationParameters):
    """Returns all Todolists created by a User"""

    db_session = commons["db_session"]
    todolists = db_session.query(Todolist).filter(Todolist.user_id == user_id)

    return paginate(todolists, **commons)


@task_router.get("/starred-tasks", response_model=TodotaskPagination)
def get_starred_tasks(commons: PaginationParameters):
    """Returns all starred tasks"""
    db_session = commons["db_session"]

    starred_tasks = db_session.query(TodolistTask).filter(TodolistTask.is_starred == True)

    return paginate(starred_tasks, **commons)


@task_router.post(
        "/create-list", 
        response_model=TodolistRead
    )
def create_todolist(db_session: DbSession, list_in: TodolistCreate, current_user: CurrentUser):
    """Creates a new Todo List"""
    return create_list(db_session=db_session, list_in=list_in, current_user=current_user)


@task_router.post("/{list_id}/add-task")
def add_tasks(db_session: DbSession, task_in: TodotaskCreate, list_id: int):
    """Adds a new task to Todolist"""
    todolist = get(db_session=db_session, list_id=list_id)
    if not todolist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message":"List not found"}
        )
    
    return add_task(db_session=db_session, task_in=task_in, todolist= todolist)


@task_router.put("/{list_id}/update-list")
def update_todolist(db_session: DbSession, todolist_in: TodolistUpdate, list_id: int):
    """Updates a list"""
    todolist = get(db_session=db_session, list_id=list_id)
    if not todolist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message":"List not found"}
        )
    
    return update_list(db_session=db_session, todolist=todolist, todolist_in=todolist_in)


@task_router.put("/{task_id}/update-list")
def update_todotask(db_session: DbSession, todotask_in: TodotaskUpdate, task_id: int):
    """Updates a task"""
    todotask = db_session.query(TodolistTask).filter_by(id=task_id).first()
    if not todotask:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message":"A Todotask with this id does not exist."}
        )
    
    return update_task(db_session=db_session, task=todotask, task_in=todotask_in)


@task_router.delete("/{list_id}/delete-list", response_model=None)
def delete_list(db_session: DbSession, list_id: int):
    """Delete a List."""
    todolist = get(db_session=db_session, list_id=list_id)
    if not todolist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=[{"msg": "A Todolist with this id does not exist."}],
        )
    delete_lt(db_session=db_session, list_id=list_id)


@task_router.delete("/{task_id}/delete-task", response_model=None)
def delete_task(db_session: DbSession, task_id: int):
    """Delete a Task."""
    todotask= db_session.query(TodolistTask).filter_by(id=task_id).first()
    if not todotask:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=[{"msg": "A Todotask with this id does not exist."}],
        )
    delete_tk(db_session=db_session, task_id=task_id)