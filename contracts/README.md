# Contracts

`uptime_cases.json` arrives with M1 and holds the shared cases of the uptime formula: no
downtime, everything blocked, insufficient window, truncation of 99.996, and one to five nines.

The same file runs twice, so the SQL views and the web formatter cannot drift:

- `pytest` against the views of a local Supabase (M3).
- `vitest` against `web/src/lib/format.ts` (M1).

Adding a case means adding it here once, with the input seconds, the expected uptime, the
expected nines and the expected formatted strings.
