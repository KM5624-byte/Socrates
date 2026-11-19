import { z } from "zod";
import { api } from "../../data";

const request = z.object({
  source: z.enum(["laus", "cps", "jolts"]),
  version: z.string().regex(/^[a-f0-9]{64}$/),
  start: z.string().regex(/^\d{4}-(0[1-9]|1[0-2])$/),
  end: z.string().regex(/^\d{4}-(0[1-9]|1[0-2])$/),
});

export async function GET(req: Request) {
  const parsed = request.safeParse(Object.fromEntries(new URL(req.url).searchParams));
  if (!parsed.success) return new Response("Invalid export selection", { status: 400 });
  const { source, ...selection } = parsed.data;
  try {
    const response = await api(`/api/v1/employment/${source}/csv?${new URLSearchParams(selection)}`);
    if (!response.ok) return new Response("Export unavailable", { status: response.status === 404 ? 404 : 502 });
    return new Response(response.body, {
      headers: {
        "Content-Type": "text/csv; charset=utf-8",
        "Content-Disposition": `attachment; filename="${source}-${selection.version.slice(0, 12)}.csv"`,
      },
    });
  } catch {
    return new Response("Research data service unavailable", { status: 503 });
  }
}
