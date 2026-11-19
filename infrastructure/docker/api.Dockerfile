FROM ghcr.io/astral-sh/uv:0.13.9 AS uv
FROM python:3.12-slim
WORKDIR /opt/aileo
COPY --from=uv /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY services/api/ services/api/
COPY data/registry/ data/registry/
COPY data/releases/ data/releases/
RUN useradd --system --uid 10001 aileo
USER aileo
ENV PORT=8080
CMD ["sh", "-c", "exec .venv/bin/uvicorn aileo.main:app --app-dir services/api --host 0.0.0.0 --port \"$PORT\""]
