# Meept agent-loop result ceilings and the two routing patterns (2026-09-06)

Constants that bind (internal/agent/loop.go:3210-3226, verified this
session):

- `ToolResultMaxTokens = 3000` (~9k chars at the 3 chars/token heuristic).
  Applied via `ToCompressedJSON` → `compressMapResult` truncating long
  string values in the result map (executor.go). Note: the compression
  pipeline's map path only extracts `m["output"]` — a map result keyed
  `content` bypasses LLM compression but still gets structurally truncated
  by `compressMapResult`.
- The per-result budget SHRINKS late in a turn:
  `max(3000 × (1 − totalTokens/convBudget), 600)` — pagination math that
  assumes a constant page size is wrong by up to 5×.
- Iteration window 30k tokens, oldest-first eviction
  (`Conversation.TruncateByTokens`, keeps from the end backward). Early
  tool results vanish mid-turn — a model can never "hold" a long document
  across a turn; it must distill as it goes.
- Turn budget 50k tokens, graceful stop at 80%.

Design conclusion: the loop is built for bounded tool results feeding
in-context reasoning, NOT bulk document ingest. Fighting the caps is
wrong; route around them.

## Pattern 1 — file-backed ingest ("learn" workflows)

Tool writes the FULL artifact to disk, returns path + bounded preview +
`total_chars`. Agent pages the file with `file_read` (offset/limit,
never whole-file) taking notes per slice, synthesizes from notes.
Key detail: write the file BEFORE any pagination slicing so the on-disk
text is byte-identical to what the caller paginates; relative paths
resolve session-working-dir-first, config-fallback-root second; never
`os.Getwd()` in daemon code.

## Pattern 2 — in-tool map-reduce ("describe the shape" / gist)

Tool slices the artifact (~12k chars, ~500 overlap), sends each window
to a LOCAL summarizer model, reduces to a digest capped ~4k chars.
Meept seam: `c.SummarizerClient` (built components.go ~:843 via
`createAuxiliaryLLMClientWithResolver`, ref chain
`summarizer_model` → `small_model`); inject into tools via a nil-guarded
`Set*` taking `llm.Chatter`; gate the wiring on a config enable flag
(spends tokens per call). Nil chatter → honest config error at call
time, never a silent no-op. Fake `llm.Chatter` in tests must implement
Chat + ChatWithProgress + Config.

## Plan-authoring consequences

- Any leaf promising "the model reads the whole N00k-char output" is
  unimplementable; rewrite the workflow to notes-per-slice or digest
  before dispatch (the learn-from-video "40k chunks" step shipped wrong
  because no one checked the caps against the leaf text).
- Capability defaults: learn/faithful-extraction → Pattern 1 (verbatim
  detail survives); gist/shape → Pattern 2 (bounded, cheap).
- The caps themselves are correct — never propose raising
  ToolResultMaxTokens as the fix.

## What shipped against the caps (2026-09-06, tool-result-budget tree)

The decaying budget's failure modes and their fixes, now in the tree:

- `ResultSizer` optional interface (internal/tools/interface.go,
  Categorizer pattern; `GetMaxResultTokens` helper — cap at
  ToolResultMaxTokens happens in the LOOP, not the helper: the tools
  package must not import agent, import cycle). Loop consults per
  result via `resultBudgetFor(l.registry, dynamicToolBudget, toolName)`.
  transcript_fetch declares `TranscriptResultTokens = 1400` (~4200
  chars: a full 4k digest or preview arrives whole even at the
  600-token floor).
- CRITICAL wiring rule: the budget has TWO consumers —
  `compressionPipeline.CompressToolResult` (DESTRUCTIVELY rewrites
  `result.Result`) and `ToCompressedJSON` (read-side). The floor must
  be applied at BOTH; the pipeline is the binding site because it is
  destructive and runs first. Leaf wired only ToCompressedJSON and its
  tests passed — the harness ran with `compressionPipeline == nil`,
  so the destructive consumer was unobservable. When a value has
  multiple consumers, enumerate them and wire the destructive one;
  state which consumers a test harness exercises.
- `compressMapResult` (executor.go) now deterministic and
  metadata-preserving: sorted keys, primary content key
  (content/output/result → longest-string, lex-first tiebreak)
  processed LAST and alone truncatable; non-primary keys always copied
  whole (overflow → keep all + `_truncated`); `_truncated` set exactly
  when anything clipped. Before this, Go's random map order decided
  WHICH keys survived truncation — the model could lose `path` while
  keeping `timestamps`.
- Slices in skills must fit the 600-token floor: ~2k chars (~50 lines)
  per file_read request — a 400-line slice gets clipped late-turn and
  the model's next offset skips the tail forever.

## Test-assertion observability (same tree)

- `encoding/json` sorts map keys on marshal — "assert sorted key
  order" passes vacuously. Falsifiable determinism probe: byte-identical
  output across N runs under a TIGHT budget (where the old random-victim
  behavior differs run to run) + explicit all-keys-present assertion.
- `ToCompressedJSON` reserves ~200 chars for the JSON wrapper — budget
  math in tests/examples must subtract it.
- The wrapper's map path extracts `m["output"]` only: map results keyed
  `content` skip LLM compression (still structurally truncated).
  Choose the primary content key name per this asymmetry.

## Watchdog rescue turn (2026-09-07, second pass over the decaying budget)

The reasoning-only watchdog termination ("stopped after extended
thinking") was a guaranteed-failure loop for thinking-mode local models
(LFM2.5 on mlx_lm): the template thinks by default, the whole reply
lands in `reasoning_content`, and retrying unchanged re-fails
identically. Fixed: on the SECOND consecutive reasoning-only reply the
loop runs ONE rescue turn with `llm.DisableThinking()` (appended after
the agent's reasoning opts — single reasoning pointer, last apply wins)
plus a firmer nudge; a reasoning-only reply from the rescue terminates
immediately (rescued=true also leaves streakBreach=true — do NOT reset
streakBreach in the rescue branch, or the post-rescue reply reads as a
fresh streak and nudges forever). Guards tests updated:
rescue-success sequence and rescue-fails-terminates bound. General
pattern: when a watchdog terminates for a DETERMINISTIC model-mode
failure, retry once with that mode toggled off before giving up —
retrying unchanged re-fails identically.
