# Reference: when a leaf spec's prose contradicts its own mandated tests

Worked case: chat-dispatch-ux leaf 05 (meept, 2026-09-04). The leaf spec
mandated a reply-guard heuristic with a literal ">40% non-symbol word
content" prose check, then shipped six EXACT test cases in the same doc —
and the literal prose reading failed three of the spec's own tests:

- **JSON is letter-dense.** A raw `{"status": "running", "uptime_seconds": ...}`
  dump is ~85% letters/digits by character count, so a char-ratio "symbol
  content" check classifies the machine dump as prose and passes it through.
- **Rosters embed prose fragments.** The offender roster contained a full
  English sentence ("You are Meept, an autonomous assistant serving your
  creator.") — enough running text that any sentence-level leniency defeats
  the detector.
- **Char-counting is the wrong unit.** Machine output is line-structured:
  bullets (`- `/`* `), headers (`#`), table rows (`|`), JSON braces, and
  `"key": value` lines vote STRUCTURE; only plain-text lines vote prose.

## The fix pattern

Re-implement the spec's INTENT as a **line-shape ratio** instead of its
literal character arithmetic: count non-blank lines, classify each as
structural (bullet/header/pipe/brace/quoted-key) or prose, and keep the
spec's 0.40 threshold. This passed all six mandated cases on the first
try, kept ordinary markdown answers byte-identical, and still guarded a
machine dump carrying one embedded sentence. Document the deviation in the
completion report ("spec heuristic literal reading fails spec's own tests;
implemented line-shape ratio preserving the spec's threshold and intent").

## Protocol for the general case

1. Implement the spec's test cases FIRST (they are the binding contract —
   the spec says so: verify RED, implement, verify GREEN).
2. If the prose heuristic then fails its own tests, do NOT weaken the
   tests and do NOT hand-tune thresholds until green. Treat the mismatch
   as a spec bug and re-derive the heuristic that satisfies the tests
   while preserving the stated intent (thresholds, pass-through
   guarantees, category naming).
3. The "cheap check" phrasing in a spec is a hint about COST, not a
   normative algorithm — a regex-free line classifier is a faithful
   implementation of "cheap".
4. Record the deviation explicitly in the completion report so the review
   agent judges one coherent diff (mirrors the pre-implemented-leaf
   reporting discipline in multi-agent-git-coordination #16).
