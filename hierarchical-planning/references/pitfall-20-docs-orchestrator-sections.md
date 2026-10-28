# Pitfall 20 - Docs Trees Ship with Incomplete Orchestrator Sections

When to use: authoring a plan tree for documents (GDD, specs, audits) rather than code.
Lesson: content focus makes you skip process sections; the structural compliance scan - not memory - catches the gaps.

When writing a plan tree for documents, you naturally focus on content: which doc needs what edit, what the new spec should say, what status marker to bump. This makes it very easy to skip the PROCESS sections in orchestrator documents: Dispatch Protocol, Interface Contracts, Review Checklist, Coding Conventions, and Integration Test Plan are the most commonly forgotten.

Worked evidence: in one doc-completion tree, a template compliance reviewer found 4 of 5 branch orchestrators missing the Dispatch Protocol, and all 5 were missing at least one required section. In a 12-tree forest, an execute_code grep scan caught 5 of 12 masters missing Dispatch Protocol and/or Coding Conventions before dispatch.

## Prevention: run the scan, never verify by memory

```
python3 ~/.hermes/skills/software-development/hierarchical-planning/scripts/check_template_compliance.py plans/feature-name --strict-leaves
```

The script walks every master.md/orchestrator.md (checking for `## Dispatch Protocol`, `## Interface Contracts`, `## Child Index`, `## Review Checklist`, `## Coding Conventions`, `## Completion Tracking Table`, `## Integration Test Plan`) and every leaf (checking for "Do NOT commit" and, with `--strict-leaves`, a Self-Verification checklist). Patch any gaps and re-run until `ALL TREES COMPLIANT: True`.

Exact heading strings are required - variants fail (Pitfalls 34, 36; `references/compliance-headings.md`).

A plan tree with content-only orchestrators forces the executing orchestrator agent to guess its own workflow, which wastes context and produces inconsistent results.
