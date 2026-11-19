# Implementation status

The first source-to-dashboard pilot runs locally. The full AILEO directive remains in progress. See the [roadmap](ROADMAP.md) for sequencing and the [acquisition report](DATA_SOURCES.md) for dataset-specific next actions.

| Capability | Status | Verified scope and remaining work |
| --- | --- | --- |
| Monorepo and local runtime | Complete for pilot | Frozen pnpm and uv installs, Next.js production build, FastAPI readiness, research toolchain |
| Source discovery | Partial | 20 source records. Product-specific licenses, schemas, schedules, revisions and storage estimates remain incomplete |
| CPS, LAUS, JOLTS | Verified | 108 total monthly observations, zero missing in the 2022–2024 window, pinned publisher responses and replay tests |
| O*NET | Verified subset | 1,016 valid 31.0 occupation definitions via searchable API. Tasks, skills, historical releases and crosswalks remain open |
| Bronze, Silver and Gold | Verified locally | Versioned files, atomic writes, checksums and Parquet. Durable object storage, refresh scheduling and retries remain open |
| Public overview and labor explorer | Verified pilot | Real charts, indicator and month filtering, readable data table and version-pinned CSV |
| Regulation explorer | Verified pilot | NYC and EU selection, source links and distinct legal milestones. Provision-level obligations and amendment history remain open |
| Policy and outcomes | Partial | NYC dates over a Manhattan unemployment series, with explicit coverage limitations. Matched comparison geography, subgroup filters and formal tests remain open |
| Audit study | Partial and reuse-dependent | Capture contracts and denominator tests. Historical ACLU reuse scope and third-party report rights require review. The research corpus, descriptive results, UI and longitudinal analysis remain open |
| Data catalog and API | Verified pilot | Release-backed statuses and manifests, occupation search, export, OpenAPI and health endpoints |
| Research workbench and model lab | Planned | No general-purpose workbench, authenticated queue or persistent model registry |
| Descriptive and predictive baselines | Verified locally | Pinned CPS profile and rolling one-month persistence, with 2024 holdout errors checked to tolerance |
| Causal research | Partial | Pinned policy coverage diagnostic records inadequate identification. No estimator, specification lock, trial workflow or causal output |
| Bayesian, simulation, NLP and graphs | Planned | Separate execution environments and model implementations remain open |
| Notebook environment | Partial | Two executed and versioned notebooks. Container recipe and loopback Jupyter configuration provided. Hosted jobs and remaining studies are planned |
| CI and security | Verified locally and CI configured | Python, TypeScript, browser and dependency checks run locally. Hosted CI and container builds remain unverified |
| Auth, roles, database and operations | Planned | OIDC, PostgreSQL/Alembic, Redis/queues, review state, production monitoring and admin UI remain open |
| Deployment | Configured and partially validated | Terraform format and validation succeeded. Vercel and container configs provided. Docker unavailable locally. Live deploy and smoke tests require authorized Vercel and Google Cloud projects and identities |

## Runtime versions

Local verification used Node.js 24.22.3, pnpm 10.34.8, Turborepo 2.11.13, Next.js 16.4.6, React 19.3.1, TypeScript 5.9, Tailwind 4.3.5, Python 3.12.16, FastAPI 0.165.0, Pydantic 2.14.3, DuckDB 1.5.6, Polars 1.44.2 and JupyterLab 4.6.6. Terraform 1.13.5 validated against Google provider 7.46.2.

## Research interpretation

The pilot displays published estimates and separately identified policy events. It makes no claim about employment impacts, audit compliance, or discrimination. The historical data window ends in December 2024. The 2025 New York State oversight milestone lies outside it.

## Verification record

- 15 pytest checks passed, including raw BLS replay, missingness, duplicate rejection, release immutability, OpenAPI drift, CSV parity, O*NET search, and audit rubric behavior.
- Three Playwright checks passed against fresh production-mode local services. They cover filters and CSV, mobile layout and automated accessibility checks, and EU timeline selection.
- Both parameterized notebooks executed. The pinned CPS baseline reproduced MAE 0.075 and RMSE 0.1040832999733067 percentage points. The policy notebook recorded unsupported causal identification.
- Type checking, ESLint, Ruff, production build, Terraform validation, and npm and core Python dependency audits passed. Python test output includes an upstream Starlette TestClient deprecation warning.

The Vercel read-only fallback serves the pinned pilot without Cloud Run when no upstream is configured. The three production-mode Playwright tests also passed with the fallback enabled.

## Socrates app and research workbench

- Routed overview, labor, regulation, catalog, methodology and workbench pages share a responsive navigation shell. The catalog supports search and validated-release filtering.
- The Vercel gateway runs descriptive summaries, deterministic endpoint changes and NYC design-coverage diagnostics on pinned data, with downloadable run records.
- The Python notebook study router runs summaries, deterministic endpoints, Ridge with a persistence baseline, and seeded Monte Carlo. Its causal route rejects unsupported identification with the single-series pilot data.
- Hosted notebook execution, the PostgreSQL job layer, authorization and durable object storage are outstanding. Public requests cannot submit arbitrary code or start Jupyter kernels.
