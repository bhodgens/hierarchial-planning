# Oopenbot parity campaign shape
When to use: issues to frozen-contract wave plans.
Lesson: campaign shape template: contracts in master.md beat prose.

# Campaign shape: issues → frozen-contract wave plan (humanplusone openbot-parity, 2026-09)

Worked variant of plan-tree organization for a batch of related GitHub issues
turned into one campaign. Lighter than branch/orchestrator trees; proven for
10 issues / ~16 leaves / 9 dependency-ordered waves.

## File shape

```
plans/<campaign>/
  master.md      # goal, wave-order table (with WHY column), FROZEN CONTRACTS, dispatch rules
  wave1.md       # per wave: leaf N.M sections — files owned, requirements checklist, acceptance, verification cmd
  wave2.md
  ...
```

No per-branch orchestrator.md — the wave file IS the dispatch context. Each
leaf section must be self-contained enough that its text (plus master.md's
contracts) can be pasted into a leaf dispatch verbatim.

## Frozen contracts — the key addition

At PLANNING time, write exact interface contracts into master.md as a
numbered section (Contract A, B, ...): full SQL schemas, JSON payload shapes,
naming conventions, replacement-format strings, module boundaries. Rules that
made this work:

1. **Contract owns cross-wave shared data.** Anything two waves both touch
   (an audit_log table, a redaction scrubber's output format, a policy JSON
   schema) gets one contract with the exact DDL/shape. Later waves reference
   "per Contract A" instead of restating — and cannot silently diverge.
2. **Freeze signatures, placeholder bodies.** When wave N needs a function
   wave N+1 will fully implement (redaction scrubber needed by audit writer
   before the scrubber wave), wave N's leaf creates the module with the
   FROZEN signature + pass-through body + `# wave-N+1 replaces` marker.
   Signature lands once; body swaps later; no rework.
3. **Duplicated-by-design beats cross-package import.** Worker twin of a
   control-plane module (redaction, policy evaluator): vendor a mirror with
   a header `# vendored mirror of control.<mod> vX — keep in sync`, and
   duplicate the test fixtures too. Worker must not import control code.
4. **One source of truth per behavior.** The scrubber contract says WHO
   calls it (Langfuse pre-export AND audit writer) so both waves wire the
   same module instead of each inventing redaction.

## Shared-file region ownership written at PLAN time

Where two leaves in different waves touch the same file (database.py,
main.py), each wave doc's leaf section states: "own ONLY the <regions>".
Planning-time ownership beats dispatch-time haggling — the wave author sees
all waves' claims at once. Patterns used:

- "own ONLY that field block" (config.py additions)
- "own ONLY the 2 router-include lines" (main.py)
- "own ONLY the new route fn" (routes/*.py)
- "own ONLY the gate block + policy fetch" (worker main.py dispatch)
- "additive `write_audit` calls, no logic changes" (instrumentation leaves)

## Dispatch rules that went in master.md

- Every leaf TDD-first, ends with lint+format+suite green
- Orchestrator commits per leaf (leaves are no-commit); `Refs #N`/`Closes #N`
- No branch-per-leaf; sequential orchestrator commits to main
- Commit plans BEFORE dispatching wave 1 (baseline; drift attributable)

## Wave-order discipline

The master wave table carries a WHY column ("audit trail prereq for policy;
scrubber shared with audit writer"). When the user reorders or repriorizes
mid-campaign, the WHY column is what tells you which reorders are safe.

Leaf doc's verification bar is a FLOOR, not the ceiling, when the tools
themselves install locally (verified leaf 2.2, 2026-09-09): zizmor and
cyclonedx-py pip-install into the root venv even though the CI stack can't
run, so the leaf can and should smoke-test the actual invocations it adds.
Two reasons this matters: (1) plan-doc commands can encode OUTDATED CLI
syntax — wave2.md said `cyclonedx-py requirements -i requirements.lock`,
which on cyclonedx-py 7.x treats the path as a package index and exits 0
with an EMPTY SBOM; (2) silent-success failures are exactly the ones that
ship, so validate OUTPUT CONTENT (SBOM component counts, zizmor finding
counts), never exit codes alone. Where a required edit lands in a sibling
leaf's file (upload-artifact step in the wave-1 CI file), verify the fact
anyway (action SHA via `gh api` tags + commit cross-check) and record it as
a header comment in a file you own, marked as handoff — don't touch the
sibling's file, don't drop the verified fact. Tool specifics:
repo-quality-gates-setup skill → references/supply-chain-gates.md.

## Verification bar without live infra

GH Actions / SPIRE / n8n leaves can't run their stack in the leaf env. The
leaf's acceptance is: YAML parses, every `uses:` SHA-pinned (regex check
`@[0-9a-f]{40}`), referenced make targets exist, referenced paths exist.
Live verification lands at the wave gate (orchestrator push), and the leaf
doc says so explicitly — never let a leaf claim "CI works" when it can only
claim "CI file is valid".

## Orchestrator-side review gates for no-commit leaf batches (waves 1–2)

- **Re-verify every from-memory pin.** Leaf 1.1 pinned `hashicorp/setup-tofu`
  from model knowledge — `gh api repos/hashicorp/setup-tofu/commits/<sha>`
  returned 404. Fix that worked: swap to the vendor install script with a
  pinned version + honest comment ("no verified SHA at authoring time").
  Leaf 2.2 did it right: resolved tag→commit via `gh api .../tags` + commit
  cross-check and cited the tag. Rule: an action pin without a gh-api
  verification trail is a finding, not a fact.
- **Scope `git diff` per leaf's declared file list** before committing —
  ownership violations show up as hunks outside the leaf's claimed files.
  Waves 1–2: zero violations; the plan-time region ownership held.
- **Null-test trap in leaf reports:** "hook installed and green" from a leaf
  that staged an already-committed file is a vacuous pass (empty
  `git diff --cached` → every stage skipped). Demand: modify a real file →
  stage → run → revert. Same skepticism applies to any leaf verification
  whose command could no-op.
- **Commit per leaf, not per batch** (`git add <leaf files>` explicit
  pathspecs) so `Closes #N` attribution stays per-issue and a later
  batch-review revert can't take unrelated leaves with it.

## Leaf-side lessons from wave 3 leaf 3.1 (audit writer, 2026-09-09)

Direct implementer-role execution of the first Contract-A consumer; the
frozen-contract machinery held (Contract A DDL landed byte-exact, verified
by PRAGMA-tuple schema tests), plus four new reusable bits:

1. **Exact-set assertions in sibling test files are coupled to your leaf.**
   `start_scheduler` job registration was pinned by an EXACT set-equality
   test in an existing test file — registering `purge_audit_log` broke it.
   Before final green, grep the test tree for the registry surface
   (`grep -n "get_jobs" tests/`) and update every exact-set assertion in
   the same change. This is expected drift, not a sibling-ownership
   violation: the +1 line is your leaf's to land.
2. **Byte-cap truncation must guarantee valid UTF-8, never parseable
   JSON.** The 4KB `args_redacted` cap cuts mid-string, so `json.loads` of
   stored args is undefined BY DESIGN. Test strict decode + marker, not
   parseability. The truncate-by-bytes loop needs BOTH continuation-byte
   stripping AND orphaned-lead-byte dropping (a cut between 0xC3 and 0xA9
   otherwise emits invalid UTF-8). Full recipe:
   python-test-suite-authoring skill →
   references/humanplusone-audit-writer-coverage.md.
3. **Pragmatic-contract note:** the leaf doc said "reuse the existing
   `DEFAULT_PURGE_CRON` const" for the audit purge; reusing a const NAMED
   for archived-client purge couples two unrelated jobs' schedules
   silently. Landed as a new named placement (same `'0 3 * * *'` literal,
   inline at the registration with its own `_make_cron_trigger` call).
   When "reuse" is satisfied by equal value rather than shared symbol,
   prefer the new name and record the deviation.
4. **Patch-assembly placeholder ghosts:** a broken placeholder (`:=` stub,
   undefined default-expr) left mid-file by a sloppy incremental edit is
   caught by the write-time lint/LSP gate — but only if you don't keep
   batching edits on top of it. Verify the file parses after each
   structurally novel edit before building on it.

Also: **format-gate attribution by tool version** (new drift class this
session). A newer ruff (0.16.x, 2025+ formatting style:
magic-trailing-comma expansion) flags pre-2025-formatted files the tree
never touched — `ruff format --check` over all of `src/` reported 4
"would be reformatted" files that are pre-existing drift, not leaf
regressions. Scope the FORMAT gate to the leaf's own file list; keep
`ruff check` (lint) repo-wide since it's version-stable here. Never
reformat sibling/legacy hunks to make the global format check green.

## Leaf-side lessons from wave 5 leaf 5.1 (policy model + evaluator, 2026-09-09)

1. **Two more spec-deviation classes, same recording discipline as the
   DEFAULT_PURGE_CRON note.** (a) Physically-fragile acceptance criterion:
   the leaf's "100ms guard" on regex matching — a true runtime watchdog is
   fragile under async workers and protects nothing for admin-authored,
   parse-compiled, length-capped patterns over short subject strings.
   Implemented the protective INTENT compile-time (256-char cap, malformed-
   regex rejection at validate, lru_cache compile, tokenizer token cap),
   disclosed the deviation in the module docstring, pinned it with
   at-cap/over-cap boundary tests. (b) Unspecified edge: `tools: []` —
   chose safe semantics (valid document, rule never matches) + test pin.
   Fill gaps with the safe reading, pin, report.
2. **Acceptance text names a mechanism, not a ceiling.** Leaf said
   "assert via `'eval(' not in inspect.getsource(...)`" — shipped the
   leaf's named test AND stronger forms (AST Name-call walk incl. compile;
   import ALLOWLIST). Caveat recorded for reviewers: the substring form
   false-positives on identifiers ending in `eval(` (`retrieval(`) — the
   AST form is the precise one.
3. **Contract C mirror heads-up for the worker wave:** control-side
   `control/policy.py` is now the source of truth for the vendored worker
   mirror (campaign rule 3) — grammar, None semantics (`!=` True on
   missing paths), bool/int strictness, and the fail-closed matrix
   (deny-rule error → deny even with default=allow; allow-rule error →
   skip + noted in reason) all duplicate from it, along with the fixture
   style in tests/test_policy.py. Use the `# vendored mirror` header
   discipline when that leaf dispatches. Full worked example:
   python-test-suite-authoring skill →
   references/humanplusone-policy-evaluator-leaf.md.

## Leaf-side lessons from wave 5b leaf 5.3 (worker PolicyGate + policy/audit routes, 2026-09-09)

The Contract-C consumer wave — worker mirror + gate + the two worker-key
routes. Frozen contracts held (mirror byte-drift guard, plan-time region
ownership, per-client-key tenant binding); five new reusable lessons:

1. **Contract fallback literals must pass the campaign's OWN validator.**
   The deny-default doc `{"rules": [], "default": "deny"}` lacks
   `version`, which the wave-5.1 validator REQUIRES — strict validation
   rejected the server's exact deny-default response. Fix: recognize the
   exact literal (and null policy) at the worker's fetch boundary →
   normalize to the validated default-deny form; real documents still
   validate strictly. Planner rule: any contract naming a fallback
   literal must run that literal through the sibling validator contract
   at PLANNING time.
2. **Fail-closed fallbacks MASK wire-shape mismatches.** First cut parsed
   a `{"policy": ...}` envelope while the route (per contract prose:
   "returns that client's policy JSON") returns the BARE document — the
   mismatch normalized silently to deny-all: no error, no log, and the
   first test run still passed 8/23. Detect via (a) parse the shape the
   contract TEXT names, tolerating alternatives with an explicit
   commented branch, and (b) happy-path tests assert policy CONTENT
   (rule ids served, rule ids surfacing in decisions) — deny-outcome-only
   tests pass vacuously against a gate that denies everything forever.
3. **Per-task refresh gates need BOTH entries: sync-scheduling refresh()
   and awaitable arefresh_wait().** From sync code under a running loop,
   refresh() can only schedule the fetch — an async test calling
   refresh() then checking immediately races the task and silently sees
   the stale gate (wrong verdicts, not errors). Wiring tests await the
   waitable variant (exactly what the worker's task path does); the sync
   entry exists for boot/no-loop paths.
4. **pytest-asyncio mode is PER-PACKAGE.** Worker pyproject sets NO
   asyncio_mode → STRICT → every async test needs an explicit
   `@pytest.mark.asyncio` (failure signature: "async def functions are
   not natively supported"); the control-plane package's
   asyncio_mode=auto does NOT transfer across packages. Check each
   package's pytest config before reusing async-test patterns.
5. **Vendored-twin drift guard: assert `mirror == header + control_source`
   with the sibling tree path-resolved.** Bare source-equality fails on
   the mandated `# vendored mirror` banner (a 2-line delta reported as a
   670-line diff dump); resolve `../control-plane/src` relative to the
   test file and sys.path-insert it ONLY inside the drift-guard test
   (import-path pollution breaks sibling tests); keep the ImportError
   skip ONLY for true worker-isolated checkouts. Env note: the shared
   venv was missing declared worker deps (`nats-py`) — install declared
   deps into the venv before blaming import errors.

Plan-time region ownership lines that worked verbatim: "own ONLY the new
route fn(s)"; "own ONLY the gate block + policy fetch". Control-plane
serving note: run the validating getter (`get_policy`) as a corruption
guard, then SELECT the raw `policy_json` for the response — the parsed
Policy object (ASTs attached) is not the wire document. Audit-ingest
tenant binding is deliberately ASYMMETRIC with task-result: unknown
client_ids ACCEPTED (audit_log has no client FK; dropping a stale
worker's deny trail is worse than filing it under a removed id), while
task-result 404s unknown clients because its rows drive usage/value.

## Leaf-side lessons from wave 6 leaf 6.1 (control state + handoff endpoints, 2026-09-09)

Contract D landed clean (34 tests, suite 521, coverage 94.88%); three new
reusable campaign lessons:

1. **Auth-union GET dependency for "admin OR worker key" reads with
   admin-only mutations.** Contract D's split (take/release = admin key
   ONLY; GET = admin OR worker key) needed a new shape not present in any
   earlier wave: a `verify_admin_or_worker_key` dependency that calls the
   existing `verify_worker_key`/`verify_api_key` verifiers AS PLAIN
   FUNCTIONS (worker path first, each HTTPException collected, neither
   header → fail-closed 401). Per-client worker keys return the bound
   client_id → GET 403s cross-tenant reads (F-003), symmetric with 5.3's
   task-result binding. Anti-pattern: re-checking auth inline in the
   route body. Full pattern: python-test-suite-authoring skill →
   references/humanplusone-control-state-leaf.md.
2. **Clamp-vs-reject bounds follow the contract verb.** Contract D said
   `minutes<=0` rejected, `minutes>120` clamped. So pydantic enforces
   ONLY the reject class (`Field(None, gt=0)` — adding `le=120` would
   422 instead of clamp); the clamp is handler-side and the response
   ECHOES the effective clamped value so tests verify without clock
   math. When a contract mixes bound semantics, classify per-bound
   before writing Field constraints.
3. **No-op semantics pin three behaviors, not one.** Contract D's
   "release while already bot → no-op" resolved to: returns the current
   row (not None), writes nothing (COUNT stable), and (at the HTTP
   layer) writes NO audit row. Release-when-ABSENT returns None and
   creates nothing. Pin each branch separately — a single "no-op"
   test misses two of the four.

Also reconfirmed from 3.1: registering a new scheduler job required the
one-line exact-set job-id pin update (drift expected, leaf-owned), and
the AsyncIOScheduler registration test must be `async def` (two-loop
shutdown failure — see python-test-suite-authoring SKILL.md pitfalls).
Baseline-attribution note: proving "0 NEW mypy errors" needs
`git stash -u` (plain stash leaves untracked new files in the
"baseline") — see git-verification-patterns stash addendum.
