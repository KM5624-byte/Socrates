import Link from "next/link";
import { Activity, ArrowDownToLine, Database, Landmark, Scale, ChartNoAxesCombined } from "lucide-react";
import { z } from "zod";
import type { components } from "@aileo/api-client";
import Chart from "../components/series-chart";
import { api } from "./data";

type Series = components["schemas"]["Series"];
type Source = components["schemas"]["Source"];
type Event = components["schemas"]["PolicyEvent"];
const month = z.string().regex(/^\d{4}-(0[1-9]|1[0-2])$/);
const seriesIds = ["laus", "cps", "jolts"] as const;

async function get<T>(path: string): Promise<T | null> {
  try {
    const response = await api(path);
    return response.ok ? await response.json() as T : null;
  } catch {
    return null;
  }
}

export default async function Home({ searchParams }: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const query = await searchParams;
  const source = z.enum(seriesIds).catch("laus").parse(query.source);
  const jurisdiction = query.jurisdiction === "eu" ? "European Union" : "New York City";
  const startMonth = month.safeParse(query.start);
  const endMonth = month.safeParse(query.end);
  const start = startMonth.success ? startMonth.data : "";
  const end = endMonth.success ? endMonth.data : "";
  const invalid = (query.start && !start) || (query.end && !end) || (start && end && start > end);
  const filter = new URLSearchParams();
  if (start && !invalid) filter.set("start", start);
  if (end && !invalid) filter.set("end", end);
  const [data, events, catalog] = await Promise.all([
    get<Series>(`/api/v1/employment/${source}?${filter}`),
    get<Event[]>(`/api/v1/policy-events?jurisdiction=${encodeURIComponent(jurisdiction)}`),
    get<Source[]>("/api/v1/datasets"),
  ]);
  const overlay = source === "laus" && jurisdiction === "New York City" ? events ?? [] : [];
  const selected = data?.observations ?? [];
  const exportParams = data && new URLSearchParams({
    source, version: data.release.version, start: start && !invalid ? start : data.release.first_month,
    end: end && !invalid ? end : data.release.last_month,
  });
  return <>
    <a className="skip" href="#main">Skip to content</a>
    <header className="top">
      <div className="shell masthead">
        <Link href="/" className="brand"><span className="mark"><Activity size={21} /></span><strong>AILEO</strong></Link>
        <nav aria-label="Main navigation"><a href="#explore">Labor market</a><a href="#policy">Regulation</a><a href="#catalog">Data catalog</a><a href="#methods">Methods</a></nav>
      </div>
    </header>
    <main id="main" className="shell">
      <section className="intro">
        <p className="eyebrow"><Landmark size={15} /> PUBLIC RESEARCH OBSERVATORY</p>
        <h1>AI Labor &amp; Employment<br className="wide" /> Observatory</h1>
        <p>Explore labor-market estimates, trace AI hiring regulations to primary sources, and download versioned data for reproducible research.</p>
        <a className="button primary" href="#explore"><ChartNoAxesCombined size={17} /> Explore the data</a>
      </section>
      <div className="workspace" id="explore">
        <section className="panel series" aria-labelledby="series-title">
          <div className="panel-top"><span className="eyebrow"><ChartNoAxesCombined size={15} /> LABOR MARKET</span><span className="badge">Published estimates</span></div>
          <h2 id="series-title">{data?.source.dataset_name ?? "Labor-market series"}</h2>
          {data && <p className="subtitle">{data.source.geographic_coverage} · {data.source.adjustment} · {data.source.program}</p>}
          <form action="/#explore" method="get" className="filters">
            {jurisdiction === "European Union" && <input type="hidden" name="jurisdiction" value="eu" />}
            <label>Indicator<select name="source" defaultValue={source}>
              <option value="laus">New York County unemployment</option><option value="cps">U.S. unemployment</option><option value="jolts">U.S. job openings</option>
            </select></label>
            <label>From<input type="month" name="start" defaultValue={start || data?.release.first_month} /></label>
            <label>To<input type="month" name="end" defaultValue={end || data?.release.last_month} /></label>
            <button className="button" type="submit">Apply filters</button>
          </form>
          {invalid && <p role="alert">Use an ascending month range in YYYY-MM format. Showing full release coverage.</p>}
          {!data ? <p role="status">The data service is unavailable. Reload the page to try again.</p>
            : selected.length === 0 ? <p>No observations in this range. The release covers {data.release.first_month} through {data.release.last_month}.</p>
            : <>
              <Chart data={data} events={overlay} />
              {overlay.some((event) => selected.some((row) => row.month === event.date.slice(0, 7))) &&
                <p className="small legend"><span aria-hidden="true" /> Dashed lines indicate months with a policy milestone.</p>}
              <details><summary>View monthly values and source notes</summary>
                <div className="scroll"><table><caption>{data.source.dataset_name} ({data.source.unit})</caption><thead><tr><th scope="col">Month</th><th scope="col">Value</th><th scope="col">Source notes</th></tr></thead>
                  <tbody>{selected.map((row) => <tr key={row.month}><th scope="row">{row.month}</th><td>{row.value ?? "Unavailable"}</td><td>{row.footnotes.join(" · ") || "—"}</td></tr>)}</tbody></table></div>
              </details>
            </>}
          {data && <footer className="series-footer">
            <p className="small"><a href={data.source.canonical_url}>BLS · {data.source.series_id}</a><br />Release <code title={data.release.version}>{data.release.version.slice(0, 12)}</code> · {data.release.first_month}–{data.release.last_month}</p>
            {selected.length > 0 && <a className="button" href={`/api/export?${exportParams}`}><ArrowDownToLine size={16} /> CSV</a>}
          </footer>}
        </section>
        <section className="panel timeline" id="policy" aria-labelledby="policy-title">
          <p className="eyebrow"><Scale size={16} /> REGULATION</p>
          <h2 id="policy-title">{jurisdiction === "European Union" ? "EU AI Act" : "NYC Local Law 144"}</h2>
          <p className="subtitle">{jurisdiction}</p>
          <form action="/#policy" method="get" className="filters">
            <input type="hidden" name="source" value={source} />
            {start && <input type="hidden" name="start" value={start} />}
            {end && <input type="hidden" name="end" value={end} />}
            <label>Jurisdiction<select name="jurisdiction" defaultValue={jurisdiction === "European Union" ? "eu" : "nyc"}>
              <option value="nyc">New York City</option><option value="eu">European Union</option>
            </select></label><button className="button" type="submit">Show timeline</button>
          </form>
          {events ? <ol>{events.map((event) => <li key={event.id}><time dateTime={event.date}>{event.date}</time>
            <h3>{event.kind}</h3><p>{event.summary}</p><a href={event.source_url}>Primary source</a>
          </li>)}</ol> : <p role="status">The policy timeline is temporarily unavailable.</p>}
        </section>
      </div>
      <section className="methods" id="methods">
        <h2>How to interpret this view</h2>
        <p>{data?.source.known_limitations} Policy dates provide context for labor-market trends. Estimating a policy effect requires a defensible comparison group, a matching geography, and a separate identification strategy.</p>
        {data?.source.methodology_url && <a href={data.source.methodology_url}>BLS program methodology</a>}
      </section>
      <section id="catalog" className="catalog">
        <p className="eyebrow"><Database size={15} /> PROVENANCE</p><h2>Data catalog</h2>
        {catalog ? <div className="scroll"><table><thead><tr><th scope="col">Dataset</th><th scope="col">Coverage</th><th scope="col">Status</th><th scope="col">Reuse</th></tr></thead>
          <tbody>{catalog.map((item) => <tr key={item.source_id}>
            <th scope="row"><a href={item.canonical_url}>{item.dataset_name}</a><small>{item.publisher}</small></th>
            <td>{item.geographic_coverage}<small>{item.temporal_coverage}</small></td>
            <td>{item.retrieval_status}{item.dataset_version && <small><code title={item.dataset_version}>{item.dataset_version.slice(0, 12)}</code></small>}</td>
            <td>{item.license_url ? <a href={item.license_url}>{item.license}</a> : item.license}{item.source_id === "onet" && <small>{item.attribution}</small>}</td></tr>)}</tbody></table></div> : <p role="status">The catalog is temporarily unavailable.</p>}
      </section>
    </main>
    <footer className="bottom"><div className="shell">AILEO · AI Labor &amp; Employment Observatory</div></footer>
  </>;
}
