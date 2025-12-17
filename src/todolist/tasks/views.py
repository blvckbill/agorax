from fastapi import APIRouter, HTTPException, status

from sqlalchemy import desc, or_
from fastapi import Query
from sqlalchemy.orm import selectinload

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
    TodolistMembers,
    InviteUserPayload,
    ListMemberResponse,
    UserSearchResponse
)

from .service import (
    get_user_list,
    create_list,
    add_task,
    update_list,
    update_task,
    delete_lt,
    delete_tk
)

task_router = APIRouter()
user_router = APIRouter()


@task_router.get("/starred-tasks", response_model=TodotaskPagination)
def get_starred_tasks(db_session: DbSession, commons: PaginationParameters, current_user: CurrentUser):
    """Returns all starred tasks"""
    starred_tasks = db_session.query(TodolistTask).filter_by(user_id=current_user.id, is_starred = True)

    return paginate(starred_tasks, **commons)

@task_router.get("/{list_id}", response_model=TodolistRead) 
def get_list(
    db_session: DbSession,
    list_id: int,
    current_user: CurrentUser,
    permission: ViewPermission,
):
    """Get a single list and inject the user's role."""
    
    todolist = get_user_list(db_session=db_session, list_id=list_id, user_id=current_user.id)
    if not todolist:
        raise HTTPException(status_code=404, detail={"message": "List not found"})

    if todolist.user_id == current_user.id:
        todolist.user_role = "owner"
    else:
        # Check membership table if not owner
        membership = (
            db_session.query(TodolistMembers)
            .filter_by(list_id=list_id, user_id=current_user.id)
            .first()
        )
        if membership:
            todolist.user_role = membership.role
        else:
            todolist.user_role = "viewer"

    return todolist


@task_router.get("/{list_id}/tasks", response_model=TodotaskPagination)
def get_all_tasks(db_session: DbSession, list_id: int, commons: PaginationParameters, permission: ViewPermission):
    """Returns all tasks linked to a Todolist with pagination"""
    query = db_session.query(TodolistTask).filter(TodolistTask.list_id == list_id)

    return paginate(query, **commons)


@task_router.get("/{list_id}/tasks-completed", response_model=TodotaskPagination)
def get_completed_tasks(
    db_session: DbSession, 
    list_id: int, 
    commons: PaginationParameters, 
    current_user: CurrentUser, 
    permission: ViewPermission
):
    """Returns ALL completed tasks for a list, regardless of who created them."""
    
    completed_tasks = (
        db_session.query(TodolistTask)
        .filter(
            TodolistTask.list_id == list_id,
            TodolistTask.is_completed == True
        )
        .order_by(desc(TodolistTask.updated_at)) 
    )

    return paginate(completed_tasks, **commons)


@user_router.get("/{user_id}/todolists", response_model=TodolistPagination)
def get_all_todolists(
    db_session: DbSession, 
    user_id: int, 
    commons: PaginationParameters
):
    """Returns all Todolists a user has access to, with the correct role injected."""

    query = (
        db_session.query(Todolist)
        .options(
            selectinload(Todolist.members),
            selectinload(Todolist.task)
        )
        .filter(
            or_(
                Todolist.user_id == user_id,
                Todolist.members.any(user_id=user_id)  
            )
        )
    )

    paginated_result = paginate(query, **commons)

    for todo in paginated_result["items"]:
        if todo.user_id == user_id:
            todo.user_role = "owner"
        else:
            membership = next(
                (m for m in todo.members if m.user_id == user_id), 
                None
            )
            
            if membership:
                todo.user_role = membership.role 
            else:
                todo.user_role = "viewer"

    return paginated_result


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


@task_router.patch("/{list_id}/{task_id}/update-task")
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

@task_router.post("/{list_id}/invite")
async def invite_user(
    db_session: DbSession, 
    list_id: int, 
    payload: InviteUserPayload, 
    current_user: CurrentUser,
    permission: InvitePermission
):
    """Invite a new user to the todolist (owners only)."""

    invitee_id = payload.invitee_id
    role = payload.role

    # Check if already a member
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

    # Fetch the user to be invited
    invitee = db_session.query(TodolistUser).filter_by(id=invitee_id).first()
    if not invitee:
        raise HTTPException(status_code=404, detail="Invitee not found")

    # Create new membership
    new_member = TodolistMembers(
        list_id=list_id,
        user_id=invitee_id,
        role=role
    )
    db_session.add(new_member)
    db_session.commit()
    db_session.refresh(new_member)

    member_response = {
        "id": new_member.id,
        "user_id": new_member.user_id,
        "list_id": new_member.list_id,
        "role": new_member.role,
        "user": {
            "id": invitee.id,
            "email": invitee.email,
            "first_name": invitee.first_name,
            "last_name": invitee.last_name
        }
    }

    # RabbitMQ Event
    await rabbit_publisher.publish_sharded_event(
        list_id=list_id,
        message={
            "action": "user_added",
            "member": member_response
        }
    )

    return {
        "message": f"User {invitee.email} invited as {role}",
        "member": member_response 
    }


@task_router.post("/{list_id}/remove-user")
async def remove_user(
    db_session: DbSession, 
    list_id: int, 
    user_id: int = Query(..., description="The ID of the user to remove"),
    current_user: CurrentUser = None,
    permission: RemovePermission = None
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
                "user_id": user_id
            }
        }
    )

    return {
        "message": "User removed successfully",
    }


@task_router.get("/{list_id}/members", response_model=list[ListMemberResponse])
def get_list_members(
    db_session: DbSession,
    list_id: int,
    current_user: CurrentUser
):
    """Fetch all members of a list, including the owner."""
    
    todolist = (
        db_session.query(Todolist)
        .options(selectinload(Todolist.user)) 
        .filter(Todolist.id == list_id)
        .first()
    )
    
    if not todolist:
        raise HTTPException(status_code=404, detail="List not found")

    members = (
        db_session.query(TodolistMembers)
        .options(selectinload(TodolistMembers.user)) 
        .filter(TodolistMembers.list_id == list_id)
        .all()
    )
    all_members = []


    owner_id = todolist.user_id
    all_members.append({
        "id": None,
        "user_id": owner_id,
        "list_id": todolist.id,
        "role": "owner",
        "user": todolist.user
    })

    for member in members:
        if member.user_id != owner_id:
            all_members.append(member)

    return all_members


@user_router.get("/search", response_model=list[UserSearchResponse])
def search_users(
    q: str,
    db_session: DbSession,
    current_user: CurrentUser
):
    """Search users by email or name."""
    if len(q) < 2:
        return []
    
    users = (
        db_session.query(TodolistUser)
        .filter(
            or_(
                TodolistUser.email.ilike(f"%{q}%"),
                TodolistUser.first_name.ilike(f"%{q}%"),
                TodolistUser.last_name.ilike(f"%{q}%")
            )
        )
        .limit(10)
        .all()
    )

    return users