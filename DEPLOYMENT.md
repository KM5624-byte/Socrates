# Deployment

This procedure serves the aggregate, read-only pilot. Cloud Run, Artifact Registry, a Vercel project, deployment identity, billing authorization and permission to expose the public application are prerequisites. Use separate service names and environment settings for preview and production.

## Cloud Run

Use an existing authorized Artifact Registry repository and an authenticated gcloud session. Build a Linux image and resolve its digest before Terraform.

```sh
export AILEO_PROJECT=your-project
export AILEO_REGION=us-central1
export AILEO_REPOSITORY=your-existing-artifact-repository
export AILEO_IMAGE="$AILEO_REGION-docker.pkg.dev/$AILEO_PROJECT/$AILEO_REPOSITORY/aileo-api"
gcloud auth configure-docker "$AILEO_REGION-docker.pkg.dev"
docker buildx build --platform linux/amd64 -f infrastructure/docker/api.Dockerfile -t "$AILEO_IMAGE:pilot" --push .
gcloud artifacts docker images describe "$AILEO_IMAGE:pilot" --format='value(image_summary.digest)'
terraform -chdir=infrastructure/terraform init
terraform -chdir=infrastructure/terraform validate
terraform -chdir=infrastructure/terraform plan -out=pilot.tfplan \
  -var "project_id=$AILEO_PROJECT" -var "region=$AILEO_REGION" \
  -var 'service_name=aileo-api-preview' -var "image=$AILEO_IMAGE@sha256:REPLACE_WITH_DIGEST"
```

Review and apply the saved plan only when authorized. The default Cloud Run service requires IAM. Validate privately using `gcloud run services proxy aileo-api-preview --region "$AILEO_REGION"` and request `/readyz` on the proxy port. For an authorized public aggregate-only pilot, regenerate the plan with `-var public_read=true` and apply it. A private browser-facing deployment requires a separately implemented Vercel-to-Cloud Run identity exchange.

## Vercel

Import `KM5624-byte/Socrates` after the source is approved for publication. Set the root directory to `apps/web`, allow source files outside that directory, select Node.js 24 and keep framework defaults. Use the root pnpm lockfile. For exact pnpm resolution enable Corepack with `ENABLE_EXPERIMENTAL_COREPACK=1`. Set server-only `AILEO_API_URL` to the appropriate HTTPS Cloud Run URL in each environment. Build preview first. [Vercel monorepos](https://vercel.com/docs/monorepos) · [Vercel package managers](https://vercel.com/docs/package-managers)

Verify API readiness, release manifest and data across browser and CSV, invalid selections, and failure states before promotion. For rollback, redeploy the previous Vercel build and restore the previous Cloud Run revision or image digest. Preserve the release directories and manifests in all retained revisions.

The pilot has no mutable production database to migrate or restore. Managed PostgreSQL, future Alembic procedures, worker jobs and lifecycle-managed remote storage require a separate deployment milestone. Keep future credentials in provider secret stores and use short-lived workload identities. [Cloud Run runtime contract](https://docs.cloud.google.com/run/docs/container-contract)

## Read-only Vercel snapshot

With no `AILEO_API_URL` configured, Vercel serves the pinned public pilot release through the Next.js server. This mode provides the observatory, timeline, catalog, and CSV without requiring a Cloud Run account. It serves the release bundled at build time. To rebuild the bundle after verifying an updated release, run `PYTHONPATH=services/api uv run --locked python scripts/export-vercel-snapshot.py` and deploy the resulting Git revision. Set `AILEO_API_URL` to switch to FastAPI.
