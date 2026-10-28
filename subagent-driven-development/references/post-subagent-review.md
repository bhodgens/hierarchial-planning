# Post-Subagent Review Checklist

When to use: after any subagent returns completed code, before committing.
Lesson: stat the files, read the summary, spot-check conventions, run the suites and lint, fix, then stage exact paths - one commit per leaf.

After a subagent returns completed code, run this checklist before committing.

## 1. Verify the Output

- **Stat the files**: confirm the subagent created all expected files (`git status --short` for untracked, `git diff --stat` for modified).
- **Read summary**: check the subagent's saved summary file at `~/.hermes/cache/delegation/subagent-summary-*.txt`.
- **Spot-check**: read key sections of the actual files, not just the summary. Confirm:
  - File headers follow conventions (copyright, source spec comment)
  - API contracts match the dispatch spec (function signatures, types, constants)
  - No unexpected changes to files the subagent shouldn't have touched

## 2. Run Tests (Go sidecar projects)

```bash
cd sidecar && go test ./... -short -race -count=1
```

- Check for non-zero exit codes, race conditions, panics
- For procgen: verify determinism tests pass (same seed → identical output)

## 3. Check Pre-commit Lint

The project's pre-commit hook runs 9 checks. The most common blocker:

- **U1000 (unused code)**: subagents often leave dead variables or unused functions. **Always remove the dead code**  -  never add `//nolint:U1000`. The hook correctly rejects nolint on unused vars.

Other checks run automatically on `git commit`. Look for:
- `mutexio`  -  I/O under a held mutex
- `gosec`  -  security vulnerabilities
- `predid`  -  time-based IDs
- `vet`  -  go vet failures

## 4. Verify UE5 C++ Code (No Engine Available)

Since UE5 engine is not available on the build machine, review by inspection:

- **Header contract**: does every UFUNCTION/UPROPERTY match the dispatch spec? Are all public methods present?
- **No stubs**: grep for `TODO`, `FIXME`, `PLACEHOLDER`, `// stub`. One-line stubs with logs are acceptable for deferred work; multi-line stubs with no logs are not.
- **Conventions**: Epic prefixes (A, U, F, E, I), UCLASS/UFUNCTION/UPROPERTY reflection, UE_LOG not printf, `#pragma once` not include guards
- **Build.cs**: if the module needs new dependencies (Sockets, Networking, Json), verify they were added

## 5. Fix and Commit

- Fix any issues found (patch the file, re-run tests)
- `git add <exact paths from the subagent>`
- `git commit` with message format: `feat(<scope>): <description> (plans-glm/<tree>/<leaf>)`
- A single commit per tree/leaf, not one giant batch
