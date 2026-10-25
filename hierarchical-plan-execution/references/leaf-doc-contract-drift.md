# Leaf-Doc Contract Drift — Verify the Leaf's Code Snippets Before Implementing

Plan-tree leaf docs are written by an orchestrator model and can contain
illustrative snippets whose API details DON'T match the real repo. Treat the
leaf's CONTRACT section (type names, signatures, JSON tags, file paths,
behavior requirements) as binding, but grep-verify every concrete API detail
in its snippets and runner commands before implementing.

## What actually drifted (2026-08-29, meept WikiSkill leaf 01)

1. **Wrong arity in the snippet**: leaf said `pkgid.Generate()`; the real
   signature is `Generate(prefix string)`. Trust the definition site, not the
   doc: `grep -n "func Generate" pkg/id/`.
2. **Fictional test helper**: leaf's test used `testLogger()`; the package's
   actual discard-logger helper is `slogDiscardLogger()` (existing, in
   `applier_test.go`). Before writing any test helper, grep the package for
   an existing one — white-box test files share one namespace, so a
   re-declaration breaks the whole test build.
3. **Runner command with uncheckable flags**: fine here, but leaf commands
   can also name helpers/flags that don't exist; verify each named symbol
   the same way.

## Protocol

1. Extract the contract: exported names, signatures, JSON tags, exact file
   paths, behavioral requirements (atomic rename, truncation markers,
   sampling order).
2. For each symbol the snippets reference: grep its DEFINITION in the repo
   and confirm arity/shape. For each test helper: `grep -rn "func <name>"
   <pkg>/` — reuse > define.
3. Implement the contract exactly; implement snippets only as far as they
   agree with the real API.
4. When a snippet is wrong, follow the corrected usage and list it under the
   leaf's "Deviations from spec" section (the leaf template provides one) —
   the reviewer compares against the contract, and silent divergence without
   a deviation note reads as a gap.

Signal that drift is likely: leaf docs written in a wave (many leaves at
once, per a master plan) — the more prose and pseudo-code per leaf, the
higher the odds of arities/helpers invented from pattern-matching rather
than read from the tree.

## Drift class 4: the Files: list itself is stale (function-home drift, 2026-09-05)

A leaf can cite the right FUNCTION names but attach them to the wrong
FILE: `skill-authoring-and-media-ingest/04` listed "scanTier/loadSkillFile
population point: internal/skills/discovery.go", but both live in
source_file.go (discovery.go only holds the Discovery orchestrator).
Grep-verify named symbols finds this instantly — but only if you grep
BEFORE reading the cited file: the trap is opening the cited file,
assuming the missing function means drift in the CODE, and planning
around the wrong anchor. Resolution: `grep -rn "func <Name>" internal/`
first, implement at the ACTUAL home, and record the file-list correction
under Deviations ("loadSkillFile lives in source_file.go, not
discovery.go as the leaf's file list implied"). Reviewer compares against
the contract — the contract names the functions and their behavior, not
their file, so the deviation is a documentation fix, not a contract
violation. Related hygiene: when the leaf says "extend <existing>_test.go"
but sibling leaves work the same package, writing the new tests in a
sibling file (e.g. discovery_linked_assets_test.go) satisfies the intent
(fixtures exercised) without merge churn — note it as a deviation.

## Sibling failure class: symbol exists, behavior composes badly

Symbol-level verification (protocol above) does NOT catch the case where
every pinned symbol exists with the right signature but two PRE-EXISTING
behaviors conflict when composed — e.g. the leaf's pinned production flow
marks a row `is_current = 0` while its pinned test loads that row through a
reader that filters `is_current = 1`. Only running the pinned test RED
exposes it. Triage and the swap-the-loader-keep-the-assertions fix:
see `leaf-pinned-test-impossible-read-path.md`.

## Drift class 5: structural-ordering claims (init-order prose, 2026-09-06)

Leaf prose asserting EXECUTION ORDER ("tools initialize before X; register
at the END of Y") is a hypothesis about control flow, not a contract — and
line-number anchors make it worse, not better. In
skill-authoring-and-media-ingest/05 both anchors were real line numbers
attached to a FALSE ordering claim: initializeSkills (~:869), the SkillWriter
assignment (~:1183), and registerBuiltinTools (~:2237) all live inside ONE
function (NewComponents), so execution order = file order, and registering
"at the end of initializeSkills" would have injected a NIL writer into the
skill tools. Protocol:

1. For each cited anchor, find its ENCLOSING function: `grep -n "^func "
   <file>`, take the last func line at-or-before the anchor. Anchors in
   different functions can execute in an order unrelated to their line
   numbers.
2. Derive order from call structure (or a wiring test), not from the prose.
   Pick the registration point where the dependency handles provably exist.
3. When the leaf carries an explicit fallback clause in Notes ("if you find
   the writer available earlier, prefer X — but ONLY with test evidence"),
   that clause is the tiebreaker. Implement the branch the evidence
   supports and record the resolution under Deviations.

Two supporting hygiene rules from the same session:

- Prove handle-liveness FUNCTIONALLY in wiring tests: execute the tool
  end-to-end through the real dependency (a nil writer/registry fails with
  its own "unavailable" error before doing work) instead of asserting
  struct fields or trusting constructor comments.
- `gofmt -l` flagging a leaf-owned file does NOT mean you introduced debt.
  Compare deltas against the HEAD blob (`git show HEAD:<path> > /tmp/x.go
  && gofmt -l /tmp/x.go`; or diff the `gofmt -d` outputs) — identical
  deltas are pre-existing. Reformatting them inside a leaf violates
  single-writer discipline and pollutes the review diff; leave them for
  the orchestrator.

## Drift class 6: the leaf's suggested MECHANISM contradicts its own CONTRACT (2026-09-06)

A leaf can pin a correct behavioral contract AND, in its Context/Notes
prose, suggest an implementation mechanism that violates it. In
transcript-large-corpus/04-wiring: the contract said the injected chatter
is "c.SummarizerClient (chain default)" or a dedicated
TranscriptSummarizerClient — but the Context prose suggested falling back
to the existing `summarizerChatter` param as the chain default, and that
param is the MAIN LLM provider (the prose itself flagged it as wrong two
sentences earlier). Implementing the suggested fallback shipped the wrong
client for the chain-default case and passed every compile check; only a
contract-only re-read during end-review caught it.

Protocol addition:

1. When the leaf offers both a CONTRACT (post-conditions, verbatim
   behaviors, quoted log lines) and a suggested MECHANISM (parameter
   names, fallback values, "prefer the minimal change: ..."), treat the
   contract as the test oracle and the mechanism as a hint that may be
   stale.
2. Derive each fallback/default from the contract's own words, not from
   whatever value is already in scope at the call site. "Closest
   available value" is exactly how the wrong-but-convenient client got
   suggested.
3. End-review check: re-read ONLY the contract/interface-contracts
   section and test your diff against it, deliberately ignoring the
   mechanism prose you implemented from. Do this after implementation,
   when you can no longer tell contract from suggestion by memory.
4. Record the divergence under Deviations ("selected chain-default
   SummarizerClient at the NewComponents call site instead of the leaf's
   suggested summarizerChatter fallback — the contract requires the
   local summarizer; param 12 is the main provider").

Corollary — typed-nil at injection points: when the contract says "nil
client -> leave nil", guard the CONCRETE pointer (`if *T != nil`) before
assigning into an interface parameter. `var chatter llm.Chatter =
typedNilPtr` yields a non-nil interface that dodges every downstream nil
check (golang-safety's nil-interface trap, instantiated in wiring code).
Related: leaf-verbatim-contract-messages.md already notes named func
types need plain-nil guards, not typed-nil-interface rituals — same
lesson at a different site.
