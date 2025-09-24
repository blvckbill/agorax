import logging

from fastapi import Query, Depends

from sqlalchemy.exc import ProgrammingError
from sqlalchemy_filters import apply_pagination

from typing import Annotated

from .core import get_class_by_tablename, DbSession

log = logging.getLogger(__name__)

def paginate(
    db_session,
    model: str,
    page: int = 1,
    items_per_page: int = 10
):
    """Functionality for pagination."""
    model_cls = get_class_by_tablename(model)

    try:
        query = db_session.query(model_cls)

        # apply pagination
        query, pagination = apply_pagination(
            query,
            page_number=page,
            page_size=items_per_page
        )

        items = query.all()

    except ProgrammingError as e:
        log.debug(e)
        return {
            "items": [],
            "itemsPerPage": items_per_page,
            "page": page,
            "total": 0,
            "numPages": 0,
        }

    return {
        "items": items,
        "itemsPerPage": pagination.page_size,
        "page": pagination.page_number,
        "total": pagination.total_results,
        "numPages": pagination.num_pages,
    }

def pagination_parameters(
    db_session: DbSession,
    page: int = Query(1, gt=0, lt=2147483647),
    items_per_page: int = Query(10, alias="itemsPerPage", gt=-2, lt=2147483647),
):
    return {
        "db_session": db_session,
        "page": page,
        "items_per_page": items_per_page,
    }


PaginationParameters = Annotated[
    dict[str, int | DbSession],
    Depends(pagination_parameters),
]
