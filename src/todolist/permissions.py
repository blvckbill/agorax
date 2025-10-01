from fastapi import HTTPException, status, Depends

from src.todolist.database.core import DbSession
from src.todolist.auth.service import CurrentUser
from src.todolist.tasks.models import TodolistMembers

from typing import Annotated

ROLE_PERMISSIONS = {
    "owner": {"invite", "remove", "add_task", "edit_task", "delete_task", "view_task"},
    "editor": {"add_task", "edit_task", "delete_task", "view_task"},
    "viewer": {"view_task"},
}


def has_permission(role: str, action: str) -> bool:
    """Check if a role is allowed to perform an action."""
    return action in ROLE_PERMISSIONS.get(role, set())


def require_permission(action: str):
    """
        Dependency factory that checks if current_user 
        has permission to perform `action` on a given list_id
    """

    def dependency(db_session: DbSession, list_id: int, current_user: CurrentUser):
        membership = (
            db_session.query(TodolistMembers)
            .filter_by(list_id=list_id, user_id=current_user.id)
            .first()
        )
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this list."
            )
        
        if not has_permission(membership.role, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Your role '{membership.role}' does not allow '{action}'"
            )

        return membership

    return dependency

InvitePermission = Annotated[TodolistMembers, Depends(require_permission("invite"))]
AddPermission = Annotated[TodolistMembers, Depends(require_permission("add_task"))]
EditPermission = Annotated[TodolistMembers, Depends(require_permission("edit_task"))]
ViewPermission = Annotated[TodolistMembers, Depends(require_permission("view_task"))]
DeletePermission = Annotated[TodolistMembers, Depends(require_permission("delete_task"))]
RemovePermission = Annotated[TodolistMembers, Depends(require_permission("remove"))]