import { ArrowDownToLine } from "lucide-react";
import releases from "./global-releases.json";

export default function GlobalPanel({ selection, indicator }: { selection: string | string[] | undefined; indicator: string | string[] | undefined }) {
  const release = releases.find((item) => item.indicator === indicator) ?? releases[0];
  const usa = release.series[0];
  const peer = release.series.find((series) => series.code === selection && series.code !== usa.code) ?? release.series[1];
  return <section className="panel">
    <div className="panel-top"><h2>Annual labor indicators</h2>
      <a className="button" href={`/api/global?indicator=${release.indicator}`}><ArrowDownToLine size={16} /> Download release</a>
    </div>
    <p className="subtitle">Modeled ILO estimates · {release.unit} · Annual</p>
    <form action="/global" className="filters">
      <label>Indicator<select name="indicator" defaultValue={release.indicator}>{releases.map((item) => <option key={item.indicator} value={item.indicator}>{item.label}</option>)}</select></label>
      <label>Compare the U.S. with<select name="peer" defaultValue={peer.code}>
        {release.series.slice(1).map((series) => <option key={series.code} value={series.code}>{series.name}</option>)}
      </select></label><button className="button" type="submit">Compare</button>
    </form>
    <div className="scroll">
      <table><caption>{release.label}</caption><thead><tr><th scope="col">Year</th><th scope="col">{usa.name}</th><th scope="col">{peer.name}</th></tr></thead>
        <tbody>{[...usa.values].reverse().map((row) => <tr key={row.year}>
          <th scope="row">{row.year}</th><td>{row.value === null ? "Unavailable" : `${row.value}%`}</td>
          <td>{peer.values.find((item) => item.year === row.year)?.value != null
            ? `${peer.values.find((item) => item.year === row.year)?.value}%` : "Unavailable"}</td>
        </tr>)}</tbody></table>
    </div>
    <div className="series-footer"><p className="small">Annual modeled estimates use a different methodology and frequency from the monthly U.S. labor series. The comparison uses the same World Bank indicator for both columns.</p>
      <p className="small"><a href={release.source}>World Bank · ILOSTAT</a> · {release.license} · Release <code title={release.version}>{release.version.slice(0, 12)}</code></p>
    </div>
  </section>;
}
