# API reference

The local API publishes Swagger UI at `/docs` and OpenAPI at `/openapi.json`. The [versioned contract](packages/api-client/openapi.json) is used to generate web types.

| GET endpoint | Use |
| --- | --- |
| `/healthz`, `/readyz` | Process and verified-release readiness |
| `/api/v1/datasets` | Source catalog and release status |
| `/api/v1/datasets/{source_id}/releases` | Available releases |
| `/api/v1/datasets/{source_id}/releases/{version}` | Manifest and lineage |
| `/api/v1/employment/{source_id}` | Monthly series, optional start/end and version |
| `/api/v1/employment/{source_id}/csv` | Same selection in CSV |
| `/api/v1/policy-events` | Curated timeline, optional exact jurisdiction |
| `/api/v1/occupations` | O*NET definitions, optional q, offset, limit and version |

Month bounds are inclusive. Values missing from the source are JSON null and empty CSV fields with notes. Unknown releases return 404. Invalid filters return 422. Record the request ID when investigating service errors.
