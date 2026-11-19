# Data dictionary

## Gold monthly observation

| Field | Type | Semantics |
| --- | --- | --- |
| `month` | string | Calendar month as YYYY-MM. Unique per series release |
| `value` | nullable double | Publisher estimate in percent (CPS/LAUS) or thousands (JOLTS) |
| `footnotes` | list of strings | Publisher notes or explicit absence marker |

The connector skips annual-average period M13, preserves monthly gaps, rejects duplicates and retains original payloads. Rates stay in percent units.

## Gold occupations

`code` is a unique O*NET-SOC code, `title` is the publisher's occupation name, and `description` is its occupation description. The version month refers to release date. It does not describe occupation observations over time.

## Release and legal events

A release records source identity, raw and normalized hashes, Gold hash, artifact name, retrieval timestamp, transformation ID, envelope coverage, row count and missing count. The transformation identifies a versioned interface; exact regeneration also uses the committed lockfile. Policy events have instrument, jurisdiction, milestone kind, event date, summary and source URL. Reporting, enactment, effective, enforcement and consolidation dates carry distinct event kinds.
