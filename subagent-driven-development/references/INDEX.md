# Reference Index

One line per file: filename - when to use - one-line lesson. Full protocol: SKILL.md. Canon: ../hierarchical-planning/references/plan-tree-canon.md

- adversarial-test-infrastructure.md - subsystem too heavy to test directly - fixture + trace collector + deterministic evaluator (+ optional LLM adversary); catches Go JSON-tag bugs
- delegation-size-limits-and-splits.md - dispatch nears the time cap or spans two language trees - split into single-half parallel dispatches, schema pinned in both briefs; salvage timeouts
- docs-only-plan-tree-audit-pipeline.md - auditing a docs-only plan tree (no code) - 5 parallel audits, dependency-ordered fixes, SPLIT verifiers, all majors resolved
- download-assessment-methodology.md - batch-downloading assets past security scanners - assess tool behavior first; exact PIDs not pkill patterns; serial urllib fallback
- external-api-contract-verification.md - subagent writes an unverified external-API client - live-docs check pre-dispatch, live dry-run after; mocks mask production bugs
- go-project-conventions.md - Go monolith tasks (pgx/v5, River, chi) - embed UUID-as-TEXT, JSONB, River migration, Makefile, embed-guard conventions in dispatch contexts
- meept-cluster-implementation-status.md - resuming the meept distributed-cluster work - phase 1-4 components, files, and status snapshot for gap analysis
- multi-task-batches.md - several distinct user workstreams in one session - batch by file set, one writer per file, queue follow-ups onto running agents, guard protected literals and sourced tables
- orchestrator-fix-and-dispatch-contracts.md - orchestrator fix passes and shared naming contracts - count-asserted batch edits, serialize the contract-definer, single-command verify steps
- parallel-dispatch-git-discipline.md - parallel waves committing to one repo - compact briefs, explicit git add paths, index.lock retry, single-command verify steps
- parallel-fanout-partitioning.md - N agents concurrently on ONE repo - file partitioning, parent owns shared schema first, per-agent verify then one consolidated commit
- parallel-python-leaves-playbook.md - parallel leaves of a Python/uv plan tree - plan for partial work, fault-tolerant self-registration, never repo-wide ruff format, contract-drift checklist
- parallel-ui-reconciliation.md - parallel dispatch on one UI feature - blind selector mismatches are predictable; pin the markup/CSS contract or sequence the consumer later
- plan-forest-assessment.md - worked forest survey (14 pkgs, 12 trees) - tracking tables showed 12/12 PLANNED, code showed 10/12 complete; always ground in tests+git+filesystem
- post-subagent-review.md - after any subagent returns code - stat files, read the summary, spot-check conventions, run suites, fix, stage exact paths, one commit per leaf
- subagent-delegation-godot-features.md - delegating Godot/GUT feature leaves - inline the GDD spec text, one leaf per agent, expect timeout salvage and lint-nit cleanup
- subagent-dispatch-patterns.md - dispatching multiple independent plan-tree leaves - self-contained briefs, disjoint file sets even within a package, per-subagent review and commit, U1000 scan
- pre-dispatch-checks.md - before dispatching integration, port, or migration tasks - pre-read API surfaces, verify source paths, grep schema collisions, URLs from manifests only
- example-workflow-auth.md - first run of the loop or calibrating brief shapes - implementer/spec/quality prompt templates plus a full two-task worked trace
- concurrency-races-and-file-ownership.md - concurrent agents writing the same files - one writer per file; re-read after any sibling-modification warning; stale reads corrupt
- verify-subagent-self-reports.md - after EVERY code subagent returns - ls files, grep symbols, build and test yourself; a completion summary is a claim, not evidence
- timeout-and-rate-limit-recovery.md - dispatch timeout or 429 - salvage partials before re-dispatching; split on timeout, serialize on 429; two failed rounds means write it yourself
- dispatch-shape-catalog.md - deciding how many subagents, how big, how parallel - per-task for independent work, chains for sequential, waves for dependencies, worktrees for isolation
- domain-pitfalls-go-npm-sim.md - dispatching into Go, npm, or simulation code - JSON tags, committed-file deletion, count-guard tests, node_modules, ID-derived coordinates
- shared-repo-git-discipline.md - staging or committing in a repo others write to - explicit-path staging only; concurrent-writer detection; verify then disclose provenance
- plan-verification-and-resume.md - verifying a finished plan or resuming one - parallel review subagents read the actual code; tracking tables and surface greps lie
- steering-and-skill-integration.md - user says "continue" or asks which skill owns a sub-phase - assess done-vs-remaining and dispatch the next wave; route specialized phases to companion skills
