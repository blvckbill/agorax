from datetime import datetime, timezone
from sqlalchemy import event
from sqlalchemy import Column, DateTime

from pydantic import ConfigDict, SecretStr, BaseModel, StringConstraints
from typing import ClassVar, Annotated


NameStr = Annotated[str, StringConstraints(pattern=r".*\S.*", strip_whitespace=True, min_length=3)]

#SQLAlchemy models
class TimeStampMixin(object):
    """Timestamping mixin for created_at and updated_at fields"""
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    @staticmethod
    def _updated_at(mapper, connection, target):
        """Updates the updated_at field to the current UTC time."""
        target.updated_at = datetime.now(timezone.utc)

    @classmethod
    def __declare_last__(cls):
        """Registers the before_update event to update the updated_at field."""
        event.listen(cls, "before_update", cls._updated_at)

#Pydantic models
class ToDoListBase(BaseModel):
    """Base Pydantic model with shared config for ToDoList models."""
    model_config: ClassVar[ConfigDict] = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
        str_strip_whitespace=True,
        json_encoders={
            # custom output conversion for datetime
            datetime: lambda v: v.strftime("%Y-%m-%dT%H:%M:%S.%fZ") if v else None,
            SecretStr: lambda v: v.get_secret_value() if v else None,
        },
    )


class Pagination(ToDoListBase):
    """Pydantic model for paginated results."""
    itemsPerPage: int
    page: int
    total: int
