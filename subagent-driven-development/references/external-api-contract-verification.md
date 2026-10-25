# External API Contract Verification — Live Dry-Run Pattern

When implementing fetchers/clients against external APIs (job boards,
SaaS products, public data feeds), the test fixtures written from plan
assumptions or stale blog posts are the single largest source of
production bugs. Mock-server tests confirm the code parses the fixture
correctly — not that the fixture matches reality.

## The 3-stage verification pipeline

### Stage 1: Pre-dispatch — verify the API contract before writing code

Before dispatching an implementation subagent for an external API
client, verify the contract yourself (the orchestrator) via:

1. `web_search` for the provider's official API docs page
2. `web_extract` the docs page to get the real request/response shape
3. Embed the VERIFIED shape in the subagent's context, not the plan's
   description

Do NOT trust the plan's API description if no one has verified it this
session. Plans are often written from memory or community examples that
may be months or years stale.

### Stage 2: Post-implementation — live dry-run smoke test

After unit tests pass and the code is committed, run the actual tool
against real endpoints in a no-side-effects mode:

```sh
go run ./cmd/your-tool -dry-run -board-timeout 15s
```

Scan output for:
- **Decode errors** (HTML returned where JSON expected → endpoint moved)
- **Type mismatch errors** (field shape changed → struct needs updating)
- **HTTP 4xx/5xx** (auth or endpoint wrong)
- **Zero results when results were expected** (silent failure)

### Stage 3: Review phase — check for contract verification

When dispatching review subagents for code that integrates with external
APIs, add these checks to the review prompt:

1. Were the API contract details (endpoint URL, auth headers, response
   field names/types) verified against live docs or a live curl?
2. Does the test fixture use a response shape copied from real API
   output, or one written from the plan's description?
3. For auth-bearing sources: is there a live curl verification step in
   the plan? If not, flag it as an open risk.

## Concrete bugs caught by this pattern (jobforge ATS fetchers)

### USAJobs auth scheme (Critical — would 401 on every request)

**Assumed (plan):** `Authorization: Basic email:apikey` (literal, not
base64), host `developer.usajobs.gov`.

**Actual (official docs):** `Authorization-Key: <apikey>` (custom
header), `User-Agent: <email>`, host `data.usajobs.gov`. The
`developer.usajobs.gov` host serves the docs site, not the API.

**How caught:** Review subagent flagged the non-standard auth as
suspicious. Orchestrator verified via `web_extract` of the official
authentication docs page, which explicitly documents the three required
headers.

### SmartRecruiters endpoint + URL field (Critical — wrong URLs stored)

**Assumed (plan):** Endpoint `careers.smartrecruiters.com/{board}/api/v1/jobs`
(undocumented CORS mirror), URL field `ref`.

**Actual (official OpenAPI spec):** Endpoint
`api.smartrecruiters.com/v1/companies/{slug}/postings`. The `ref` field
is an API detail URL, not the user-facing apply URL (`applyUrl`).

**How caught:** Review subagent flagged that `ref` values in the test
fixture looked hand-crafted (a careers-page URL) rather than API-issued
(an API endpoint URL). Orchestrator verified via `web_search` of the
SmartRecruiters developer docs, which showed the correct endpoint and
the `applyUrl`/`postingUrl`/`ref` field distinction.

### Arbeitnow endpoint migration (Caught by live dry-run)

**Assumed (plan):** Endpoint `/api/job-board.json`.

**Actual (live API):** Old endpoint 302-redirects to homepage (returns
HTML). New endpoint is `/api/job-board-api`. Response shape identical
except `location` field changed from array to string.

**How caught:** Live `go run ./cmd/ingest-ats -dry-run` produced a
decode error: `invalid character '<' looking for beginning of value`
(HTML returned where JSON expected). A 30-second curl confirmed the
redirect. The fix was a 1-line endpoint URL change + struct field type
change.

**Key lesson:** This bug was NOT caught by the mock-server test (which
always returns valid JSON at the expected path) NOR by the doc-based
review (the docs hadn't been updated). Only the live dry-run caught it.

## Decision matrix: when to use each stage

| Situation                                   | Stage 1 | Stage 2 | Stage 3 |
|---------------------------------------------|---------|---------|---------|
| API client for well-known stable API        | skip    | skip    | review  |
| API client for niche/unfamiliar API         | **yes** | **yes** | **yes** |
| API client where auth scheme is unusual     | **yes** | **yes** | **yes** |
| Plan written from memory/community examples | **yes** | **yes** | review  |
| Quick prototype / spike                      | skip    | optional| skip    |

The cost of all 3 stages for a 3-fetcher implementation: ~5 minutes of
orchestrator time (web_extract + dry-run) + 1 review subagent dispatch.
The cost of skipping them: 2 critical production bugs that pass all
unit tests and only surface when a real user tries to use the feature.
