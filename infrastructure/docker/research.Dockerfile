FROM ghcr.io/astral-sh/uv:0.13.9 AS uv
FROM python:3.12-slim
WORKDIR /opt/aileo
COPY --from=uv /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --group research --group ingest --no-install-project
COPY research/ research/
COPY pipelines/ pipelines/
COPY data/registry/ data/registry/
COPY data/releases/ data/releases/
RUN useradd --create-home --uid 10001 aileo && mkdir -p research/output && chown aileo research/output
USER aileo
ENV PATH=/opt/aileo/.venv/bin:$PATH PYTHONPATH=/opt/aileo
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--no-browser", "--KernelManager.transport=ipc"]
