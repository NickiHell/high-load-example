#!/bin/sh
set -e
cd /app
export PYTHONPATH=/app/src
uv run alembic upgrade head
exec uv run uvicorn positions_service.main:app --host 0.0.0.0 --port 8000 --workers "${UVICORN_WORKERS:-1}"
