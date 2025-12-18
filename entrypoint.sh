#!/bin/bash

set -e

# Run migrations (Alembic)
alembic upgrade head

# start app
if [ "$#" -gt 0 ]; then
  exec "$@"
else
  exec uvicorn src.todolist.main:app --host 0.0.0.0 --port 8000
fi