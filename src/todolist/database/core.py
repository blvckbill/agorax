import re
from fastapi import Depends
from contextlib import contextmanager
from todolist import config
from starlette.requests import Request
from typing import Annotated, Any, Generator
from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase, declared_attr
from todolist.database.logging import SessionTracker

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
    names = re.split("?=[A-Z]", name)
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

@contextmanager
def get_session() -> Generator[Session]:
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