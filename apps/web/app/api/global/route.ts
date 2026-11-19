import releases from "../../global-releases.json";

export function GET(request: Request) {
  const indicator = new URL(request.url).searchParams.get("indicator");
  const release = indicator ? releases.find((item) => item.indicator === indicator) : releases[0];
  if (!release) return Response.json({ error: "Unknown global indicator." }, { status: 404 });
  return Response.json(release, {
    headers: { "Content-Disposition": `attachment; filename="world-bank-ilo-${release.version.slice(0, 12)}.json"` },
  });
}
