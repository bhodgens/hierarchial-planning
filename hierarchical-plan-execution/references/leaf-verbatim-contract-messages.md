# Verbatim contract messages vs error-wrapper formatting (leaf 03/01, dependency-visibility tree, 2026-09-06)

Contract F demanded a byte-verbatim failure message:

    skill <name> requires unavailable tool(s): <missing joined ", "> — run 'meept doctor' to diagnose

The executor's existing `ExecutorError.Error()` formats as
`skill "name": msg` — so naively putting the contract text into `Message`
produces `skill "web-browsing": requires unavailable tool(s): ...` which
does NOT match the contract, and the mismatch is invisible to the usual
review checks (`strings.Contains(err.Error(), "meept doctor")` passes).

## 1. The additive escape hatch: unexported `raw` field

```go
type ExecutorError struct {
    SkillName string
    Message   string
    // raw, when non-empty, is returned by Error() verbatim. Existing
    // call sites (Message-only) keep the legacy formatting.
    raw string
}

func (e *ExecutorError) Error() string {
    if e.raw != "" {
        return e.raw
    }
    return fmt.Sprintf("skill %q: %s", e.SkillName, e.Message)
}
```

Backward-compatible: every existing constructor leaves `raw` empty and
behaves identically. `SkillName` stays available for programmatic
matching. Cost: one field, one if-statement.

Alternative considered and rejected: changing `Error()`'s format
globally — it would alter every existing error string consumers may
match on.

## 2. Test shape: full-string equality, not Contains

The only test that catches this class of drift is equality on
`err.Error()`:

```go
want := "skill web-browsing requires unavailable tool(s): cua-driver.capture — run 'meept doctor' to diagnose"
if err.Error() != want { t.Fatalf("got %q want %q", err.Error(), want) }
```

Add this whenever a contract quotes an exact message. A Contains-based
test will stay green through wrapper-formatting changes that break the
contract.

## 3. Related drift found in the same leaf — contract file-lists

The contract said the field lives in `internal/context/skill_parser.go`,
but the `Skill` struct the field must surface on lives in
`internal/context/types.go` (same package). The orchestrator drift-audit
greps file:line claims, but struct-location claims need a different
grep: `grep -rn "type Skill struct" internal/` before trusting any "add
the field to X" instruction. Same failure shape as the discovery.go /
source_file.go drift — the fix is grepping by SYMBOL, not by file.

## 4. Named func types need plain-nil guards, not typed-nil-interface ritual

Contract said "typed-nil guard per AGENTS.md" for
`SetToolAvailability(fn ToolAvailabilityFunc)`. AGENTS.md's typed-nil
rule targets `*ConcreteType` stored in an interface — a func type has no
wrapper-pointer hazard, so the correct guard is simply:

```go
func (e *Executor) SetToolAvailability(fn ToolAvailabilityFunc) {
    if fn != nil { e.toolAvailability = fn }
}
```

Reading: apply the AGENTS.md guard INTENT (never store something that
panics on call), not its example MECHANICS. A `*T` in an interface →
typed-nil ritual; a func/nilable value → plain nil check.
