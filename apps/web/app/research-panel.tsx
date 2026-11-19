import { FlaskConical, ArrowDownToLine } from "lucide-react";
import { runResearch, specification } from "./research";

export default async function ResearchPanel({ query }: { query: Record<string, string | string[] | undefined> }) {
  const parsed = specification.safeParse(query);
  const output = parsed.success ? await runResearch(parsed.data).catch(() => null) : null;
  const download = output && new URLSearchParams(Object.entries(output.input).filter((entry): entry is [string, string] => typeof entry[1] === "string"));
  return <div className="research-grid">
    <section className="panel">
      <h2>Study specification</h2>
      <form action="/research" className="research-form">
        <label>Method<select name="method" defaultValue={typeof query.method === "string" ? query.method : "summary"}>
          <option value="summary">Descriptive statistics</option><option value="endpoint-change">Change between endpoints</option><option value="policy-coverage">NYC policy coverage check</option>
        </select></label>
        <label>Indicator<select name="source" defaultValue={typeof query.source === "string" ? query.source : "laus"}>
          <option value="laus">New York County unemployment</option><option value="cps">U.S. unemployment</option><option value="jolts">U.S. job openings</option>
        </select></label>
        <div className="filters"><label>From<input name="start" type="month" defaultValue={typeof query.start === "string" ? query.start : ""} /></label>
          <label>To<input name="end" type="month" defaultValue={typeof query.end === "string" ? query.end : ""} /></label></div>
        <button className="button primary" type="submit"><FlaskConical size={16} /> Run analysis</button>
      </form>
    </section>
    <section className="panel" aria-labelledby="results-title">
      <div className="panel-top"><h2 id="results-title">Results</h2>{download && <a className="button" href={`/api/research?${download}`}><ArrowDownToLine size={16} /> Download run</a>}</div>
      {output ? <>
        <p className="subtitle">{output.geography} · {output.unit} · <a href={output.source}>Publisher data</a></p>
        <dl className="metric-grid">{output.metrics.map((item) => <div key={item.label}><dt>{item.label}</dt><dd>{item.value.toLocaleString("en-US", { maximumFractionDigits: 3 })}</dd></div>)}</dl>
        <h3>Diagnostics</h3><ul className="diagnostics">{output.diagnostics.map((item) => <li key={item}>{item}</li>)}</ul>
        {output.policySource && <p><a href={output.policySource}>NYC enforcement source</a></p>}
        <p className="small">Run fingerprint <code title={output.runId}>{output.runId.slice(0, 12)}</code> · Release <code title={output.input.version}>{output.input.version.slice(0, 12)}</code></p>
      </> : <p className="state" role={query.method ? "alert" : "status"}>{query.method ? (parsed.success ? "The release is unavailable. Try again shortly." : "Check the indicator and date range and run again.") : "Choose a method and indicator to run an analysis. Leave dates blank to use the full release."}</p>}
    </section>
  </div>;
}
