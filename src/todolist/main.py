import logging
from os import path

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, FileResponse
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.middleware.gzip import GZipMiddleware
from starlette.responses import StreamingResponse
from starlette.staticfiles import StaticFiles

from src.todolist.auth.views import auth_router
from src.todolist.tasks.views import task_router
from src.todolist.config import STATIC_DIR

# -------------------------------
# Logging
# -------------------------------
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# -------------------------------
# Exception Middleware
# -------------------------------
class ExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> StreamingResponse:
        try:
            response = await call_next(request)
        except ValidationError as e:
            log.exception(e)
            response = JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={"detail": e.errors()},
            )
        except ValueError as e:
            log.exception(e)
            response = JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={"detail": [{"msg": "Unknown", "loc": ["Unknown"], "type": "Unknown"}]},
            )
        except Exception as e:
            log.exception(e)
            response = JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": [{"msg": "Unknown", "loc": ["Unknown"], "type": "Unknown"}]},
            )
        return response

# -------------------------------
# Not Found handler
# -------------------------------
async def not_found(request: Request, exc):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": [{"msg": "Not Found."}]},
    )

# -------------------------------
# Frontend App (SPA)
# -------------------------------
frontend = FastAPI(openapi_url="")
frontend.add_middleware(GZipMiddleware, minimum_size=1000)

@frontend.middleware("http")
async def spa_fallback(request: Request, call_next):
    response = await call_next(request)
    # If 404, return index.html (SPA fallback)
    if response.status_code == 404 and STATIC_DIR:
        index_path = path.join(STATIC_DIR, "index.html")
        if path.exists(index_path):
            return FileResponse(index_path)
    return response

if STATIC_DIR and path.isdir(STATIC_DIR):
    frontend.mount("/", StaticFiles(directory=STATIC_DIR), name="frontend")

# -------------------------------
# API App
# -------------------------------
api = FastAPI(
    title="Todolist API",
    description="API for managing tasks and auth",
    root_path="/api/v1",
    docs_url="/docs",
    openapi_url="/docs/openapi.json",
    redoc_url=None,
)
api.add_middleware(GZipMiddleware, minimum_size=1000)
api.add_middleware(ExceptionMiddleware)

api.include_router(task_router, prefix="/tasks", tags=["Tasks"])
api.include_router(auth_router, prefix="/auth", tags=["Auth"])

@api.get("/")
def root():
    return {"message": "Welcome to Todolist API. Visit /docs for API documentation."}

# -------------------------------
# Main ASGI app
# -------------------------------
app = FastAPI(exception_handlers={404: not_found}, openapi_url="")
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Mount API and frontend
app.mount("/api/v1", app=api)
app.mount("/", app=frontend)
