# Leaf 04 (coder gates) deep audit — 2026-08-30

Audited pristine worktree /tmp/meept-harness-audit @ 5d31b720 (leaf 04 landed
as 0e522625). Verdict: PARTIAL — core wiring verified end-to-end, one contract
omission + one test gap.

## Wiring chain (verified, evidence)
1. Parse: internal/agents/models.go:113 `Gate *GateMetadata` (yaml+json tags
   match C2); GateMetadata :118-136; default-true via UnmarshalYAML *bool
   tracking (:159-173) + NormalizeGateDefaults (:143-153).
2. Convert: internal/agent/registry.go:940-948 — NormalizeGateDefaults() then
   spec.Gate = &RosterGateConfig{...}; spec field at spec.go:118.
3. Construct: loop.go:1727-1728 — rosterGate = NewRosterGate(*loop.spec.Gate).
4. Call: ONE hook, loop.go:2317-2349 inside RunOnceWithParts (:1967) — the
   path used by dispatcher roster agents (dispatcher.go:1708) and chat
   handler (handler.go:794,1648). Spec-less/chat loops: rosterGate==nil no-op.
5. Engine: internal/gate/gate.go RunGate (:123) — extracted verbatim from
   internal/employee; employee re-exports via aliases (gate.go:28,38). No
   duplicate implementation. No os.Getwd in any gate path.

## Findings
1. MISSING (C2): 6 executors with `capabilities: code` lack the gate block:
   architect (has file_write+shell_execute — material), doc-keeper, explore,
   flaky-test-hunter, onboarding-tour, release-manager. Reviewers correctly
   ungated: 5 `*-reviewer` agents + verifier (role: reviewer).
2. GAP: no test exercises the hook inside RunOnceWithParts (loop.go:2324);
   roster_gate_test.go / roster_gate_e2e_test.go cover Evaluate mechanics only.
3. MINOR: shell_execute treated as unconditionally mutating (roster_gate.go:26)
   vs C2 "non-read" qualifier — over-triggers on read-only shell turns;
   documented in-code, fail-safe direction.
4. MINOR: default-true enforced only at parse layer — skipExplicit is set only
   by UnmarshalYAML; a JSON decode followed by Normalize would flip an explicit
   false→true. NewRosterGate copies cfg as-is (safe today: sole construction
   site normalizes at registry.go:942).
5. NOTE: internal/gate has zero test files; coverage lives in
   internal/employee/gate_test.go via the aliases — same code objects.
6. NOTE: learning/trajectory capture goroutines snapshot finalResponse and
   success (loop.go:2272-2312) BEFORE the gate mutates them (:2345) — failed
   gate turns are recorded as successful trajectories.
7. NOTE: dispatcher final fallback returns the registry singleton with no
   session context → empty workdir → gate silently skipped (loop.go:2329-2330).
   A coder dispatched without session binding is effectively ungated.

## Kill switch + workdir verification
- EmployeesGateConfig.Enabled zero-false; DefaultConfig() sets no Gate
  (schema.go:244-262) → employees.defaults.gate.enabled stays false. Roster
  path never consults it (TestGateConfigForGoal_KillSwitch).
- cwd resolution: handler.go:1682-1705 GetByConversationID → ProjectPath,
  WorktreePath override → GetOrCreateWired(conversationID, workingPath, ...);
  ConfigSnapshot (loop.go:5788) deliberately excludes workingDir (per-session,
  set by manager.go:77). No gate-specific conv-vs-session test (pre-existing
  mechanism, low risk).

## Test output (verbatim tail)
$ go test ./internal/gate/ ./internal/agents/ ./internal/employee/ -race -count=1
?   github.com/caimlas/meept/internal/gate [no test files]
ok  github.com/caimlas/meept/internal/agents 1.630s
ok  github.com/caimlas/meept/internal/employee 4.212s
$ go test ./internal/agent/ -race -count=1
ok  github.com/caimlas/meept/internal/agent 18.825s

## AGENT.md gate blocks (verbatim, both coder/AGENT.md:31-34 and debugger/AGENT.md:30-33)
gate:
  command: "go test ./..."
  timeout_seconds: 300
  skip_when_unchanged: true
