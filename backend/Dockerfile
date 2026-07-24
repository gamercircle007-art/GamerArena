# Multi-stage Dockerfile for Paythan backend
# Stages: base -> development (hot reload) -> production (lean image)
# Render: uses production stage; PORT is injected by the platform.

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.4 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    PATH="/opt/poetry/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 -
WORKDIR /app

# poetry.lock is optional for first deploy; prefer committing lock for reproducibility
COPY pyproject.toml ./
COPY poetry.lock* ./
RUN if [ -f poetry.lock ]; then \
      poetry install --no-root --only main; \
    else \
      poetry lock && poetry install --no-root --only main; \
    fi

COPY . .
RUN chmod +x scripts/docker-entrypoint.sh scripts/render-start.sh

# --- Development: hot reload ---
FROM base AS development

RUN poetry install --no-root

EXPOSE 8000
ENTRYPOINT ["scripts/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# --- Production / Render: non-root, single worker by default (free tier) ---
FROM base AS production

RUN addgroup --system paythan && adduser --system --ingroup paythan paythan
USER paythan

EXPOSE 8000
# Render sets PORT; render-start.sh runs migrations then uvicorn
CMD ["bash", "scripts/render-start.sh"]
