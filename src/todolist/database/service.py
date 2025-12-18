import logging

from fastapi import Query, Depends

from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Query as sqlQuery
from sqlalchemy_filters import apply_pagination

from typing import Annotated

from .core import DbSession

log = logging.getLogger(__name__)

def paginate(
    query: sqlQuery,
    page: int = 1,
    items_per_page: int = 5
):
    """Functionality for pagination."""
    try:
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
    page: int = Query(1, gt=0, lt=2147483647),
    items_per_page: int = Query(10, alias="itemsPerPage", gt=-2, lt=2147483647),
):
    return {
        "page": page,
        "items_per_page": items_per_page,
    }


PaginationParameters = Annotated[
    dict[str, int],
    Depends(pagination_parameters),
]
