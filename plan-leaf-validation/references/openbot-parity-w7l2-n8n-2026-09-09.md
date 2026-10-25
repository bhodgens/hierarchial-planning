# Openbot-parity wave 7 leaf 7.2 — n8n worker tools + tenant isolation + completion ingest (2026-09-09, humanplusone)

TDD implementing-leaf session. Dispatch: "Leaf 7.2: n8n worker tools + tenant
isolation + completion ingest per plans/openbot-parity/wave7.md, TDD. No commit."

## Landed (uncommitted per dispatch)
- NEW `worker/src/hpo_worker/n8n.py` — `N8NClient` (never-raise error results,
  per-call httpx client, 30s timeout), `n8n_list_workflows()` / `n8n_execute_workflow()`
  LLM tool entry points, `has_agent_tag` / `_tag_names` isolation helpers
  (normalizes both string tags and `[{id,name}]` tag objects).
- NEW `worker/tests/test_n8n.py` — 19 tests (respx): list auth+filter+cursor
  pagination, execute roundtrip pinning the endpoint body, tag-mismatch/untagged/404
  refusals, timeout/connect/http error posture, config plumbing, policy-gate CEL
  `args.workflow_id`, main.py registration+dispatch routing via `_process_task_inner`.
- `worker/src/hpo_worker/config.py` — only `n8n_base_url` / `n8n_api_key` fields.
- `worker/src/hpo_worker/main.py` — only: import, 2 tool defs (registered only when
  `n8n_base_url` set), 2 dispatch branches (before the `mcp__` arm).
- NEW `control-plane/tests/test_n8n_result.py` — 7 tests.
- `control-plane/src/control/routes/agent.py` — only `POST /api/agent/n8n-result`
  (`N8nResultPayload`, audit row actor=system action=`n8n.workflow_completed`,
  outcome ok/failed, worker-key authed, per-client-key tenant binding, 401 writes
  nothing; mirrors /help-request structure).
- `docs/configuration.md` — regenerated (required; see cross-suite gate below).

Suites: worker 140 → **159 passed**; control 533 → **540 passed** (coverage 94.94%);
ruff check + format clean. HEAD unchanged `5c60d71`.

## Pinned endpoints (n8n public API, `X-N8N-API-KEY` header)
- list: `GET /api/v1/workflows` (cursor pagination via `nextCursor`)
- isolation pre-fetch: `GET /api/v1/workflows/{id}`
- run: `POST /api/v1/workflows/{id}/execute` — payload passthrough in
  `{"runData": {...}}`; requires `workflow:execute` scope. (The wave7.md text
  mentioned `/run` OR "execute endpoint per n8n public API — pin the endpoint
  used"; pinned to `/execute` per n8n PRs #20234/#23435.)

## Tenant isolation design (the leaf's core)
Tag contract: a workflow belongs to a client iff its `tags` contain
`agent-<client_id>`.
- List filters strictly by tag (cross-client + untagged invisible).
- Execute does a DEFENSE-IN-DEPTH re-fetch and refuses with
  `{"error": "workflow not assigned to this client"}` BEFORE any execution POST —
  tests assert `post_route.called is False` (proves the cross-tenant run never fired).
- Policy: write tool gated by `tool.name`; CEL `args.workflow_id == "wf-1"` allow
  rules work via the existing build_context (no new machinery needed).

## Test-side fixes (patterns now in protocol items 23-26)
- Dev machine env carried a real `N8N_API_KEY` → pydantic-settings defaults test
  failed through no code fault. Fix: `monkeypatch.delenv("N8N_API_KEY",
  raising=False)` AND `WorkerSettings(_env_file=None)`.
- `control.write_audit` serializes args compactly (`{"a":"b"}`) — test assertions
  with `": "` spacing failed on green code; read the writer's `json.dumps` kwargs
  before writing membership assertions.
- Policy rules in this repo REQUIRE a `when` field (`rules[0]: missing required
  field: when`); `"when": "true"` for unconditional allows.
- Freshness gate is cross-suite: adding worker config fields failed
  `control-plane/tests/test_docs_freshness.py`. Ran `make docs` generator, verified
  via `git diff` that only the 2 new rows appeared.

## Reusable structure notes for this repo's future leaves
- Worker tests mirror `test_mcp.py`'s `_make_worker` + `_StubRegistry` +
  fake-`llm_complete` two-iteration loop pattern (tool call iter 1, final answer
  iter 2) — drive `_process_task_inner` directly with `payload` key.
- Control-plane route tests mirror `test_help_request.py`: in-memory sqlite,
  direct async route-function invocation with `authed_client_id=None` (shared key)
  / bound id (per-client key), `clients` + `audit_log` schema fixture.
- Policy-gate preload pattern: `monkeypatch.setattr(PolicyGate, "_fetch_policy",
  _fake_fetch)` then `await gate._fetch_policy_safe()` — no HTTP.
