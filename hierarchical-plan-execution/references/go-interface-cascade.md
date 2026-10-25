# Go Interface Extension Cascade — Worked Example

Pitfall 36 reference. When a plan leaf adds methods to a Go interface, the
actual file count is 3-5x the plan's estimate because implementors live in
packages the plan author never looked at.

## Session: meept claude-code-parity (2026-07-24)

### The plan's claim
Leaf 05-01 (per-tool-safety): "Add IsReadOnly and IsConcurrencySafe to
`tools.Tool` interface. Update all builtin tools (~15 files)."

### The reality
66 files changed across 5 packages. The subagent timed out at 600s/47 API calls.

### Implementor census (what the plan missed)

| Package | Types missed | Why invisible |
|---------|-------------|---------------|
| `internal/tools/mcp/` | `MCPTool` | Wrapper for external MCP servers; lives in a different package |
| `internal/skills/` | `SkillMCPTool` | Skill-embedded MCP wrapper; nobody thinks of skills as "tools" |
| `internal/agent/` | `noopLeaf`, `spawnLeaf`, `descriptorTool` | Test helpers + depth-gating wrappers in tool_registry.go |
| `internal/code/tools/` | 15 AST/LSP tool types | Entire sibling package of code-intelligence tools |
| `*_test.go` (3 files) | `mockTool`, `mockTerminatingTool`, `mockTerminatingLoopTool`, `fakeLeafTool`, `fakeSpawnTool` | Test mocks — invisible to `go build`, only break `go test` |

### The pre-dispatch scan that would have caught it

```bash
# 1. Compile-time interface assertions (production types)
grep -rn 'var _ tools.Tool' --include='*.go' . | grep -v '.git/'
# Found: 49 assertions across 4 packages

# 2. After subagent returns, catch test mocks
go test ./... 2>&1 | grep 'does not implement' | sort -u
# Found: 5 broken test mocks in 3 test files
```

### Recovery sequence (orchestrator, in-session)

1. `go build ./...` → 10 "does not implement" errors (production types)
2. Fixed `MCPTool`: 2-line fail-closed defaults (both return false)
3. Fixed `SkillMCPTool`: same 2-line pattern
4. Fixed `noopLeaf`, `spawnLeaf`, `descriptorTool` in tool_registry.go:
   - `noopLeaf` and `descriptorTool`: fail-closed defaults
   - `spawnLeaf`: delegates to wrapped `t.base.IsReadOnly(input)`
5. `go build ./...` → clean
6. `go test ./... 2>&1 | grep 'does not implement'` → 5 test mocks broken
7. Fixed all 5 test mocks with fail-closed defaults
8. `go test ./... -race` → all pass

Total recovery time: ~5 minutes of direct patching.

### Scope rule derived

If the implementor census shows 20+ types across 3+ packages, do NOT
dispatch as a single subagent leaf. Instead:
- **Wave 0 (orchestrator):** Define the interface methods + `ToolDefaults`
  embedded struct with fail-closed defaults. Commit.
- **Wave 1 (parallel subagents by package):**
  - Subagent A: `internal/tools/builtin/` (the ~50 builtin tools)
  - Subagent B: `internal/code/tools/` (15 AST/LSP tools)
  - Subagent C: `internal/tools/mcp/` + `internal/skills/` + `internal/agent/` wrappers
  - Subagent D: All `_test.go` mock types
- **Wave 2 (orchestrator):** `go build ./... && go test ./... -race` sweep.

### Key insight

The plan author counted files in `internal/tools/builtin/` and wrote "~15 files."
The actual implementor set spans every package that wraps, adapts, mocks, or
gates a tool. The `grep -rn 'var _ tools.Tool'` scan takes 2 seconds and
prevents a guaranteed 600s subagent timeout + 5 minutes of manual recovery.
