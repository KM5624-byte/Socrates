# Threat model

| Boundary | Current control | Outstanding control |
| --- | --- | --- |
| Public read traffic | Bounded queries, fixed routes, request IDs and Cloud Run resource limits | Rate limiting, load tests, monitoring and alert thresholds |
| Ingestion source | Fixed hosts, no redirects, timeout, size bound, schema validation | Central egress and integrity monitoring, bounded retries |
| Release artifacts | Immutable file creation, manifests and checksums | Signed release promotion, durable object store and restoration drills |
| Browser | Same-origin CSV gateway, server-only API URL, restrictive framing and MIME headers | CSP compatible with chart rendering and independent accessibility/security review |
| Research | Loopback Jupyter and isolated dependencies | Private job runner, OIDC roles, resource quotas and audit trails |
| Documents | Curated links and no untrusted document execution | Sandboxed parsing, evidence review and injection isolation before NLP |
