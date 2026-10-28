"""One-shot: add C4 trigger headers to existing SDD reference files lacking them."""
import os

REFS = 'references'
HEADERS = {
    'adversarial-test-infrastructure.md': (
        'When to use: a subsystem is too heavy to test directly (init, event loop, external processes).',
        'Lesson: wrap it in a fixture + trace collector + deterministic evaluator; optionally add an LLM adversary loop for edge-case discovery.'),
    'delegation-size-limits-and-splits.md': (
        'When to use: a dispatch nears the delegation time cap or spans two language trees.',
        'Lesson: split into parallel single-half dispatches with the shared schema pinned in both briefs, and salvage timed-out partial work from disk before re-dispatching.'),
    'docs-only-plan-tree-audit-pipeline.md': (
        'When to use: a full audit-fix pass over a docs-only plan tree (no code exists).',
        'Lesson: 5 parallel audits, dependency-ordered fixes, then SPLIT verifiers separate fixing from judging.'),
    'download-assessment-methodology.md': (
        'When to use: batch-downloading assets where security scanners block naive fetch patterns.',
        'Lesson: assess scanner behavior first, use exact PIDs or service names instead of pkill patterns, and fall back to serial parent-side urllib.'),
    'external-api-contract-verification.md': (
        'When to use: a subagent writes a client for an external API nobody verified live this session.',
        'Lesson: verify the contract from live docs pre-dispatch, run a live dry-run smoke test after, and add contract checks to review - mock-server tests mask production bugs.'),
    'go-project-conventions.md': (
        'When to use: dispatching subagents into a Go monolith using pgx/v5, River queue, or chi.',
        'Lesson: embed UUID-as-TEXT, JSONB marshalling, River migration, Makefile backgrounding, and embed-guard conventions directly in the dispatch context.'),
    'meept-cluster-implementation-status.md': (
        'When to use: resuming or assessing the meept distributed-cluster plan tree.',
        'Lesson: a per-component file/status snapshot is the baseline for gap analysis before any new dispatch.'),
    'multi-task-batches.md': (
        'When to use: several distinct user workstreams run in one session via parallel subagents.',
        'Lesson: batch by file set with one writer per file, queue follow-ups instead of touching a running agent files, and guard protected literals and sourced tables.'),
    'orchestrator-fix-and-dispatch-contracts.md': (
        'When to use: orchestrator-side reconciliation after parallel builds, or tuning rounds from terse user feedback.',
        'Lesson: count-asserted batch edits, serialize the contract-definer before dependents, single-command verify steps, and explicit entrypoint-wiring ownership.'),
    'parallel-dispatch-git-discipline.md': (
        'When to use: parallel delegate_task waves committing to one shared repo.',
        'Lesson: compact briefs, explicit git add paths only, index.lock retry, and one simple verification command per check.'),
    'parallel-fanout-partitioning.md': (
        'When to use: N agents run concurrently on ONE repo.',
        'Lesson: file partitioning is the collision boundary - parent owns shared schema first, agents verify their own files, parent makes one consolidated commit.'),
    'parallel-python-leaves-playbook.md': (
        'When to use: executing parallel implementation leaves of a Python/uv plan tree.',
        'Lesson: plan for partial work on timeout, keep fault-tolerant module self-registration, never run repo-wide formatters, and run the cross-worker contract-drift checklist.'),
    'parallel-ui-reconciliation.md': (
        'When to use: parallel dispatch on one UI feature (HTML/CSS/JS split across siblings).',
        'Lesson: blind selector mismatches are predictable - pin the markup/CSS contract on disk or in both briefs, or sequence the consumer into a later wave.'),
    'plan-forest-assessment.md': (
        'When to use: a worked reference for cross-plan forest surveys.',
        'Lesson: tracking tables showed 12/12 PLANNED while code inspection showed 10/12 complete - ground every assessment in tests, git history, and the filesystem.'),
    'post-subagent-review.md': (
        'When to use: after any subagent returns completed code, before committing.',
        'Lesson: stat the files, read the summary, spot-check conventions, run the suites and lint, fix, then stage exact paths - one commit per leaf.'),
    'subagent-delegation-godot-features.md': (
        'When to use: delegating Godot/GUT feature leaves (geometry, shaders, scene wiring, tests).',
        'Lesson: inline the GDD spec text per leaf, expect timeout salvage, and treat lint nits as orchestrator-direct fixes.'),
    'subagent-dispatch-patterns.md': (
        'When to use: dispatching multiple independent plan-tree leaves as parallel subagents.',
        'Lesson: self-contained briefs (no read_file needed), disjoint file sets even within a package, per-subagent review and commit, and a U1000 dead-code scan.'),
}

for fname, (when, lesson) in HEADERS.items():
    p = os.path.join(REFS, fname)
    lines = open(p, encoding='utf-8').read().splitlines()
    joined = "\n".join(lines[:5])
    if 'When to use:' in joined:
        print(f"skip {fname} (already has header)")
        continue
    if lines and lines[0].startswith('# '):
        out = [lines[0], '', when, lesson] + lines[1:]
    else:
        out = [when, lesson, ''] + lines
    open(p, 'w', encoding='utf-8').write("\n".join(out) + "\n")
    print(f"headered {fname}")
