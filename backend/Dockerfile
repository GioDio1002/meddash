FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON=/usr/local/bin/python3.12

WORKDIR /app/backend

COPY backend/pyproject.toml backend/uv.lock backend/README.md backend/.python-version ./
COPY backend/src ./src

RUN uv sync --frozen --no-dev --python /usr/local/bin/python3.12

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app/src" \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=builder /app/backend/.venv /app/.venv
COPY --from=builder /app/backend/src /app/src
COPY backend/pyproject.toml backend/README.md ./

EXPOSE 8000

CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
