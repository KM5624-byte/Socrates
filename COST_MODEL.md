# Cost model

The local pilot requires no managed infrastructure. The cloud pilot adds Vercel requests/compute, Cloud Run CPU and memory, image storage and logging. Use usage volumes and region-specific prices before approval. The Terraform pilot bounds scale at two instances with zero minimums. Budget alerts and workload quotas remain to be provisioned.

For the production forecast, separately estimate persistent database, object storage and egress, research job minutes and scheduled ingestion. Base the estimate on measured request and job profiles. The pilot has no automatic retraining schedule.
