# Data acquisition report

| Source | Pilot scope | Verified result | Publisher |
| --- | --- | --- | --- |
| CPS | LNS14000000, U.S. unemployment rate | 36 months, 0 missing | [BLS CPS](https://www.bls.gov/cps/) |
| LAUS | LAUCN360610000000003, New York County resident unemployment rate | 36 months, 0 missing | [BLS LAUS](https://www.bls.gov/lau/) |
| JOLTS | JTS000000000000000JOL, U.S. job openings | 36 months, 0 missing | [BLS series](https://data.bls.gov/timeseries/JTS000000000000000JOL) |
| O*NET | Release 31.0 occupation definitions | 1,016 unique codes, 0 incomplete rows | [O*NET Database](https://www.onetcenter.org/database.html) |

BLS windows cover January 2022 through December 2024, retrieved November 19, 2026 UTC. BLS-produced aggregate material is generally public domain with source attribution. O*NET 31.0 occupation definitions use CC BY 4.0 under the publisher's database terms. Attribution is stored in the registry and API. AILEO renamed columns and converted CSV to Parquet. [BLS copyright](https://www.bls.gov/bls/linksite.htm) · [O*NET license](https://www.onetcenter.org/license_db.html)

The [registry](data/registry/sources.json) stores discovery metadata. The serving catalog merges manifest-backed statuses and timestamps. [BLS acquisition log](data/manifests/pilot-ingestion.jsonl) · [O*NET acquisition log](data/manifests/onet-ingestion.jsonl)

## Source follow-up

1. Extend BLS coverage through verified recent vintages and acquire matched-adjustment citywide and comparison series. Preserve BLS revisions by release.
2. Census BTOS has downloadable AI supplement aggregates. Acquire the release-specific downloads, document questionnaire breaks and validate estimates and suppression before publication. QWI and other Census labor products remain discovery records. [Census release notice](https://cdn.www.census.gov/newsroom/press-releases/2026/btos-june-18.html)
3. Expand O*NET to tasks, skills and historical occupational classifications. Confirm each table's specific license and exceptions before export.
4. The ACLU tracker and FAccT replication README cite CC BY-NC 4.0 for the tracker. Confirm which files are covered, approval for the intended public reuse, citation and third-party report rights. The tracker file inventory was inspected. No ACLU records were published or integrated. [Tracker](https://github.com/aclu-national/tracking-ll144-bias-audits) · [FAccT replication materials](https://github.com/aclu-national/auditing-the-audits-facct-2025)
5. NYC and EU policy timelines use curated official references. The NYC FAQ returned HTTP 403 from the CLI and was reviewed via publisher-indexed documentation. No automated retrieval bypass was used. NYC OSC findings are oversight evidence, distinct from adjudicated violations. The EU entry links the July 2026 consolidated text. Provision-level schedules remain to be modeled. [NYC DCWP](https://www.nyc.gov/site/dca/about/automated-employment-decision-tools.page) · [NY OSC](https://www.osc.ny.gov/state-agencies/audits/2025/12/02/enforcement-local-law-144-automated-employment-decision-tools) · [EUR-Lex](https://eur-lex.europa.eu/eli/reg/2024/1689/2026-07-27/eng)
6. Confirm OECD export interfaces and terms, Stanford AI Index upstream licenses, and the selected academic exposure archive's replication rights. Preserve distinctions between exposure, adoption, and displacement.

## Global comparison releases

Socrates serves annual ILO modeled estimates published by the World Bank for unemployment, labor-force participation, and the employment-to-population ratio. The pilot pins 2015–2025 values for the United States, Canada, Mexico, Germany, the United Kingdom, Japan and the World aggregate. Its 231 country-or-aggregate/year/indicator slots preserve any publisher nulls. The raw replay files and retrieval metadata are committed. Refresh through `uv run --locked --group ingest python -m pipelines.worldbank` and update the checked-in ingestion log after validation. [World Bank unemployment](https://data.worldbank.org/indicator/SL.UEM.TOTL.ZS) · [Participation](https://data.worldbank.org/indicator/SL.TLF.CACT.ZS) · [Employment ratio](https://data.worldbank.org/indicator/SL.EMP.TOTL.SP.ZS)
