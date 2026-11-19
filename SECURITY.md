# Security

The pilot exposes only reviewed public aggregate datasets and curated reference records. Its API has no write or compute-submission routes. User-provided URLs are outside the ingestion interface. Source targets are configured or hardcoded, response sizes and timeouts are bounded, redirects are rejected, and DuckDB queries bind parameter values.

Keep Jupyter token authentication enabled and bind the host port to loopback. Do not distribute tokens or logs containing notebook access URLs. Report a vulnerability privately to the repository owner. See the [threat model](THREAT_MODEL.md) for outstanding controls.
