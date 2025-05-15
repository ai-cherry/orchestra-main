FROM python:3.11-slim AS base
ENV PIP_DISABLE_PIP_VERSION_CHECK=on \
    PYTHONUNBUFFERED=1
WORKDIR /app
COPY poetry.lock pyproject.toml ./
RUN pip install --no-cache-dir poetry==1.8.2 \
 && poetry install --only main --no-dev

FROM base AS runtime
COPY services/admin-api /services/admin-api
CMD ["poetry", "run", "uvicorn", "admin_api.main:app", "--host", "0.0.0.0", "--port", "8080"]
