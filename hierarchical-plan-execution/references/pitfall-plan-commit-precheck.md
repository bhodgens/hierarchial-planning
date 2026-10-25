# Pitfall: Pre-commit Unused Code Check Blocks Commit

## Symptom
Pre-commit hook blocks commit with:
```
⚠️ staticcheck U1000: unused code detected in staged packages
Commit blocked: remove unused code or suppress with //nolint:U1000
```

## Root Cause
When adding new code to existing files, the unused code analyzer runs on staged files and blocks if any function/variable is marked unused.

## Fix
Two approaches:
1. **Add nolint directive**: `func X() { //nolint:U1000 // reason }`
2. **Integrate into existing code**: Add new state constant to `AgentState.String()` switch, remove duplicate private method

## Lesson
Always run pre-commit checks BEFORE finalizing a plan implementation. The staticcheck U1000 check is aggressive and will block commits on unused code even if it's referenced indirectly.
