import logging

from datetime import datetime, timezone, timedelta

from fastapi import HTTPException, Depends, BackgroundTasks
from fastapi.security.utils import get_authorization_scheme_param

from jose import jwt, JWTError
from jose.exceptions import JWKError

from sqlalchemy.exc import IntegrityError

from starlette.requests import Request
from starlette.status import HTTP_401_UNAUTHORIZED

from todolist.auth.models import TodolistUser, UserCreate, OtpCode, OtpModel
from todolist.config import TODOLIST_JWT_SECRET, TODOLIST_JWT_ALG, OTP_EXPIRY_TIME
from .utils import (
    generate_random_string, 
    send_mail
)

from typing import Annotated

log = logging.getLogger(__name__)


def get(*, db_session, user_id: int) -> TodolistUser | None:
    """Returns a user based on the given user id."""
    return db_session.query(TodolistUser).filter(TodolistUser.id == user_id).one_or_none()


def get_by_email(*, db_session, email: str) -> TodolistUser| None:
    """Returns a user based on the given email"""
    return db_session.query(TodolistUser).filter(TodolistUser.email == email).one_or_none()


def create(*, db_session, user_in: UserCreate) -> TodolistUser:
    """Creates a new TodoList User"""

    user = TodolistUser(
        **user_in.model_dump(exclude={"password"}),
        password=user_in.password
    )

    db_session.add(user)
    db_session.commit()

    return user


def send_otp_user(*, db_session, user, background_tasks: BackgroundTasks):
    otp_code =  generate_random_string(5)
    otp_expires = datetime.now(timezone.utc) + timedelta(seconds=OTP_EXPIRY_TIME).timestamp()

    # Check if user already has an OTP record
    otp_instance = db_session.query(OtpModel).filter(OtpModel.user_id == user.id).first()

    if otp_instance:
        # Update existing OTP
        otp_instance.otp_code = otp_code
        otp_instance.otp_expires = otp_expires
        otp_instance.is_used = False
    else:
        # Create a new OTP record
        otp_instance = OtpModel(
            otp_code=otp_code,
            otp_expires=otp_expires,
            user=user,
        )
        db_session.add(otp_instance)
    
    db_session.commit()

    background_tasks.add_tasks(
        send_mail,
        email=user.email,
        subject="One-Time Password (OTP) for ToDoList App",
        body=f"Hello {user.first_name}, your OTP is {otp_code}. It expires in {OTP_EXPIRY_TIME} seconds. Do not share it with anyone."
    )

    return otp_code


def get_or_create(*, db_session, user_in: UserCreate) -> TodolistUser:
    """Gets an existing user or creates a new one."""
    user = get_by_email(db_session=db_session, email=user_in.email)

    if not user:
        try:
            user = create(db_session=db_session, user_in=user_in)
        except IntegrityError:
            db_session.rollback()
            log.exception(f"Unable to create user with email address {user_in.email}.")

    return user


             
def get_current_user(request: Request)-> TodolistUser:
    """Attempts to get the current authenticated user"""
    authorization = request.headers.get("Authorization")
    scheme, param = get_authorization_scheme_param(authorization)
    if not authorization or scheme.lower() != "bearer":
        log.exception(
            f"Malformed authorization header. Scheme: {scheme} Param: {param} Authorization: {authorization}"
        )
        return
    token = param

    try:
        data = jwt.decode(token, TODOLIST_JWT_SECRET, algorithms=TODOLIST_JWT_ALG)
    except (JWTError, JWKError):
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail=[{"msg": "Could not validate credentials"}],
        ) from None
    
    user_id = data.get("sub")

    user = get(
        db_session=request.state.db,
        user_id=user_id
    )
    return user

CurrentUser = Annotated[TodolistUser, Depends(get_current_user)]