# Prose-Artifact Sweep — beyond the compliance scanner


When to use: tree passes the heading scanner but prose is broken.
Lesson: sweep for contradictions, dead references, and mass-authoring artifacts beyond headings.
Learned 2026-08-19, agent-orange tree (26 documents).

## The gap

`check_template_compliance.py --strict-leaves` checks required HEADINGS
only. A tree that mass-authoring produced in one session can pass the
scanner clean while still containing template-filling artifacts that
leak into dispatch contexts and confuse implementation agents.

## Observed artifacts (all passed the scanner)

- Headings: `## Goal**`, `## Goal}`, `### What This Leaf Consumes**`
- Self-noticing bracket notes left inline:
  `[Stray brace — Goal follows]`, `[Stray asterisks — Consumes follows]`,
  `[NOTE: ignore the stray brace ...]`
- Typo'd module names introduced during composition: `agent_ororge`
  (for `agent_orange`), `with_files` (for `search_files`)

## The sweep (run after scanner passes, BEFORE first commit)

```bash
grep -rnE '^## [A-Za-z ]+[}|*]|Stray brace|Stray backtick|Stray asterisks|ignore the stray' plans/<tree>/
```

Also grep for known project identifiers near the ones you typed from
memory (package names, module paths) — composition typos survive
review-by-eye.

## Fix rules

- Fix by hand or scripted per-file replace; verify each file after.
- Re-run the compliance scanner after fixes (a fix can break a heading).
- Use targeted patch replaces (mode=replace, full old_string) for
  multi-line artifacts — never regex-delete across files blind.
- For rows of near-identical artifacts across ~12 files, a single
  execute_code replace pass with per-path verification was ~4x faster
  than 12 manual patches; expect 2-3 misses on the first pass (escaping
  or whitespace variants) — the verification grep catches them.
