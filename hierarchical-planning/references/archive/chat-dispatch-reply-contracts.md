# Chat-Dispatch Reply Path — Contract Notes (meept)


When to use: agent-harness dispatch pipeline shaping user-visible replies.
Lesson: failure taxonomy and the fixed seams any future reply-path work must respect.
Distilled 2026-09-04 from the meept-vs-hermes comparison and the
chat-dispatch-ux tree. Class-level value: how an agent-harness dispatch
pipeline should shape its USER-VISIBLE replies, and the meept-specific
seams any future reply-path work must respect.

## The comparison bar (what "good" looked like)

Identical naive-user prompt + model (agnes-2.5-flash): hermes delivered a
working app in 4 turns; meept delivered nothing in 6. Every hermes turn
ended with what-was-done + how-to-run + one next step; meept's replies were
task-ID stubs, tool-catalog dumps, or the model apologizing for broken
tools. Full findings: /tmp/meept-vs-hermes-findings.md (session
2026-09-04), meept session session-6ef9cc62ebecffec.

## Failure taxonomy (each maps to a harness bug, not a model bug)

1. **Stub replies.** Sync dispatch polled the task store and returned
   `fmt.Sprintf("Task %s completed.", taskID)` — the step's real `Result`
   existed but never reached the chat reply. Fix: reply from
   bestStepResult(steps) with the stub only as empty-result fallback.
2. **Laundered failures.** ReviewManager's error-step skip returned
   ReviewApproved (feedback "Skipped review — step has execution error"),
   so errored tasks published task.completed. Worse: `AreAllCompleted` is
   success-only, so a terminal-with-failures task hung forever in an
   active state instead of finalizing. Fix: error gate ABOVE all policy
   paths (the old post-policy block was unreachable for no-review steps —
   red-phase verified), plus allStepsTerminalWithFailures.
3. **Wrong cwd.** Step jobs resolved relative paths against the daemon's
   CWD; a `chat --cwd /tmp/x` write landed in the meept repo. Fix:
   resolveStepWorkingDir falls back to the linked session's
   DetectionContext.CWD (WorktreePath > ProjectPath > CWD > ""; never
   os.Getwd). Anchor correction: session.go:56 is DetectionContext.CWD —
   Session has NO top-level CWD field (DetectionContext at :79).
4. **Context burn.** Task-scoped loops never inherited tool-schema mode;
   the coder shipped all ~75 full schemas and hit 49k/50k budget on a
   trivial task. Key mechanic: FilteredToolRegistry has NO SetSchemaMode —
   apply schema mode to the shared PARENT registry; filtered views
   delegate GetDefinitions to the parent, so parent-level stubbing covers
   every loop including cached ones.
5. **Machine-shaped replies.** Raw platform_status JSON, the "## Available
   Agents" roster (which leaked specialist system-prompt bodies), and
   tool catalogs became final replies. Fix: sanitizeCatalogReply at the
   RunOnceWithParts response-assembly site; prose passes byte-identical
   via a LINE-SHAPE ratio (>40% non-structural lines) — a char-ratio
   reading of "prose" fails its own tests because JSON is letter-dense
   and rosters embed prose sentences.
6. **Quota as self-harm.** A 429 escaping a specialist loop surfaced as
   "my tools aren't working" hallucination. Fix: classify
   *llm.QuotaResetError in AgentJobProcessor.Process, publish the EXISTING
   agent.quota_wait topic, append a user sentence to the returned error —
   the tactical failure path stores that error verbatim as the step
   Result, so the reply path (1) quotes it. Deliberate hyphenation
   "rate-limited" avoids llm.IsRateLimitErrorMessage patterns so the
   string-based tactical retry gate cannot re-queue quota'd jobs.
7. **Quota parked = nil response.** chatWithFailover returns (nil, nil)
   after a successful park; EVERY call site needs the nil-check or the
   caller reports failure AND the parker later re-runs the turn (double
   execution). (Sibling bughunt H1; noted here because it is reply-path
   adjacent.)

## Durable seams for future work here

- Reply path: RunOnceWithParts assembles finalResponse → applyReplyGuard
  → security scan → persist → notify → return. Anything user-visible must
  be shaped before persist.
- Step Result → chat reply: OnJobFailed/OnJobCompleted store the returned
  error/summary verbatim in step.Result; sync replies quote it. Fix the
  producer's message, not the reply formatter.
- config gate: AgentRegistry (all specialist agents) only constructs under
  cfg.MultiAgent.Enabled — a scratch/test config missing it yields
  `no agent available for "chat"` on every turn.
- Session store List(): ORDER BY archived ASC, last_activity DESC —
  "find by name" selectors must take the LAST match (most recent).
- Skill frontmatter: internal/skills stringList accepts YAML lists AND
  comma-separated scalars (Claude-format `allowed-tools: A, B`); MCPServers
  stays strict; StopWordSet() is the single stopword source (do not fork).
