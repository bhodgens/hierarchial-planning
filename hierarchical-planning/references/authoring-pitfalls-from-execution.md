# Plan Authoring Pitfalls Observed in Execution (2026-08-25)

Written by the executing orchestrator after running three trees
(unified-theming, oauth-providers review, loop-economics dispatch) against
meept. For plan AUTHORS: these are mistakes found in trees at execution time
that cost dispatch cycles or forced in-session redesign.

## 1. Verify embedding/asset mechanics before freezing the contract

The unified-theming master.md originally specified "Go embeds tokens.json5,
Flutter reads the same file as an asset." Neither works: go:embed cannot
cross the module root upward, and Flutter assets cannot escape the package
dir. The executed design (Go embed via a root-level `theme` package; Flutter
gets a const-copy Dart file guarded by a byte-for-byte parity test) had to be
invented mid-execution. When a plan's contract depends on file placement or
tooling mechanics, run a 2-minute spike first.

## 2. hujson does not accept unquoted keys

JSON5-style unquoted object keys fail `hujson.Standardize` ("invalid literal").
If the tree specifies JSON5 config/token files parsed by hujson, write the
example with quoted keys.

## 3. Specify sub-package import direction explicitly

Trees that span a Go parent package and its sub-packages must state which
direction imports flow. meept: `internal/tui` imports `internal/tui/models`,
so models cannot reach the parent's palette — each sub-package needed its own
bridge over the shared low-level package. Plans should name the bridge owner
per sub-package; otherwise every leaf invents its own (or worse, creates an
import cycle).

## 4. Count things at authoring time, not from memory

Issue #24 said "1,031 Flutter refs"; execution measured 1,076 across 49 files.
Agent counts drift within days. A census script one-liner at authoring time
keeps leaf sizing honest.

## 5. Name the frozen role/key lists verbatim in master.md

Execution went smoothly because the 18-role list was written out in full in
the contracts. Where a plan said only "the union of used roles," implementers
guessed. Freeze exact key lists in the parent doc; leaves reference them.

## 6. Record accepted visual/behavioral drift in the parent

TUI primary changed #F97316 → #FF6600 when converging on shared tokens.
Because master.md documented this as accepted drift, no reviewer flagged it
as a regression. Un-documented intentional deltas get re-litigated forever.

## 7. Orchestrator-side: failed subagents often landed their work anyway

Execution-side companion to the authoring pitfalls above — when running a
tree, treat `status=failed/timeout` leaves as "verify, then salvage," not
"re-dispatch." Decision tree, recurring parent-review defect classes, and
commit hygiene: `references/subagent-failure-salvage.md`.

## 8. Design-phase decisions must be written as contracts/non-goals in master.md

When a tree follows an in-session design discussion, the user's resolved
answers belong in master.md, not just chat history. Write them as contract
fields, leaf Notes warnings ("do not simplify X into Y"), and explicit
non-goals with the reason. Verified 2026-08-30 (quota-reset-resilience): the
session settled retry-on-402 default, per-credential-key blocking, no
fuzzy-string/timezone parsing, 24h soft-stop ladder, first-available
fallback — each landed as a contract field or named non-goal. Without the
written non-goals, a leaf implementer re-litigates the design mid-execution.

## 9. Sweep the design against real code before freezing contracts

Before writing master.md, gap-sweep the discussed design against actual code
paths and fold findings into the tree. Recurring checks: (1) duplicate client
stacks — integrate at EVERY implementation (e.g. OpenAI-compat + Anthropic-
native clients, each with its own doRequest/retry loop; missing one means
aliases routed through it bypass the feature); (2) existing mechanisms that
already implement part of the design (rotation order IS a fallback chain —
contract with it, don't build a parallel one); (3) sibling-vs-nested error
semantics — a new error may need to exit one retry loop while still
triggering another layer's rotation; two "retryable" meanings coexist by
design, warn leaves against merging them; (4) repo invariants constraining
surfaces (TUI/GUI parity, WS event classification, lowercase UI text);
(5) shared-pool identity — things keyed by "provider" are often really keyed
by credential and need a stable non-secret fingerprint.

## 10. Contract text must survive an implementer reading ONLY the contract (2026-09-04)

Every behavioral sentence in a contract gets taken literally. Two real
cases from chat-dispatch-ux: (a) master.md said "never ReviewApproved for
error steps" with the fix sited at the ~150 skip block — but the no-review
policy path auto-approves EARLIER (~line 105), so the sited fix alone could
not satisfy the contract; the implementer had to hoist the gate above all
policy paths (correct, but discovered via red-phase failure + reasoning the
author should have done). (b) "verify `go test -p 2 ./internal/daemon/ -run
Schema`" — there was no such test; the leaf's sanctioned-fallback language
saved it, but the verify command was invented, not checked. Authoring rule:
for each contract, ask "can an agent satisfy this by editing ONLY the code
region I named?" If not, either name the earlier/other site or state the
invariant without siting the fix. Grep the leaf's own verify commands for
test-name existence before publishing the leaf.

## 11. Anchor precision: field vs struct-path, and hidden gating (2026-09-04)

Two anchor classes failed in the same tree despite a recon pass:
(a) `session.go:56` was cited as "Session.CWD" — line 56 is
`DetectionContext.CWD` inside the DetectionContext struct; Session carries
it as a POINTER field at :79 (`sess.DetectionContext != nil` guards
required). Cite the full access path (`Session.DetectionContext.CWD`),
not the struct-member line. (b) components.go:1422 was cited as the
SetSchemaModeConfig wiring site — `c.AgentRegistry` is nil there (the
registry is constructed at ~2251 inside `if cfg.MultiAgent.Enabled`).
Grep where the receiver object is CONSTRUCTED, not just where the
sibling call sits. Related: one leaf contract specified
`filtered.SetSchemaMode(...)` but FilteredToolRegistry does not implement
SetSchemaMode — the interface assertion would silently no-op. Before
freezing a call site on a wrapper type, verify the METHOD exists on that
type (grep the type's methods), or contract against the wrapped object.

## 12. Anti-findings: name what must NOT change, with the reason

Leaf 01's "polling loop, timeouts, and logging preserved exactly" kept the
implementer from "fixing" the 2s-ticker-then-check latency pattern; leaf
02's event-topic note ("subscribers depend on it — topic unchanged") kept
task.completed intact. Both anti-findings prevented well-meaning scope
creep during implementation. For every contract, add one "do not change"
line for the most tempting adjacent refactor (timing constants, topic
names, log strings callers parse, error-prefix shapes downstream code
matches on).

## 13. E2E/config-boilerplate leaves carry the highest post-dispatch bug rate — plan iteration, not one-shot (2026-09-04, chat-dispatch-ux leaf 10)

The nine code leaves landed first-try; the ONE leaf writing a
scratch-daemon e2e script needed three in-session fix cycles, each found
only by actually running against a live daemon:

1. `set -u` + a variable referenced before assignment → crash
   misreported as a provider SKIP (the SKIP path masked the script bug;
   distinguish "provider answered with an error" from "script crashed"
   BEFORE classifying).
2. The minimal scratch config omitted the one flag that constructs the
   component under test (`multiagent.enabled` gates AgentRegistry
   creation → `specs=0` → every turn fails "no agent available"). A
   MINIMAL config is not a VALID config: enumerate the construction
   gates in components.go (grep `if cfg.<X>.Enabled`) and set every one
   the transcript's path needs.
3. `session list --json` shape assumption crashed the parser before the
   skip/fail classification could run.

Also: a live-daemon e2e run FAILS whenever ANY sibling session leaves
the tree mid-edit (three consecutive build breaks from sibling lanes —
each transient, none the script's fault). Author e2e leaves with (a) a
"build failed → FATAL with log tail, never run stale binaries" rule
(that part worked), (b) the expectation of 2-4 fix iterations in the
orchestrator's review loop, and (c) fresh-binary builds per run so a
broken tree fails loudly at step 1 instead of producing false
assertion results.

Sibling corollary: a docs-only sibling commit (product rename) landed
mid-execution and made three leaf contexts' prose ("daemon") stale
without breaking any anchor — harmless, but check `git log` for
rename-class commits before dispatch since they invalidate dispatch-context
wording that implementers quote verbatim.

## 14. Authoring-time root-cause claims must be code-path verified end to end (2026-09-04, session-continuity)

A tree authored to fix "continuity is flaky" carried a verified-looking
root-cause chain — but the REAL blocker only surfaced after the fix
leaves landed: a pre-existing routing gate (dispatcher's intent-analyzer
ambiguity check) short-circuits status-shaped turns into canned
clarifications BEFORE the code the tree fixed ever runs, so the plumbing
worked and the assertion still failed. Authoring rule: when the plan
states "X is why Y happens", trace the RUNTIME ORDER of gates between
the user input and the code region you plan to fix, and grep for
short-circuit returns that fire earlier. A plan that fixes genuine
defects can still miss the ONE gate above them — budget a leaf-03-style
diagnostic leaf whose STOP clause converts a residual failure into a
precisely-attributed follow-up instead of a weakened assertion. The
tracking table is the right place to record "deps proven good via DB
forensics; real blocker = gate at file:line; design decision owned by
user."

## 15. Plan docs and snippets are English-only (2026-09-04, hard user signal)

The user twice flagged non-English characters ("garbled hanji
characters, not english") — once on garbled session summaries, once on a
plan doc. A leaf's example error-string carried a CJK fragment meaning
"not" inside `非-string`; the user demanded the plan be re-stated in
English, then commissioned a repo pre-commit hook
(`.githooks/pre-commit-ascii`) that fails commits introducing CJK/
Hangul/fullwidth characters in staged text files.

- Write every snippet, example error message, and string literal in
  English. To cite a CJK leak as evidence, TRANSLATE it inline ("a CJK
  char meaning 'not' inside the error string") — never leave raw CJK in
  a file that will be committed.
- After writing a tree, scan it before dispatch. macOS/BSD grep has no
  -P; use python:
  `re.search(r'[\u2E80-\u9FFF\uAC00-\uD7AF\uFF00-\uFFEF]', line)`.
  Em-dashes/arrows/box-drawing are fine; CJK/Kana/Hangul never is.
- The orchestrator's own commits (plan docs included) pass the ASCII
  hook once it exists — a dirty tree doc fails the integration commit
  like any source file.
