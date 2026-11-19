# AILEO · AI Labor & Employment Observatory

A public research platform for exploring published labor-market estimates and tracing AI regulation to primary sources. The pilot serves real BLS and O*NET releases through FastAPI and DuckDB, with a server-rendered Next.js interface and a separate notebook environment.

See [implementation status](IMPLEMENTATION_STATUS.md), [architecture](ARCHITECTURE.md), [source acquisition](DATA_SOURCES.md), and [deployment](DEPLOYMENT.md).

## Local development

Install Node.js 24, pnpm 10.34.8 and uv. Run these commands from the repository root.

```sh
pnpm install --frozen-lockfile
uv sync --locked --group ingest --group research
uv run --locked uvicorn aileo.main:app --app-dir services/api --host 127.0.0.1 --port 8000
```

In a second terminal, run `pnpm dev` and open http://localhost:3000. OpenAPI documentation is at http://127.0.0.1:8000/docs. The default API URL works locally. Set `AILEO_API_URL` in `apps/web/.env.local` for a different service.

Serve a frozen release with `docker compose up --build api`. To start isolated and token-authenticated JupyterLab with Compose, run `docker compose --profile research up --build notebook` and use the loopback token URL in the logs. For local JupyterLab without Docker, run `uv run --locked --group research jupyter lab --ip=127.0.0.1 --KernelManager.transport=ipc`.

## Acquire and verify

```sh
uv run --locked --group ingest python -m pipelines.ingest cps laus jolts --start 2022 --end 2024
uv run --locked --group ingest python -m pipelines.onet
uv run --locked --group ingest pytest
uv run --locked ruff check services/api pipelines research tests
pnpm check
pnpm build
pnpm exec playwright install chromium
pnpm exec playwright test
uv run --locked --group research bash scripts/reproduce-notebook
```

Live acquisition can return a revised source vintage. The pinned notebook always reads its designated release. It writes an executed notebook under `research/output/`, with exact expected errors checked to an absolute tolerance of `1e-10`. The three small BLS Bronze responses are checked in for independent replay. O*NET Bronze and other new raw artifacts are stored under the ignored `.lake/` directory.

## Repository

| Directory | Purpose |
| --- | --- |
| `apps/web` | Next.js public observatory and CSV gateway |
| `services/api` | FastAPI contracts, routes and read-only repositories |
| `packages/api-client` | OpenAPI snapshot and generated TypeScript contract |
| `pipelines` | Bounded source connectors, normalizers and release writers |
| `data` | Registry, pinned Gold artifacts, manifests and small Bronze replay inputs |
| `research` | Research methods and parameterized notebook |
| `infrastructure` | Container recipes and Cloud Run configuration |
| `tests` | Ingestion, contract, research and Playwright tests |
| `docs/adr` | Architecture decisions |
