# Operations runbook

- Check `/healthz` for a live process and `/readyz` for the integrity of packed releases. Inspect JSON request logs using the request ID.
- Acquire releases in a writable workspace. Capture log output, compare missingness and run tests before including a release in an image. Failed validation leaves prior manifests intact.
- To recover a pinned release, restore the release directory from the Git revision or known image digest. Confirm the SHA-256 against the manifest and run API contract tests before promotion.
- If the public web cannot load data, check environment-specific API URL, Cloud Run ingress, readiness and deadline errors. Revert to the previous deployment if the new revision fails validation.
- Track data age using the last observation and retrieval date separately. The pilot has no scheduler, managed backups or automated alert notifications.
