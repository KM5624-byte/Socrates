# Contributing

Use pinned runtimes and lockfiles. Commit changes in working slices with a comparable real-data demonstration. Update the implementation ledger when a capability moves state.

Regenerate API types after modifying a Python route or contract.

```sh
PYTHONPATH=services/api uv run --locked python -c 'import json; from aileo.main import app; print(json.dumps(app.openapi(), indent=2))' > packages/api-client/openapi.json
pnpm api:generate
```

Validate imports, formatting, unit tests, OpenAPI, production web build, and tests for changed user flows. Keep benchmark inputs versioned. Development fixtures must be clearly synthetic and live outside public release paths.
