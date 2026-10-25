# QuickPlan tree execution + M4 smokes (2026-09-09)

Session detail for the quickplan-mode tree (4 leaves, all first-try clean,
10 commits) and the M4 e2e smoke pass. Complements
`references/quickplan-tree-prestate-2026-09-09.md` (pre-execution state)
and `references/classifier-campaign-quickplan-2026-09-09.md` (taxonomy
rules). This file covers only what those do not.

## Scratch-daemon config gotchas (meept hujson + transport)

1. **hujson requires ALL object keys quoted** — a `^`-anchored key-quoting
   regex misses inline objects (`{ enabled: true }`). The regex must match
   keys following `{` or `,` as well as line-start. Symptom: hujson errors
   "invalid literal: enabled" at the inline-object line.
2. **`transport.http.rest` is a plain BOOL** (`HTTPTransportConfig.REST`).
   Omitting it → `RESTEnabled=false` at runtime → EVERY `/api/v1/*` route
   404s ("404 page not found") while `/health` still returns 200.
   `DefaultServerConfig()` sets RESTEnabled=true, but daemon.go
   unconditionally overwrites: `httpCfg.RESTEnabled = fullCfg.Transport.HTTP.REST`.
   Set `"rest": true` explicitly in scratch configs.
3. **`require_auth: false` + no api_keys → dev-key fallback.** The server
   uses `pkg/constants.DevAPIKey()`, which resolves via `os.UserHomeDir()`
   → the REAL `~/.meept/dev_key`, NOT `$MEEPT_HOME/dev_key`. Smoke clients
   must send `Authorization: Bearer <contents of ~/.meept/dev_key>`. The
   legacy string `meept_dev_default_key_CHANGE_ME` is banned → HTTP 418.
4. **"daemon already running (PID N)"**: a prior scratch instance from a
   failed config attempt holds the RPC socket. Kill by PID (`lsof` the
   socket path), and note `kill -9` may be needed after graceful `kill`.
5. **`MODEL_PATH` env warning** in spawn_command configs is benign when
   the lifecycle block is removed (adopting an external runtime); the
   daemon logs the warning and continues.

## Centroid builder vs current adversarial corpus

`scripts/build_prefilter_centroids.py --sweep` crashed on the tracked
adversarial corpus for two reasons (fixed 2026-09-09):

1. `parse_json5` lacked `//` line-comment stripping (iters 19/20 added
   comment headers). Add `re.sub(r"(?m)^\s*//.*$", "", text)` AFTER
   string-stashing (order matters: stash strings first so `//` inside
   string values survives).
2. `load_cases` only read the legacy `categories:` layout; the adversarial
   corpus uses `cases:` with `expected_intent`/`ood`. Port the harness's
   dual-layout loading and SKIP `ood`/empty-intent cases (the prefilter
   index carries only real intents — OOD/compound-abstain are not
   indexable).

Sweep after fix: 14/202 direct at LOO, quickplan present as a class,
best tau 0.85 at 100% precision.

## Quickplan leaf-execution notes (what the checklist under-counts)

The leaf contract listed 5 intent-method switches; actual touchpoints were
10: also SemanticIndex.BuildIndex, SteeringHeuristicTable,
ShouldDispatchAsync (precedent: follow requiresPlanning), Keywords (nil
return corrupts buildIntentText's strings.Join), IsValidIntentType. A new
intent constant needs a full-inventory grep, and every deliberate
EXCLUSION needs a recorded reason (LLM-classifier whitelist tables: adding
the class there would short-circuit the cascade).

Two latent bugs surfaced as prerequisites of leaf 02 — both now fixed and
tested:

- The ambiguity gate never recorded pending-clarification state at all
  (ResumeAfterClarification was unreachable code). Fixed: record the
  clarify intent with `PendingMode` seeded from the analysis category.
- The intent analyzer's category whitelist coerced "quickplan" to
  "other", so the quickplan seed could never match. Fixed: added to the
  whitelist.

`ResumeAfterClarification` must re-set `intent.SuggestedMode` /
`result.SuggestedMode` from `pending.PendingMode` BEFORE any clear, so
post-clarification turns dispatch in quick_plan mode (the clarification
answer completes the plan; it never downgrades to plain chat). Session
execution context (active plan ID/title/state, open tracked tasks, prior
quickplan runs) renders in `session_digest.go` and is injected into the
orchestrator planner prompt for quick_plan only, with the one-way rule:
session evidence upgrades code/git → quickplan; absence never downgrades
an explicit quickplan.

## Adjudication → gold promotion specifics

- Adjudication sheet format that worked: per case — message, silver
  label, cascade answer (A/B/C with conf), `your label:` line;
  disagreements sorted first; agreements after. User labeled 48/48 in one
  pass with 3 follow-up calls (research-vs-analyze = testable criteria;
  doc-edit-with-artifact = code; bare "implement the plan" = quickplan,
  superseding an earlier bare-verb split).
- Promoted corpus is a SEPARATE untracked file
  (`replay-gold.local.json5`) with `silver: false, adjudicated: true` —
  distinct from the untracked silver corpus, so promotion is auditable.
- Gitignore additions for verbatim-text artifacts: sheet, rows, data, and
  both corpora. If one is accidentally committed (gitignore does not
  untrack): `git rm --cached <file>` + commit, and note the text remains
  reachable in history until the branch's planned end-of-campaign squash.

## Env fix (brew MLX half-install on python3.14)

Diagnosis: Cellar copy complete (41 files) vs live site-packages missing
`__init__.py`, `core.cpython-314-darwin.so`, `utils.py` (0 files), so
`import mlx` resolved a namespace package and `import mlx.core` failed.
Also present: two orphaned `numpy-2.5.x.dist-info` dirs (license-only,
no METADATA) from an interrupted pip operation — they made
`importlib.metadata.version("numpy")` return None, crashing transformers'
`require_version` ("Unable to compare versions for numpy>=1.17").

Fix: `brew reinstall mlx && brew unlink mlx && brew link --overwrite mlx`
(plain `link` refuses over existing files), then quarantine the husk
dist-info dirs. Result: mlx.core, mlx_lm, transformers 5.0, sklearn all
import on python3.14. Working interpreter for MLX work:
`/opt/homebrew/opt/python@3.12/bin/python3.12` (the 3.12 stack is the
mature one; 3.14 is the new install).

## M4 e2e smokes (scratch daemon, HTTPS :18096)

| smoke | input | observed |
|---|---|---|
| quickplan | "using subagents, review the config loader code for bugs and correct them as you find them" | full plan-execute loop; coder read real files; hit 50k conversation budget (config: raise `max_conversation_tokens` in coder AGENT.md frontmatter) |
| ambiguity | "fix it" | clarify path proven ("describe what needs to be fixed"); run variance is chain nondeterminism |
| fallback | gibberish ≥ short-guard | chat-style response — correct for content-free input |

Verdict: mechanism works live; accuracy-vs-replay gap is
corpus/distribution, not routing. Scratch config + smokes in
/tmp/qp-smoke/ (throwaway).

## User Q&A decisions that closed the campaign (2026-09-09)

1. **Double-confidence gate (user's idea) adopted**: gate stage B with
   the BACKSTOP's confidence when B's precision < backstop precision —
   the collapse to zero rescue routes is correct, and measured better
   (84.56% vs 83.97%). General form: a stage that replaces backstop
   calls fires only when its precision demonstrably exceeds the
   backstop's.
2. **Execute-existing-plan = quickplan, ALL phrasings** (bare "implement
   the plan" included — supersedes the earlier bare-verb split). `plan`
   = designing before building, only.
3. **Capability-aware allotment scoped** (user's Q3): when executor runs
   die on budget, check whether the SCHEDULER chunks work to the
   executor's context size — meept's tactical scheduler caps steps by
   count (8/phase), not token-footprint vs model context_length. The
   classifier campaign was appropriately sized; the chunker is the
   follow-up tree (internal/agent/tactical.go).
4. **"Help me…" phrasing** = quickplan signal (compound work);
   informational help = analyze. Added to intent-routing.md.
