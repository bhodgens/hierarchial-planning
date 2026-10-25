# Contract verification and review discipline for leaf returns (2026-09-05, research-audit-tools tree)

Tree: 7 leaves, 3 waves, same-day execution, 7 commits. Cleanest run to date —
what made it clean is reviewable process, not luck. Session detail lives in
meept-development skill: references/plan-tree-execution-2026-09-05.md (this
file records the transferable protocol).

## 1. Verify agent CLAIMS against primary sources before accepting

Three claim classes verified this session — and verification is what converts
them from hope to knowledge:

- **API-drift claims** ("the brief said X but the library actually takes Y"):
  confirm with `go doc <pkg>.<Symbol>` before accepting. Real catch:
  ledongthuc/pdf NewReader takes io.ReaderAt not io.Reader; Page() returns
  no error (so bounds MUST be guarded in page-range parsing);
  GetPlainText(nil) documented safe. The leaf brief had paraphrased the API
  wrong — the agent correcting it is exactly where blind trust fails.
- **License claims** ("excelize is BSD-3"): read the LICENSE file in the
  module cache yourself (`$(go env GOMODCACHE)/github.com/xuri/excelize/
  v2@v/LICENSE`). The GPL-subprocess user rule makes this a hard gate.
- **"@latest resolves to pseudo-version, no vN tag exists"**: check via the
  go.mod line + module cache path. Trust but verify — it's one command.

## 2. Re-run tests yourself; interpret failures against sibling state

The builtin package was transiently broken TWICE by sibling in-flight leaves
(RED-phase test files referencing not-yet-written symbols). A failed
orchestrator re-run mid-tree means "check `git status` + who else is writing
this package", not necessarily "the reviewed leaf failed". Targeted run
filters (`-run 'PDF|CSV|XLSX'`) pass even when the whole package cannot
compile, if the sibling breakage is in another test file — know which you
are looking at.

Mid-flight background signals (proc_* exits from the LEAF's own iteration
loops, test logs in /tmp) are early warnings, not verdicts: a FAIL in run N
is often fixed by run N+1. Read the LATEST log before re-dispatching a leaf
that is still running.

## 3. Disclosed deviations are the product, not noise

Pattern across ALL four accepted deviations — the agent violated a leaf
scope line in service of the leaf's own acceptance criteria, and SAID SO:

| Deviation | Why it was correct |
|---|---|
| "config ONLY" leaf edited catalog_test.go | test pinned the OLD entry shape; the leaf's "tests green" criterion forced it |
| Replaced existing same-named entry | duplicate names structurally collide (manager keys by name); net diff vs HEAD insertions-only |
| Omitted conditional SetWorkingDir setter | ctx convention already resolved paths; setter = dead API = U1000 pre-commit blocker |
| In-tool fence instead of SetFenceChecker | registered FenceChecker can be nil/disabled; the contract's fence must hold unconditionally |

Review question for every deviation: does it serve the CONTRACT, and was it
disclosed? Both yes → accept and record in the tracking table Notes column.
Undisclosed scope change → re-dispatch.

## 4. Frozen contracts pay for themselves only if verbatim in dispatch

Every dispatch context carried the contract INLINE (never "see master.md" —
delegate_task children inherit zero conversation). Result: zero
paraphrase-drift integration failures across 7 leaves and 4 frozen contracts
(A pdf_read, B webfetch-sniff, C spreadsheet_write, D mcp-catalog). The
writer seams (SheetSpec, writeCSV/writeXLSX, extractPDFText) were frozen in
branch orchestrators and consumed across sibling leaves WITHOUT coordination
— the parallel CSV and XLSX leaves met perfectly because both briefs pinned
the same struct shape and said "do NOT redefine".

## 5. Shared-file serialization (components.go)

Two leaves needed registration blocks in the same file → dispatched
sequentially, not parallel. Cheap insurance; the registration region was
re-grepped before each edit because the prior leaf had just moved it.

## 6. Integration tail

- `go build ./...` + corruption grep
  (`grep -rcE '^\s+[0-9]+\|' --include='*.go' <dirs>` = 0).
- Sibling-session breakage in FOREIGN packages (mid-TDD retain_typed_test.go
  referencing an unimplemented symbol from a sibling plan tree): identify
  ownership (`git log --all --grep` + docs/plans/<sibling-tree>/), verify
  YOUR packages green, do not touch their files. The sibling's own next
  commit resolved it within the hour.
- Doc-count sweep BEFORE writing numbers: `grep -c '"name":'
  config/mcp_servers.json5` beat the docs' stale "21 servers" (actual 22).
- Tracking table: per-leaf COMPLETE with commit hashes + a PROJECT COMPLETE
  block, final commit.
