# Anchor-Verification Sweep — verify plan code anchors before authoring

Plans cite `file:line` anchors as implementation contracts ("hook at
enforcement.go:1743", "wire at wiring.go:162-169"). An unverified anchor
sends the leaf agent to patch the wrong site or invent a nonexistent
integration point — expensive to discover mid-execution. Run this sweep
BEFORE writing any plan document in a code repo.

## Sweep checklist (~6-10 greps, 5-10 minutes)

1. **Primary type + constructor.** Locate each struct you'll extend:
   search `type X struct` (and `func NewX`), note real line numbers from
   the search output (search_files returns clean line-numbered hits — no
   read_file `N|` prefix risk).
2. **Hook-point fan-out.** Search the repo for call sites of the function
   the new code must observe (e.g. `\.Create\(ctx`). If N producers all
   funnel through ONE function, the plan needs ONE hook there — not N
   integration points. Producers that bypass the funnel (different record
   shape, not a finding) get their own direct-emission task.
3. **Import-cycle proof.** Before the plan says "reuse Y from package Z,
   no cycle": grep Z's import block for your packages
   (pattern like `"github.com/…/internal/(a|b|c)"`, path=internal/Z).
   0 hits IS the evidence; quote it in the plan instead of asserting.
4. **Wiring sites.** Find where the object is CONSTRUCTED in production
   code (`NewXStore` minus `_test.go` hits) — that's the wiring leaf's
   insertion point. Note dual paths (shared-handle vs standalone) if
   construction branches; the plan must mirror both.
5. **Surface anchors.** RPC/HTTP registration maps, CLI command
   constructors, docs section headings — verify each exact name/line
   exists before citing it.
6. **Greenfield check.** Grep the planned new package/dir name; 0 hits =
   greenfield, cite it. Non-zero = survey first (Pitfall 30).
7. **Convention source.** Name the existing file the leaf should mirror
   (house SQLite pattern, store constructor, setter style) and verify its
   line range — plans that point at a pattern file produce consistent
   leaves across independent agents.
8. **Type-alias indirection.** A file may be pure re-exports
   (`type X = pkg.Y`); grep the alias to find where the type is REALLY
   defined before citing a line for its fields.

Plan documents cite anchors as file:line plus the identifying line's text.
Leaves re-verify with `terminal cat` immediately before patching — line
numbers rot across refactors.

## Worked example — meept tamper-evident audit log (2026-09-05)

Sweep results that shaped the tree (`docs/plans/tamper-evident-audit-log/`):

- `type AuditStore` enforcement.go:1685, `Create` :1743.
- Fan-out: ALL finding emitters call `AuditStore.Create`
  (scheduler_jobs.go:396, manager.go:1317/1544, goal_loop.go:1415) → one
  post-insert `ChainEmitter` hook chains PostTurnAuditor + PeriodicAuditor
  + manager paths; only gate results (goal_loop.go:1014, not findings)
  emit directly.
- Construction: wiring.go:162-169 branches sharedDB (`NewAuditStoreFromDB`)
  vs standalone path → chain store mirrored both.
- Cycle proof: internal/security imports 0 of employee/bot/agent/tools →
  safe for the `internal/auditlog` redactor to reuse `OutputMonitor`.
- Greenfield: `auditlog` 0 hits under internal/.
- Aliases: employee/gate.go is pure `type X = gate.X` re-exports → real
  `GateResult` fields cited from internal/gate/gate.go:62.
- Surfaces: `agents.audit.list` handler.go:123 (RPC registration),
  api_handlers.go:78 (HTTP), CLI `newAgentsAuditCmd` agents_cmd.go:1235.

Result: zero anchor-driven plan rewrites during authoring; every cited
line number was real at authoring time.
