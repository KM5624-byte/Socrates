import { runResearch, specification } from "../../research";

export async function GET(request: Request) {
  const parsed = specification.safeParse(Object.fromEntries(new URL(request.url).searchParams));
  if (!parsed.success) return Response.json({ error: "Invalid research specification." }, { status: 422 });
  try {
    const result = await runResearch(parsed.data);
    return Response.json(result, {
      headers: { "Content-Disposition": `attachment; filename="socrates-${result.runId.slice(0, 12)}.json"` },
    });
  } catch {
    return Response.json({ error: "Research release unavailable." }, { status: 503 });
  }
}
