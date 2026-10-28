# Rreviewing parallel tool leaves
When to use: orchestrator adjudications across parallel leaves.
Lesson: review discipline for skill-authoring trees.

# Reviewing Parallel Tool Leaves — Orchestrator Adjudications (2026-09-06, skill-authoring-and-media-ingest)

In-session review calls from a 4-leaf parallel wave into
internal/tools/builtin + internal/skills that the leaf docs and review
checklists did NOT settle. Each was resolved by tracing real code, not by
asking the implementer to conform.

## 1. Sibling error-return-style split: do NOT "normalize"

Leaf 02 returned `nil, fmt.Errorf(...)` from Execute; leaf 03 returned
`tools.NewErrorResult(msg), nil`. Both are established package patterns —
counted at review time: 381 `nil, err` sites vs 58 `NewErrorResult` sites in
internal/tools/builtin. Before demanding uniformity, trace the consumer:

- `tools.Registry.Execute` (internal/tools/registry.go) converts a Go error
  return into `NewErrorResultErr(err)` and passes an existing `*ToolResult`
  through as-is — both styles converge on `*ToolResult{Success:false}`.
- The registry's retry wrapper inspects `result.Success`/`result.Error` as
  well as Go errors, and the agent executor retries on `toolErr` via
  `IsRetryable` — neither style escapes retry inspection outright.

Verdict: APPROVED BOTH. The review bar is "matches an established package
pattern", not "matches the sibling leaf". A rewrite to unify style is scope
churn; record the adjudication in the tracking table instead.

Method: grep-count each style, read the ONE consumer funnel
(Registry.Execute), state the convergence, move on.

## 2. `_ = ctx` trips the ignored-error pre-commit gate

The repo's pre-commit gate blocks newly-added `_ = <expr>()` sites — and it
also counts the unused-parameter suppression `_ = ctx` in a method whose
signature must keep the parameter (tools.Tool contract). The fix is NOT a
nolint and NOT dropping the parameter: replace the blank assignment with a
comment stating why ctx is unused ("part of the tools.Tool contract; this
tool performs no context-sensitive I/O"), gofmt, re-run the scoped test,
re-add, re-commit. Symptom signature: commit blocked with "N newly-added
ignored-error / panic(err) site(s)" while `git diff --cached` shows a bare
`+	_ = ctx`.

## 3. Config-path drift: mirror the sibling section's real shape

Leaf 05's contract wrote `cfg.Tools.Transcript` — no `Tools` config struct
exists; `Browser` is a TOP-LEVEL config section. Protocol: grep the sibling
feature's config (`type BrowserConfig`, where it hangs off `Config`, where
its defaults freeze) and mirror exactly: top-level
`Transcript TranscriptConfig` field + `DefaultTranscriptConfig()` + frozen
defaults inside `DefaultConfig()` + the file's gendoc comment tags. Record
under Deviations ("no Tools struct; [transcript] is top-level, mirroring
[browser]"). This is the config-path variant of leaf-doc-contract-drift.md
class 4 (file-home drift): the contract's FIELD names were right; the PATH
to reach them was invented from pattern-matching.

## 4. Denied rm of leaf scratch artifacts: surface, never delete

Both the leaf AND the orchestrator were denied `rm -rf` of the leaf's
abandoned scratch package (internal/tools/leaf01check/ — a fake-runner
isolation shim the leaf used while a sibling's half-written file broke the
real package). The standing user rule (surface stray dirs, don't delete)
applies to the orchestrator too, even when the subagent explicitly asks
"orchestrator should delete it". Handling that worked: leave the artifact in
place, exclude it explicitly from gate attribution (an untracked Go package
still compiles into ./... and shows up green in go test ./internal/tools/...),
flag it in Observations, and hand the user the exact cleanup command as the
final next step. Never route around a denial with a different deletion
command or a different actor.

## 5. The in-session review finds seams the leaves' green tests miss

All four leaves passed every review gate (contracts, tests, gofmt, vet,
line-corruption) and STILL shipped two cross-leaf functional gaps, caught
only by a post-tree review of the delivered CHAIN:

- Leaf 03's skills_patch resolves skills via Registry.Get — but leaf 02's
  skills_create wrote via lifecycle.Writer.WriteSkill, which never
  Register()ed into the registry. Same-session create→patch failed with
  "not found in the registry". The leaf-05 wiring test MASKED this: it
  hand-registered the created skill into comps.SkillRegistry before
  patching. LESSON: a test that hand-feeds its dependency hides exactly
  the wiring gap it exists to prove. Grep the delivered chain for
  producer→consumer seams across sibling leaves.
- Leaf 01's 100k-char transcript cap was unreachable: the agent loop caps
  every tool result at ToolResultMaxTokens (~9k chars, applied via
  ToCompressedJSON). A tool's effective output bound is
  min(its own cap, the loop's per-result cap). Size-bounded tools whose
  consumers need full content need pagination params (offset/max_chars +
  total_chars in the response) from day one.
- Length-derived result flags (e.g. `truncated`) must be computed BEFORE
  any mutation that appends a suffix/annotation — computing after makes
  the flag true only because the annotation pushed the length past the
  cap.

Fix dispatch: batch by file ownership (writer.go vs transcript_fetch.go),
parallel subagents, each told to ignore transient sibling breakage; TDD
per bug. A sibling session may commit the fix subagent's working-tree
output under its own message before you commit — verify content
correctness, skip re-landing, cite the existing sha. Committing by
EXPLICIT PATH is the shared-index escape hatch when a sibling's staged
foreign files drag their packages into pre-commit analyzer scope (mutexio
blocked on orchestrator_*_test.go that was already committed at HEAD and
touched by no one in this session).

## 6. Architecture-limit reviews: bound the consumer, not just the tool (2026-09-06, transcript-large-corpus)

The fix wave above closed the tool-side gaps, and the USER then asked the
right architectural question: what does the AGENT LOOP still impose?
Answer shaped a second tree — worth repeating because "tool ships with a
cap" reviews stop one layer short:

- The effective ceiling for any tool result is
  min(tool cap, ToolResultMaxTokens (3000 tok), the DECAYING
  dynamicToolBudget (toward 600 tok as the turn consumes budget),
  the 30k-token iteration window, the 50k turn budget). Every one of
  those layers clips INDEPENDENTLY, and the dynamic one makes identical
  calls order-dependent.
- The decaying budget's failure modes: (1) a paginated page clipped
  mid-turn makes the model compute its next offset from the SHORTENED
  text — the page tail is skipped forever (silent data loss);
  (2) identical calls return different content by turn position
  (non-reproducible); (3) compressMapResult iterates Go maps in random
  key order and truncates wholesale — WHICH metadata keys survive is
  random (the model can lose `path` while keeping `timestamps`);
  (4) late-turn verification reads are the most degraded — the budget
  punishes thorough turns.
- Fixes that landed (tool-result-budget tree): ResultSizer optional
  interface (Categorizer pattern) so tools declare a token floor
  (transcript_fetch: 1400) the loop never compresses below, capped at
  the global ceiling; compressMapResult made deterministic (sorted
  keys, primary content key truncated LAST and alone, metadata keys
  always whole, `_truncated` on any clip); skill slices sized to fit
  the 600-token floor (~2k chars).
- The user-preferred shape: file-backed ingest (full text to disk via
  output_path, bounded preview + path in-conversation, agent pages via
  file_read) for "learn", local-summarizer map-reduce digest for
  "describe the shape", routing summaries through the EXISTING
  SummarizerClient/summarizer_model→small_model chain rather than a
  new mechanism. When a workflow needs bulk content, route around the
  conversation, don't raise the caps — the caps are correct.

### §6.1 The floor must reach EVERY destructive consumer (2026-09-06, tool-result-budget tree review catch)

Leaf 01 wired the new floor at `ToCompressedJSON` only. In-session
review found the OTHER consumer: `compressionPipeline.CompressToolResult`
DESTRUCTIVELY rewrites `result.Result` (`result.Result = compressedResult`),
and it ran at the UNLIFTED dynamic budget — a real daemon with a pipeline
enabled would have LLM-compressed a floor-declared tool's digest to ~600
tokens BEFORE the floor at ToCompressedJSON ever applied. The floor was
wired to the harmless consumer and missed the destructive one. Fixes in
review: compute the per-result lifted budget ONCE per result and feed
BOTH consumers (`pipelineBudget` at the CompressToolResult call; same
value at ToCompressedJSON).

Rule: when a value (compression budget, cap, deadline) has MULTIPLE
consumers, enumerate them all and classify which are destructive/
irreversible — the destructive one is the binding site. Wiring only the
read-side consumer is a production no-op. Test gap that hid it: the
leaf's loop-level harness ran with `compressionPipeline == nil`, so the
destructive path was unobservable by construction — when claiming
coverage of a budget/cap behavior, state which consumers the harness
actually exercises.

### §6.2 Spec-side test assertions that cannot observe reality (2026-09-06, same leaf)

The leaf spec demanded "assert sorted-key emission order" —
unobservable: `encoding/json` sorts map keys on marshal, so EVERY
implementation emits sorted order and the assertion passes vacuously.
Approved replacement: (a) byte-identical output across 100 runs under
a TIGHT budget (random key-drop victims differ per run today — a
generous budget can pass determinism vacuously via copy-all), plus
(b) an explicit all-keys-present/whole assertion. Related arithmetic
trap: `ToCompressedJSON` reserves ~200 chars of the token budget for
the JSON wrapper — the spec's example math ("4200-char content fits
1400 tokens") ignored the reserve; tests used 3900/5000-char contents.
When a spec's test EXAMPLE is wrong but its INTENT is clear: fix the
example, implement the intent, record both under Deviations.

### §6.3 Sibling sweep can PARTITION your leaf's files across two commits (2026-09-06, same tree)

New sweep variant: the sibling session committed the leaf's
working-tree output WHILE the orchestrator's own commit was in flight —
but only PART of it. The orchestrator's `git commit <paths>` then
succeeded for the tools-pkg files (still unstaged) while the agent-pkg
files were already inside the sibling's commit. Outcome was benign —
the two commits partitioned the leaf's diff with zero overlap — but
the "commit failed → re-dispatch" reflex would have double-landed
agent-pkg hunks. Protocol: when a commit unexpectedly reports
"pathspec did not match" or lands fewer files than intended, `git log
--all -- <missing files>` FIRST; verify the sibling commit's content
against the leaf's report (it included the orchestrator's in-review
pipelineBudget fix — content-verified, adopted); cite BOTH shas in the
tracking table as the leaf's landing record; do not re-land or revert
for cosmetic regrouping.
