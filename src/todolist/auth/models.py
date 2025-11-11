import bcrypt
from jose import jwt
import logging
from pydantic import EmailStr, field_validator, ValidationError

from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, String, Integer, LargeBinary, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from src.todolist.models import TimeStampMixin, ToDoListBase, NameStr
from src.todolist.database.core import Base
from src.todolist.config import (
    TODOLIST_JWT_ALG,
    TODOLIST_JWT_EXP,
    TODOLIST_JWT_SECRET
)

log = logging.getLogger(__name__)
def hash_password(password: str):
    """Hash a password using bcrypt"""
    pw = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pw, salt)

class TodolistUser(Base, TimeStampMixin):
    """SQLAlchemy model for a Todolist User."""

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    password = Column(LargeBinary, nullable=False)
    is_verified = Column(Boolean, default=False)

    otp = relationship("OtpModel", back_populates="user", uselist=False)
    todolist = relationship("Todolist", back_populates="user", cascade="all, delete-orphan")
    task = relationship("TodolistTask", back_populates="user")
    memberships = relationship("TodolistMembers", back_populates="user")

    def set_password(self, password: str):
        """Set a user password before saving to the db"""
        if not password:
            raise ValueError("Password must be provided")
        self.password = hash_password(password)

    def verify_password(self, password: str) -> bool:
        """Check if provided password matches hashed password"""
        if not password or not self.password:
            log.info(f"verify_password failed: password={password!r}, self.password={self.password!r}")
            return False
        return bcrypt.checkpw(password.encode("utf-8"), self.password)
    
    @property
    def token(self):
        """Generate a JWT Token for the user"""
        now = datetime.now(timezone.utc)
        exp = (now + timedelta(seconds=TODOLIST_JWT_EXP)).timestamp()
        data = {
            "sub": str(self.id),
            "exp": exp,
            "email": self.email
        }
        return jwt.encode(data, TODOLIST_JWT_SECRET, algorithm=TODOLIST_JWT_ALG) #TODO implement refresh_token for token blacklisting 
    

class OtpModel(Base, TimeStampMixin):
    """SQLAlchemy model for otp"""

    id = Column(Integer, primary_key=True)
    otp_code = Column(String, nullable=False)
    otp_expires = Column(DateTime)
    user_id = Column(Integer, ForeignKey("todolist_user.id"), nullable=False)
    is_used = Column(Boolean, default=False)

    user = relationship(TodolistUser, back_populates="otp", uselist=False)


class UserCreate(ToDoListBase):
    email: EmailStr
    password: str | None = None
    first_name: NameStr
    last_name: NameStr

    # @field_validator("password", mode="before")
    # @classmethod
    # def hash(cls, v):
    #     """hash password before storing"""
    #     return hash_password(str(v))


class UserRead(ToDoListBase):
    """Pydabtic model to read User."""
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    is_verified: bool
    created_at: datetime
    updated_at: datetime

class OtpCode(ToDoListBase):
    """Pydantic model for user otp"""

    otp_code: str


class UserInfo(ToDoListBase):
    """Response model for user info"""
    
    id: int
    email: EmailStr
    first_name: NameStr
    last_name: NameStr

class UserLogin(ToDoListBase):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_validator(cls, v):
        """Ensure password field is not empty"""
        if not v:
            raise ValidationError("password field can not be empty")
        return v


class UserAuthResponse(ToDoListBase):
    """Pydantic model for user register response"""

    detail: str
    token: str | None = None

class UserPasswordReset(ToDoListBase):
    """Pydantic model for user password resets."""

    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v):
        """Validate the new password for length and complexity."""
        if not v or len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        if not (any(c.isupper() for c in v) and any(c.islower() for c in v)):
            raise ValueError("Password must contain both uppercase and lowercase characters")
        return v