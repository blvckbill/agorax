import re

from contextlib import contextmanager

from fastapi import Depends

from pydantic import ValidationError, BaseModel

from starlette.requests import Request

from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase, declared_attr

from src.todolist import config
from src.todolist.database.logging import SessionTracker

from typing import Annotated, Any, Generator

def create_db_engine(connection_string: str):
    """Create a database engine with proper timeout settings.

    Args:
        connection_string: Database connection string
    """

    url = make_url(connection_string)

    #custom connection settings for database cinnection pool
    timeout_kwargs = {
        "pool_size" : config.DATABASE_ENGINE_POOL_SIZE,
        "max_overflow" : config.DATABASE_ENGINE_MAX_OVERFLOW,
        "pool_recycle" : config.DATABASE_ENGINE_POOL_RECYCLE,
        "pool_timeout" : config.DATABASE_ENGINE_POOL_TIMEOUT,
        "pool_pre_ping" : config.DATABASE_ENGINE_POOL_PING
    }

    return create_engine(url, **timeout_kwargs)

#create database engine with standard timeout
engine = create_db_engine(
    config.SQLALCHEMY_DATABASE_URI
)

SessionLocal = sessionmaker(bind=engine)

def resolve_table_name(name):
    """Resolve table names for their mapped names"""
    names = re.split("(?=[A-Z])", name)
    return "_".join([x.lower() for x in names if x])
    

class Base(DeclarativeBase):
    """Base class for all SQLALchemy models"""
    @declared_attr.directive
    def __tablename__(cls):
        return resolve_table_name(cls.__name__)
    
    def dict(self):
        """Returns a dict representation of a model"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
def get_db(request: Request) -> Session:
    """Get database session from request state."""
    session = request.state.db
    if not hasattr(session, "_todolist_session_id"):
        session._todolist_session_id = SessionTracker.track_session(
            session, context="fastapi_request"
        )
    return session


DbSession = Annotated[Session, Depends(get_db)]

def get_modelname_by_tabelname(table_fullname: str) -> Any:
    """Returns the model name of a give table"""
    return get_class_by_tablename(table_fullname=table_fullname).__name__


def get_class_by_tablename(table_fullname: str) -> Any:
    """Return class reference mapped to table"""
    
    def _find_class(name):
        for mapper in Base.registry.mappers:
            cls = mapper.class_
            if hasattr(cls, "__table__"):
                return cls
        
    mapped_name = resolve_table_name(table_fullname)
    mapped_class = _find_class(mapped_name)

    if not mapped_class:
        raise ValidationError(
            [
                {
                    "type": "value_error",
                    "loc": ("filter",),
                    "msg": "Model not found. Check the name of your model.",
                }
            ],
            model=BaseModel,
        )

    return mapped_class

    

@contextmanager
def get_session():
    """Context manager to ensure session is closed after use"""
    session = SessionLocal()
    session_id = SessionTracker.track_session(session, context="context_manager")
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        SessionTracker.untrack_session(session_id)
        session.close()