import type { components } from "@aileo/api-client";
import { api } from "../../data";
import global from "../../global-releases.json";

export async function GET() {
  try {
    const response = await api("/api/v1/datasets");
    if (!response.ok) throw new Error("Unavailable");
    const catalog = await response.json() as components["schemas"]["Source"][];
    const sources = [
      ...catalog.filter((item) => item.series_id && item.dataset_version).map((item) => ({
        id: item.source_id,
        version: item.dataset_version,
        retrievedAt: item.last_successful_sync,
        coverage: item.temporal_coverage,
      })),
      ...global.map((item) => ({
        id: item.indicator,
        version: item.version,
        retrievedAt: item.retrieved_at,
        coverage: item.source_updated,
      })),
    ];
    return Response.json({ sources }, { headers: { "Cache-Control": "no-store" } });
  } catch {
    return Response.json({ error: "Release feed temporarily unavailable" }, { status: 503 });
  }
}
