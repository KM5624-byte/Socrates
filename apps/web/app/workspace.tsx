import Link from "next/link";
import { Activity, ArrowDownToLine, Database, Scale, ChartNoAxesCombined, FlaskConical, LayoutDashboard, BookOpen, Globe2 } from "lucide-react";
import { z } from "zod";
import type { components } from "@aileo/api-client";
import GlobalPanel from "./global-panel";
import ResearchPanel from "./research-panel";
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

export type Search = Promise<Record<string, string | string[] | undefined>>;
export const sections = [
  { id: "overview", label: "Overview", icon: LayoutDashboard, description: "Labor indicators, regulatory milestones, and source releases." },
  { id: "labor", label: "Labor market", icon: ChartNoAxesCombined, description: "Explore published labor-market estimates and export a pinned selection." },
  { id: "global", label: "Global comparisons", icon: Globe2, description: "Compare harmonized annual indicators with the United States as the reference." },
  { id: "regulations", label: "Regulation", icon: Scale, description: "Review jurisdiction-specific milestones and primary legal sources." },
  { id: "catalog", label: "Data catalog", icon: Database, description: "Inspect publisher, coverage, validation, and reuse terms." },
  { id: "research", label: "Research workbench", icon: FlaskConical, description: "Run supported analyses on versioned data and download reproducible results." },
  { id: "methods", label: "Methodology", icon: BookOpen, description: "Review source limits and evidence requirements before interpreting results." },
] as const;
type Section = typeof sections[number]["id"];

export default async function Workspace({ searchParams, section = "overview" }: {
  searchParams: Search;
  section?: Section;
}) {
  const view = sections.find((item) => item.id === section)!;
  const showLabor = section === "overview" || section === "labor";
  const showPolicy = section === "overview" || section === "regulations";
  const path = section === "overview" ? "/" : `/${section}`;
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
    (showLabor || section === "methods") ? get<Series>(`/api/v1/employment/${source}?${filter}`) : null,
    (showPolicy || showLabor) ? get<Event[]>(`/api/v1/policy-events?jurisdiction=${encodeURIComponent(jurisdiction)}`) : null,
    section === "catalog" ? get<Source[]>("/api/v1/datasets") : null,
  ]);
  const overlay = source === "laus" && jurisdiction === "New York City" ? (events || []) : [];
  const catalogTerm = typeof query.q === "string" ? query.q.trim().slice(0, 100) : "";
  const validatedOnly = query.validated === "yes";
  const catalogItems = catalog?.filter((item) =>
    (!validatedOnly || item.retrieval_status === "Validated") &&
    [item.dataset_name, item.publisher, item.geographic_coverage, item.series_id].some((value) =>
      value?.toLowerCase().includes(catalogTerm.toLowerCase())),
  );
  const selected = data?.observations ?? [];
  const exportParams = data && new URLSearchParams({
    source, version: data.release.version, start: start && !invalid ? start : data.release.first_month,
    end: end && !invalid ? end : data.release.last_month,
  });
  return <>
    <a className="skip" href="#main">Skip to content</a>
    <div className="app-shell">
    <aside className="side">
      <Link href="/" className="brand"><span className="mark"><Activity size={20} /></span><span><strong>Socrates</strong><small>AI & labor observatory</small></span></Link>
      <nav aria-label="Main navigation">
        {sections.map(({id, label, icon: Icon}) => <Link key={id} href={id === "overview" ? "/" : `/${id}`}
          aria-current={section === id ? "page" : undefined}><Icon size={18} aria-hidden="true" />{label}</Link>)}
      </nav>
    </aside>
    <div className="app-body">
    <header className="top"><div className="shell masthead">
      <span>Observatory <span aria-hidden="true">/</span> <strong>{view.label}</strong></span>
      <Link className="button" href="/research"><FlaskConical size={16} aria-hidden="true" /> Open workbench</Link>
    </div></header>
    <main id="main" className="shell">
      <section className="intro">
        <h1>{section === "overview" ? "AI Labor & Employment Observatory" : view.label}</h1>
        <p>{view.description}</p>
      </section>
      {section === "global" && <GlobalPanel selection={query.peer} indicator={query.indicator} />}
      {section === "research" && <ResearchPanel query={query} />}
      {(showLabor || showPolicy) && <div className={section === "overview" ? "workspace" : "workspace single"} id="explore">
        {showLabor &&         <section className="panel series" aria-labelledby="series-title">
          <div className="panel-top"><span className="eyebrow"><ChartNoAxesCombined size={15} /> LABOR MARKET</span><span className="badge">Published estimates</span></div>
          <h2 id="series-title">{data?.source.dataset_name ?? "Labor-market series"}</h2>
          {data && <p className="subtitle">{data.source.geographic_coverage} · {data.source.adjustment} · {data.source.program}</p>}
          <form action={`${path}#explore`} method="get" className="filters">
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
        </section>}
        {showPolicy && <section className="panel timeline" id="policy" aria-labelledby="policy-title">
          <p className="eyebrow"><Scale size={16} /> REGULATION</p>
          <h2 id="policy-title">{jurisdiction === "European Union" ? "EU AI Act" : "NYC Local Law 144"}</h2>
          <p className="subtitle">{jurisdiction}</p>
          <form action={`${path}#policy`} method="get" className="filters">
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
        </section>}
      </div>}
      {(section === "methods" || showLabor) && <section className="methods" id="methods">
        <h2>How to interpret this view</h2>
        <p>{data?.source.known_limitations} Policy dates provide context for labor-market trends. Estimating a policy effect requires a defensible comparison group, a matching geography, and a separate identification strategy.</p>
        {data?.source.methodology_url && <a href={data.source.methodology_url}>BLS program methodology</a>}
      </section>}
      {section === "catalog" && <section id="catalog" className="catalog">
        <h2>Source registry</h2>
        <form action="/catalog" className="filters">
          <label>Find a dataset<input type="search" name="q" maxLength={100} defaultValue={catalogTerm} placeholder="Name, publisher, or series ID" /></label>
          <label>Availability<select name="validated" defaultValue={validatedOnly ? "yes" : "all"}><option value="all">All sources</option><option value="yes">Validated releases</option></select></label>
          <button className="button" type="submit">Filter catalog</button>
        </form>
        {catalogItems ? catalogItems.length ? <div className="scroll"><table><thead><tr><th scope="col">Dataset</th><th scope="col">Coverage</th><th scope="col">Status</th><th scope="col">Reuse</th></tr></thead>
          <tbody>{catalogItems.map((item) => <tr key={item.source_id}>
            <th scope="row"><a href={item.canonical_url}>{item.dataset_name}</a><small>{item.publisher}</small></th>
            <td>{item.geographic_coverage}<small>{item.temporal_coverage}</small></td>
            <td>{item.retrieval_status}{item.dataset_version && <small><code title={item.dataset_version}>{item.dataset_version.slice(0, 12)}</code></small>}</td>
            <td>{item.license_url ? <a href={item.license_url}>{item.license}</a> : item.license}{item.source_id === "onet" && <small>{item.attribution}</small>}</td></tr>)}</tbody></table></div> : <p className="state" role="status">No sources match these filters.</p> : <p role="status">The catalog is temporarily unavailable.</p>}
      </section>}
    </main>
    <footer className="bottom"><div className="shell">Socrates · AI Labor &amp; Employment Observatory</div></footer>
    </div></div>
  </>;
}
