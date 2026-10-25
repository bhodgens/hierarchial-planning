# Leaf-03 Recovery: Interrupted Orchestrator + SSE Scanner Bug (2026-09-01)

Tree 02 leaf 03 (client-unification) of meept's llm-resilience-forest.
The orchestrator was interrupted mid-leaf; the parent recovered the ~90%-done
WIP, fixed a latent production reader bug the new tests exposed, repaired
collateral damage, and committed as `962e9924`.

## Recovery sequence (what worked)

1. Triage `git status` against the leaf's file ownership. WIP present:
   loop.go, anthropic.go, client.go, errors.go + test files, 2 new test files.
2. Validate structure by grep, not rewrite:
   - Quota invariant: `QuotaResetError` errors.As early-exit appears BEFORE
     `Classify` in all five loops.
   - Branch placement: agent loop's ThrottleBackoffError branch BEFORE the
     RateLimitError branch (loop.go ~4437 before ~4449) + a second branch in
     the streaming path (~3454).
   - Constants gone: `maxRetries`/`streamMaxRetries`/`anthropicMaxRetries`
     replaced by `ShortRetries` from `FailurePolicyConfig` (nil-safe default 3).
3. Run full gates: `go test ./internal/llm/ ./internal/config/ -count=1`
   (llm suite ≈ 5 min — run via background terminal), `make analyzers`.
4. One legit failure: `TestAnthropicChatWithProgress_RetryAfterThenSuccess`.

## The SSE scanner bug (production-grade, latent for months)

**Symptom:** retry test showed 2 server hits (retry worked) but
`resp.Content == ""`. Every existing fixture-based test passed.

**Four-probe diagnosis chain (each probe decisive):**

1. Deterministic failure → not a flake.
2. Scanner over `strings.NewReader(sse)` → 5 events, data lines intact.
   Scanner LOGIC was fine for single-chunk input.
3. Scanner over `httpResp.Body` directly → **0 events, no error**.
   Reader-type-dependent.
4. iotest matrix: OneByteReader = 5, HalfReader = 5, **DataErrReader = 0**.

**Root cause (two bugs, one function):**

- `Scan()` checked `err == io.EOF` BEFORE consuming `n` bytes. Readers that
  deliver the final bytes TOGETHER with EOF (http.Response.Body,
  iotest.DataErrReader) had those bytes silently discarded — the entire
  trailing read vanished, so a body delivered in `data+EOF` chunks yielded
  zero events. (strings.Reader returns `(n, nil)` then `(0, EOF)`, which is
  why every hand-built fixture passed.)
- Separately, the chunk loop dropped the byte at `i == len(s.buffer)-1`
  via `s.buffer = s.buffer[:0]` before writing it to the current line —
  any line split across a read-chunk boundary lost its tail.

**Fix:** append `chunk[:n]` BEFORE handling EOF (fall through and parse when
buffer non-empty; next Scan's Read returns `(0, EOF)` and the flush runs);
iterate the buffer by index, keeping the unconsumed remainder.

**Regression coverage:** `internal/llm/sse_scanner_test.go` —
AllEventsAtOnce / OneByteChunks / HalfChunks / DataWithEOF / NoTrailingNewline.
Lesson: a parser tested only with `strings.Reader` fixtures is untested
against production readers; always include an iotest split matrix.

## Collateral damage from the interrupted run (check class, not instance)

- `errors_test.go` cut 23 tests → 3. The deleted tests covered functions
  that STILL EXIST (ParseRateLimitBody, BackoffWithJitter, extractInnerJSON,
  UserMessage suite) — a sloppy in-file rewrite, not intentional removal.
  Restore via `git show HEAD:<path>`, then re-add only genuinely new tests
  (here: ThrottleBackoffError Error/Unwrap/errors.As trio). Enumerate with:
  `diff <(git show HEAD:f | grep 'func Test') <(grep 'func Test' f)`.
- Distinguish legit mechanical renames (`wantAttempts: maxRetries` →
  `defaultShortRetries` after the constant removal — correct) from
  collateral deletion. Judge hunks separately.
- Dead symbols from the refactor (`isRetryableStreamingError`, unused test
  var) blocked the repo's unused-code pre-commit gate. Delete them; avoid
  `--no-verify`.

## Concurrent-writer hygiene during recovery

- A concurrent `git stash pop` swept a sibling session's WIP
  (compress/memory/scheduler "codebase review fixes") into the working
  tree. Split `git status` against the leaf's ownership; saved out-of-scope
  diffs to /tmp, `git checkout --` them, surfaced to the user. Never commit
  another session's in-flight work inside your leaf's commit.
- A second leaf implementer (tree 04 leaf 03, slot gate) was dispatched
  into client.go only AFTER leaf 03's commit freed it — stagger map
  maintained in the parent's todo list.
