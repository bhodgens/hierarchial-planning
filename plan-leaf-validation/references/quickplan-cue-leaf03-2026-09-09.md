# Quickplan cue leaf 03 — implement record (2026-09-09)

Leaf: `docs/plans/quickplan-mode/03-prefilter-index.md` (QuickPlanCuePattern + prefilter cue guard + sweep verification).

## Landed (uncommitted, per dispatch instruction: no git add/commit)
- `internal/agent/quickplan_cue.go` — `QuickPlanCuePattern` verbatim per master Contract 3, single compiled package var, WHY doc comment (quickplan-vs-code/git undecidable from text alone, iter-20 adjudication; session-state derivation lives at the orchestrator, leaf 02).
- `internal/agent/embedding_prefilter.go` — `vote(vec []float64, input string)`; cue guard inserted immediately after `first := p.examples[neighbors[0].idx].Intent` with the leaf's verbatim rationale comment; `Match` call site passes `input`.
- `internal/agent/quickplan_cue_test.go` — 6 positive / 5 negative pinned table (negative list = the leaf's 4 + empty string).
- `internal/agent/embedding_prefilter_quickplan_test.go` — 5 identical quickplan fakes on axis 2 (exampleSet-style helpers), nearAxis2 query; Match with-cue → direct route intent=quickplan, same geometry without-cue → nil; direct `vote()` ok-flag asserted both ways under `p.mu.RLock`.
- `internal/agent/embedding_prefilter_test.go:370` — the only other `vote()` caller; `p.vote(query, "x")` (chat intent, cue-irrelevant).
- Verification green: `go build ./internal/agent/...`, `go test -run 'QuickPlan|Prefilter' -count=1`, `go test -short -count=1` (26s), gofmt + vet clean. No pre-existing prefilter fake used intent "quickplan" (grepped — Task 5 precondition held).

## Sweep blocker (pre-existing drift, NOT introduced by leaf 03)
Leaf Task 3 said "no code change needed" and pinned:
`python3 scripts/build_prefilter_centroids.py --corpus testdata/eval/classifier-adversarial-corpus.json5 --sweep`
Actual result: `json.decoder.JSONDecodeError: Expecting property name enclosed in double quotes: line 2 column 3`. Root causes:
1. `parse_json5` (`scripts/build_prefilter_centroids.py:36-61`) stashes double-quoted strings, quotes unquoted keys, strips trailing commas — but never strips `//` comments. The adversarial corpus header (rewritten in iter 19/20 commits `f8bb38b5`, `820c016f`) has 27 `//` comment lines; the old `classifier-test-corpus.json5` has none, which is exactly why the parser worked until the corpus rewrite.
2. `load_cases` (`:82-91`) reads `data["categories"]` with `expected_intent`/`expected_agent` — the old schema. The adversarial corpus is a flat `cases: []` with `input`/`intent`/`agent`/`ood`/`silver`. Even with comments stripped, a KeyError follows.
3. Sweep also requires the local embed server (`DEFAULT_URL http://127.0.0.1:8090/v1`, `embed_batch` 120s timeout). Server health was NOT probed — the probe command was denied by the user; treat the server as out of scope for the implement leaf.

## Open items for orchestrator / next pass
- Sweep script needs: `//` comment stripping (after string stash, before key quoting) + `cases:[]` schema handling (or dual-schema) in `load_cases`. Scope owner unassigned — reported, not grabbed.
- Task 3 verification (quickplan visible in per-intent sweep output) still owed once the script is fixed and the server is up. Do NOT write the centroid store to `~/.meept` — deployment action, explicitly forbidden by the leaf; "No deployment action taken" checklist item satisfied.

## Environment notes (transient, not durable rules)
- `python3` resolved to Homebrew 3.12 (no json5 module — irrelevant, the script is stdlib-only by design).
- macOS/BSD grep lacks `-P`; non-ASCII scan pattern that worked: `LC_ALL=C grep -n $'[\x80-\xff]' <files>`. The target file already contained em-dashes pre-leaf, so the pinned rationale comment's em-dashes were kept byte-exact (see plan-leaf-validation item 22).
