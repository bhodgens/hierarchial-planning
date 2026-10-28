# Oopenbot parity continuation leaves 2026 09 09
When to use: direct single-leaf continuation sessions.
Lesson: leaves 6.2 and 7.1 execution detail.

# OpenBot parity continuation: leaves 6.2 and 7.1 — direct single-leaf sessions (2026-09-09)

Both leaves were executed DIRECT in follow-up sessions — no orchestrator
dispatch — proving the campaign's dispatch-context skeleton doubles as a
solo-implementer checklist. Results: 6.2 (control gate, wave 6b) worker
82→98 / cp 521→526; 7.1 (worker-native MCP client, wave 7, Contract E)
worker 98→140 / cp 526→533 (94.92%). Both reused the same sequence:
read leaf + master contract → sibling test file for conventions →
baseline full suites BEFORE edits → RED/GREEN → ruff → pure-addition diff
proof → no commit.

## 7.1 specifics (full worked case: python-test-suite-authoring skill →
`references/humanplusone-mcp-client-leaf.md`)

1. **Probe installed SDKs before writing code.** `mcp>=1.0` resolved to mcp
   2.2.0 — every 1.x API name from model memory was wrong
   (`streamablehttp_client`→`streamable_http_client`, `FastMCP`→`MCPServer`,
   camelCase→snake_case model fields, vendored `httpx2` instead of stdlib
   httpx for the client transport). Workflow that worked: inspect
   `inspect.signature()`/`model_fields` on the installed package, get an
   in-process client↔server round-trip working as a throwaway probe BEFORE
   implementation, then land an import-fallback shim so the declared
   `>=1.0` constraint stays honest.
2. **anyio LIFO teardown** (production bug caught by the new tests): code
   caching anyio-transport connections in a dict must close them in REVERSE
   open order — FIFO close crashes with "cancel scope isn't the current
   task's current cancel scope" — and a connection must never outlive the
   task that opened it. Documented as behavior in `MCPRegistry.aclose()`.
3. **Frozen acceptance forced additive evaluator extensions** (control-plane
   `policy.py`, re-vendored byte-identically after each of 3 edits; the
   drift-guard test stayed green): `tool.effect` parser path,
   `build_context(tool_effect=)`, and trailing-`*` PREFIX match in
   `_tool_matches` — the frozen acceptance
   `tools: ["mcp__anythingllm__*"], when: 'tool.effect == "read"'` was
   unsatisfiable under exact-match-only (bare `*` semantics unchanged).
   **Planning-time rule this buys:** run the acceptance-criterion policy
   expressions through the current evaluator when authoring the wave doc;
   an unsatisfiable-but-frozen acceptance surfaces as forced mid-wave
   language changes in a later leaf.
4. **Consent-gate data point**: `rm -f /tmp/*probe*` — cleanup of the
   implementing session's OWN throwaway probe files — was denied. The
   leave-scratch-artifacts-and-mention-them-once rule extends beyond
   dispatched leaves' artifacts to the direct session's own probes.
5. **Settings-field leaves must rerun `scripts/gen-config-docs.py`**: adding
   `mcp_servers` to WorkerSettings fails the control-plane docs-freshness
   gate until `docs/configuration.md` is regenerated — do it in-leaf, not at
   review. Dependency additions: `pyproject.toml` yes, `requirements.lock`
   no — the supply-chain wave owns lock regeneration (pip-compile, hash-
   pinned); flag the stale lock in the leaf report instead of editing it.
6. **Spy-double compatibility for new params**: pass new positional args
   POSITIONALLY at existing call sites (`_execute_tool(fn, args, mcp_registry)`)
   so sibling test doubles with `def _spy(name, args, mcp_registry=None)`
   keep binding; the keyword form (`mcp_registry=`) broke 4 existing spies.
