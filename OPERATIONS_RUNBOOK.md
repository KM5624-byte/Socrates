# Operations runbook

- Check `/healthz` for a live process and `/readyz` for the integrity of packed releases. Inspect JSON request logs using the request ID.
- Acquire releases in a writable workspace. Capture log output, compare missingness and run tests before including a release in an image. Failed validation leaves prior manifests intact.
- To recover a pinned release, restore the release directory from the Git revision or known image digest. Confirm the SHA-256 against the manifest and run API contract tests before promotion.
- If the public web cannot load data, check environment-specific API URL, Cloud Run ingress, readiness and deadline errors. Revert to the previous deployment if the new revision fails validation.
- Track data age using the last observation and retrieval date separately. The pilot has no scheduler, managed backups or automated alert notifications.

## Automated source refresh

GitHub Actions checks the three BLS series and three World Bank indicators every four hours UTC, independent of website traffic. Publisher cadence determines when observations can change. The job preserves missing values, rejects older reporting coverage, skips unchanged assertions, and keeps prior BLS versions available for citation and export. Unsuccessful publishers retain their last accepted release while other validated changes can proceed. A failed check is visible in the Actions run. The job uses GitHub's scoped automation token and triggers the repository's existing Vercel integration when approved release artifacts change.

The site checks its release endpoint every minute in visible tabs and refreshes the view on a changed release. Publisher release dates, pipeline checks, and Vercel build latency are distinct. Legal timelines and research notebooks remain separate from the recurring statistical refresh.
