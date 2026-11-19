import "server-only";
import snapshot from "./release-snapshot.json";

function csvField(value: string | number | null | undefined) {
  const text = String(value ?? "");
  return /[",\r\n]/.test(text) ? '"' + text.replaceAll('"', '""') + '"' : text;
}

export function snapshotResponse(url: URL) {
  if (url.pathname === "/api/v1/datasets") return Response.json(snapshot.catalog);
  if (url.pathname === "/api/v1/policy-events") {
    const region = url.searchParams.get("jurisdiction");
    return Response.json(snapshot.events.filter((event) => !region || event.jurisdiction === region));
  }
  const match = /^\/api\/v1\/employment\/(laus|cps|jolts)(\/csv)?$/.exec(url.pathname);
  if (!match) return new Response(null, { status: 404 });
  const id = match[1] as keyof typeof snapshot.series;
  const latest = snapshot.series[id];
  const version = url.searchParams.get("version");
  const history: Record<string, typeof latest> = snapshot.history[id];
  const data = version && version !== latest.release.version ? history[version] : latest;
  if (!data) return new Response(null, { status: 404 });
  const start = url.searchParams.get("start") ?? data.release.first_month;
  const end = url.searchParams.get("end") ?? data.release.last_month;
  if (start > end) return new Response(null, { status: 422 });
  const observations = data.observations.filter((row) => row.month >= start && row.month <= end);
  if (!match[2]) return Response.json({ ...data, observations });
  const rows = observations.map((row) => {
    const note = (row.footnotes as string[]).join(" | ");
    return [row.month, row.value, data.source.unit, data.release.version,
      /^[\s]*[=+@-]|^[\t\r\n]/.test(note) ? "'" + note : note].map(csvField).join(",");
  });
  return new Response(["month,value,unit,dataset_version,footnotes", ...rows].join("\r\n") + "\r\n", {
    headers: { "Content-Type": "text/csv; charset=utf-8" },
  });
}
