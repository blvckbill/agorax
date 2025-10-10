
from fastapi import APIRouter, HTTPException, status

from sqlalchemy import case

from starlette.responses import JSONResponse

from src.todolist.permissions import (
    InvitePermission,
    AddPermission,
    EditPermission,
    DeletePermission,
    RemovePermission,
    ViewPermission
)
from src.todolist.database.core import DbSession
from src.todolist.database.service import PaginationParameters, paginate
from src.todolist.auth.service import CurrentUser
from src.todolist.auth.models import TodolistUser

from src.todolist.websocket.manager import ws_manager
from src.todolist.services.rabbitmq.producer import rabbit_publisher

from .models import (
    Todolist,
    TodolistTask,
    TodolistCreate,
    TodolistRead,
    TodotaskCreate,
    TodolistUpdate,
    TodotaskUpdate,
    TodotaskPagination,
    TodolistPagination,
    TodolistMembers
)

from .service import (
    get_user_list,
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


@task_router.get("/{list_id}", response_model=TodolistRead)
def get_list(
    db_session: DbSession,
    list_id: int,
    current_user: CurrentUser,
    permission: ViewPermission,
):
    todolist = get_user_list(db_session=db_session, list_id=list_id, user_id=current_user.id)
    if not todolist:
        raise HTTPException(status_code=404, detail={"message": "List not found"})
    return todolist


@task_router.get("/{list_id}/tasks", response_model=TodotaskPagination)
def get_all_tasks(list_id: int, commons: PaginationParameters, permission: ViewPermission):
    """Returns all tasks linked to a Todolist with pagination"""
    db_session = commons["db_session"]

    query = db_session.query(TodolistTask).filter(TodolistTask.list_id == list_id)

    return paginate(query, **commons)


@task_router.get("/{list_id}/tasks-completed", response_model=TodotaskPagination)
def get_completed_tasks(list_id: int, commons: PaginationParameters, current_user: CurrentUser, permission: ViewPermission):
    """Returns tasks completed for a Todolist"""
    db_session = commons["db_session"]

    completed_tasks = db_session.query(TodolistTask).filter_by(list_id=list_id, user_id=current_user.id, is_completed=True)

    return paginate(completed_tasks, **commons)


@task_router.get("/{user_id}/todolists", response_model=TodolistPagination)
def get_all_todolists(user_id: int, commons: PaginationParameters, permission: ViewPermission):
    """Returns all Todolists a user has access to (owner or member), including their role."""

    db_session = commons["db_session"]

    user_role = case(
        (Todolist.user_id == user_id, "owner"), 
        else_=TodolistMembers.role           
    ).label("user_role")

    query = (
        db_session.query(Todolist, user_role)
        .outerjoin(TodolistMembers, Todolist.id == TodolistMembers.list_id)
        .filter(
            (Todolist.user_id == user_id) | (TodolistMembers.user_id == user_id)
        )
        .distinct()
    )

    return paginate(query, **commons)


@task_router.get("/starred-tasks", response_model=TodotaskPagination)
def get_starred_tasks(commons: PaginationParameters, current_user: CurrentUser, permission: ViewPermission):
    """Returns all starred tasks"""
    db_session = commons["db_session"]

    starred_tasks = db_session.query(TodolistTask).filter_by(user_id=current_user.id, is_starred = True)

    return paginate(starred_tasks, **commons)


@task_router.post(
        "/create-list", 
        response_model=TodolistRead
    )
def create_todolist(db_session: DbSession, list_in: TodolistCreate, current_user: CurrentUser):
    """Creates a new Todo List"""
    return create_list(db_session=db_session, list_in=list_in, current_user=current_user)


@task_router.post("/{list_id}/add-task")
async def add_tasks(
    db_session: DbSession,
    list_id: int,
    task_in: TodotaskCreate,
    current_user: CurrentUser,
    permission: AddPermission,
):
    todolist = get_user_list(db_session=db_session, list_id=list_id, user_id=current_user.id)
    if not todolist:
        raise HTTPException(status_code=404, detail={"message": "List not found"})
    
    task = add_task(db_session=db_session, task_in=task_in, todolist=todolist, current_user=current_user.id)

    await rabbit_publisher.publish_sharded_event(
        list_id=list_id,
        message={"action": "task_added", "task": task.dict()}
    )

    return task


@task_router.put("/{list_id}/update-list")
async def update_todolist(db_session: DbSession, todolist_in: TodolistUpdate, list_id: int, current_user: CurrentUser, permission: EditPermission):
    """Updates a list"""
    todolist = get_user_list(db_session=db_session, list_id=list_id, user_id=current_user.id)
    if not todolist:
        raise HTTPException(
            status_code=404,
            detail={"message":"List not found"}
        )
    
    list_update = update_list(db_session=db_session, todolist=todolist, todolist_in=todolist_in)

    await rabbit_publisher.publish_sharded_event(
        list_id=list_id,
        message={"action": "list_title_update", "task": list_update.dict()}
    )

    return list_update


@task_router.put("/{list_id}/{task_id}/update-task")
async def update_todotask(db_session: DbSession, todotask_in: TodotaskUpdate, list_id: int, task_id: int, current_user: CurrentUser, permission: EditPermission):
    """Updates a task"""
    todotask = db_session.query(TodolistTask).filter_by(id=task_id, list_id=list_id).first()
    if not todotask:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message":"A Todotask with this id does not exist."}
        )
    
    task_update = update_task(db_session=db_session, task=todotask, task_in=todotask_in)
    
    await rabbit_publisher.publish_sharded_event(
        list_id=list_id,
        message={"action": "task_updated", "task": task_update.dict()}
    )

    return task_update


@task_router.delete("/{list_id}/delete-list", response_model=None)
async def delete_list(db_session: DbSession, list_id: int,  current_user: CurrentUser, permission: DeletePermission):
    """Delete a List."""
    todolist = get_user_list(db_session=db_session, list_id=list_id, user_id=current_user.id)
    if not todolist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=[{"msg": "A Todolist with this id does not exist."}],
        )
    delete_lt(db_session=db_session, list_id=list_id)

    await rabbit_publisher.publish_sharded_event(
        list_id=list_id,
        message={"action": "task_added", "task": {"id":list_id}}
    )

    return {"msg": "Todolist deleted", "id": list_id}


@task_router.delete("/{list_id}/{task_id}/delete-task", response_model=None)
async def delete_task(db_session: DbSession, list_id: int, task_id: int,  permission: DeletePermission):
    """Delete a Task."""
    todotask= db_session.query(TodolistTask).filter_by(id=task_id, list_id=list_id).first()
    if not todotask:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=[{"msg": "A Todotask with this id does not exist."}],
        )
    delete_tk(db_session=db_session, task_id=task_id)

    await rabbit_publisher.publish_sharded_event(
        list_id=list_id,
        message={"action": "task_added", "task": {"id":task_id}}
    )

    return {"msg": "Todotask deleted", "id": task_id}


#==================== Views for multi user on a todolist ==========================

@task_router.post("/{list_id}/invite-user")
async def invite_user(
    db_session: DbSession, 
    list_id: int, 
    invitee_id:int, 
    current_user: CurrentUser, 
    role: str,
    permission: InvitePermission
    ):
    """Invite a new user to the todolist (owners only)."""

    existing_member = (
        db_session.query(TodolistMembers)
        .filter_by(list_id=list_id, user_id=invitee_id)
        .first()
    )
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this list"
        )

    invitee = db_session.query(TodolistUser).filter_by(id=invitee_id).first()
    if not invitee:
        raise HTTPException(status_code=404, detail="Invitee not found")

    new_member = TodolistMembers(
        list_id=list_id,
        user_id=invitee_id,
        role=role
    )
    db_session.add(new_member)
    db_session.commit()
    db_session.refresh(new_member)

    await rabbit_publisher.publish_sharded_event(
        list_id=list_id,
        message={
            "action": "user_added",
            "member": {
                "user_id": new_member.user_id,
                "role": new_member.role
            }
        }
    )

    return {
        "msg": f"User {invitee.email} invited as {role}",
        "member_id": new_member.id,
        "role": new_member.role
    }


@task_router.post("/{list_id}/remove-user")
async def remove_user(
    db_session: DbSession, 
    list_id: int, 
    user_id:int, # user to be removed
    current_user: CurrentUser, 
    permission: RemovePermission
    ):
    """Remove a user to the todolist (owners only)."""

    membership = (
        db_session.query(TodolistMembers)
        .filter_by(list_id=list_id, user_id=user_id)
        .first()
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not a member of this list"
        )

    db_session.delete(membership)
    db_session.commit()

    await rabbit_publisher.publish_sharded_event(
        list_id=list_id,
        message={
            "action": "user_removed",
            "member": {
                "user_id": membership.user_id
            }
        }
    )

    return {
        "msg": "User removed successfully",
        "user_id": user_id,
        "list_id": list_id
    }
