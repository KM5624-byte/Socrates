# 0001 · Separate web delivery, serving, and research execution

Vercel runs the Next.js App Router. Its server layer calls FastAPI over HTTPS. Cloud Run serves the API and is the target for independent research and ingestion jobs. Local services use the same read-only release interface as the Cloud Run image.

The initial API serves immutable aggregate Parquet snapshots through DuckDB. Registry and policy reference records live in Git. A transactional PostgreSQL layer becomes necessary for user-owned state, review and job metadata. Bronze source bytes and Silver normalized rows stay outside Git. An intentionally small Gold release ships alongside a manifest for cold-start reproducibility.

Public results may be descriptive. Forecast experiments carry evaluation metadata. Causal study execution requires separate identification diagnostics and review. Legal-policy records preserve distinct milestones and source citations.
