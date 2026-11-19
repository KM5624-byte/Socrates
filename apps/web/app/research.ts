import "server-only";
import { createHash } from "node:crypto";
import { z } from "zod";
import type { components } from "@aileo/api-client";
import { api } from "./data";

const month = z.string().regex(/^\d{4}-(0[1-9]|1[0-2])$/);
export const specification = z.object({
  source: z.enum(["laus", "cps", "jolts"]),
  method: z.enum(["summary", "endpoint-change", "policy-coverage"]),
  start: z.union([month, z.literal("")]).default(""),
  end: z.union([month, z.literal("")]).default(""),
  version: z.string().regex(/^[0-9a-f]{64}$/).optional(),
}).refine(({start, end}) => !start || !end || start <= end, { message: "Start month must precede end month." });

export async function runResearch(input: z.infer<typeof specification>) {
  const filters = new URLSearchParams();
  if (input.start) filters.set("start", input.start);
  if (input.end) filters.set("end", input.end);
  if (input.version) filters.set("version", input.version);
  const response = await api(`/api/v1/employment/${input.source}?${filters}`);
  if (!response.ok) throw new Error("The selected release could not be loaded.");
  const data = await response.json() as components["schemas"]["Series"];
  const rows = data.observations;
  const values = rows.flatMap((row) => row.value === null ? [] : [row.value]);
  const metrics = [
    { label: "Months returned", value: rows.length },
    { label: "Observed values", value: values.length },
    { label: "Missing values", value: rows.length - values.length },
  ];
  if (input.method === "summary" && values.length) {
    const ordered = [...values].sort((a, b) => a - b);
    const center = Math.floor(ordered.length / 2);
    metrics.push(
      { label: "Mean", value: values.reduce((sum, x) => sum + x, 0) / values.length },
      { label: "Median", value: (ordered[center] + ordered[Math.ceil(ordered.length / 2) - 1]) / 2 },
      { label: "Minimum", value: ordered[0] },
      { label: "Maximum", value: ordered[ordered.length - 1] },
    );
  }
  const diagnostics = [data.source.known_limitations];
  if (!values.length) diagnostics.push("The selected window contains no numerical observations.");
  if (input.method === "endpoint-change") {
    const first = rows[0]?.value;
    const last = rows.at(-1)?.value;
    if (rows.length < 2 || first == null || last == null) {
      diagnostics.push("Endpoint change requires two distinct months with values at both endpoints.");
    } else {
      metrics.push({label:"First value",value:first},{label:"Last value",value:last},{label:"Absolute change",value:last - first});
      diagnostics.push(data.source.unit === "percent" ? "Change is in percentage points." : "Change is in the publisher's source units.");
    }
  }
  if (input.method === "policy-coverage") {
    const event = "2023-07";
    const before = rows.filter((row) => row.month < event && row.value !== null).length;
    const during = rows.filter((row) => row.month === event && row.value !== null).length;
    const after = rows.filter((row) => row.month > event && row.value !== null).length;
    metrics.push({label:"Before enforcement month",value:before},{label:"Enforcement month",value:during},{label:"After enforcement month",value:after});
    diagnostics.push("Identification unsupported. The outcome geography differs from New York City and the specification has no comparison group.");
  }
  const payload = {
    engine: "socrates-research-v1",
    method: input.method,
    inference: input.method === "policy-coverage" ? "identification_unsupported" : input.method === "endpoint-change" ? "deterministic" : "descriptive",
    input: { ...input, version: data.release.version },
    geography: data.source.geographic_coverage,
    unit: data.source.unit,
    source: data.source.canonical_url,
    policySource: input.method === "policy-coverage" ? "https://www.nyc.gov/site/dca/about/automated-employment-decision-tools.page" : null,
    metrics, diagnostics,
  };
  return { runId: createHash("sha256").update(JSON.stringify(payload)).digest("hex"), ...payload };
}
