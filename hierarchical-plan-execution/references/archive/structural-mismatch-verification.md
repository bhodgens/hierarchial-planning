# Sstructural mismatch verification
When to use: four structural mismatches in one forest.
Lesson: pre-dispatch verification worked example.

# Structural Mismatch Verification — Worked Example

## Session: meept claude-code-parity (2026-07-24)

Plan forest: 5 trees, 12 leaves. Four distinct structural mismatches caught
during pre-dispatch verification, zero subagent fix cycles from structural errors.

## The Four Mismatches

| Plan Claim | Actual Reality | Detection Method |
|---|---|---|
| Agent defs are JSON5 (`config/agents/*.json5`) | AGENT.md with YAML front matter (`config/agents/coder/AGENT.md`) | `search_files pattern="*" target="files" path="config/agents/"` returned 18 AGENT.md files, zero .json5 |
| `VerificationConfig` in `internal/agent/specs/` | No `specs/` package exists; AgentSpec is in `internal/agent/spec.go` | `search_files pattern="*.go" target="files" path="internal/agent/specs/"` returned 0 results |
| `PrepareNextTurn` returns `(*TurnModification, error)` | Returns `TurnModification` by value, no error | `search_files pattern="PrepareNextTurn" path="internal/agent/hooks.go"` showed actual signature |
| selfimprove uses Detect→Analyze→Generate→Validate→Apply | Uses RETRIEVE→JUDGE→DISTILL→CONSOLIDATE | `search_files pattern="LearningPipeline" path="internal/selfimprove/"` showed actual method names |

## Interface Census for Per-Tool Safety Leaf

The plan said "update all builtin tools." Pre-dispatch census found:

```bash
# Compile-time assertions:
grep -rn "var _ tools.Tool" --include="*.go" .
# Found: internal/tools/mcp/tool.go:206, internal/skills/skill_mcp_tool.go:22

# Method-set search:
grep -rn "func (.*) Name() string" --include="*.go" . | grep -v _test
# Found ~50 builtin tools + MCPTool + SkillMCPTool
```

The subagent updated all ~50 builtin tools correctly but missed MCPTool and
SkillMCPTool. Build broke with:
```
internal/tools/mcp/tool.go:206:20: *MCPTool does not implement tools.Tool (missing method IsConcurrencySafe)
internal/skills/skill_mcp_tool.go:22:20: *SkillMCPTool does not implement tools.Tool (missing method IsConcurrencySafe)
```

Fixed directly by orchestrator with 2-line patches (fail-closed defaults).

## Dispatch Context Corrections Applied

Every dispatch context that referenced a wrong assumption was corrected:

1. **Verification mode leaf:** told subagent agent defs are AGENT.md/YAML,
   VerificationConfig goes in `internal/agent/` not `internal/agent/specs/`
2. **Auto-trigger leaf:** told subagent PrepareNextTurn returns value type
   `TurnModification` (no pointer, no error), and gave exact TurnState fields
3. **Feedback leaf:** told subagent the pipeline uses
   RETRIEVE→JUDGE→DISTILL→CONSOLIDATE, gave actual `StorePattern` method
   signature, noted `UpdatedAt` is `*time.Time` (pointer)
4. **Per-tool safety leaf:** listed ALL implementing types including MCPTool
   and SkillMCPTool with explicit "add methods to these too" instruction
   (subagent still missed them — the census must be in the dispatch context
   as an explicit file list, not just a mention)

## Cost Comparison

- With structural verification: ~5 minutes of search_files calls, 0 fix cycles
- Without: 4 subagents producing code that doesn't compile against the actual
  interfaces, 4 fix cycles at ~10 minutes each = ~40 minutes wasted
