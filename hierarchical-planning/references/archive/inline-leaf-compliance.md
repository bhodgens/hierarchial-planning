# Inline Leaf Compliance Scanning


When to use: inline leaf definitions inside master.md files.
Lesson: scanner still requires a Child Index section; know what --strict-leaves checks.
## The Issue

When using inline leaves (leaf task definitions embedded inside `master.md` or `orchestrator.md` rather than as separate files), the compliance scanner `check_template_compliance.py --strict-leaves` still requires a `## Child Index` section in every orchestrator document.

Without `## Child Index`, the scanner reports:
```
01-infrastructure: MISSING required sections: ['## Child Index']
ALL TREES COMPLIANT: False
```

## The Fix

Add a `## Child Index` section to every orchestrator that uses inline leaves, even if the actual leaf content is in sections like `## Leaf Documents (Inline)` further down:

```markdown
## Child Index

| # | Document | Type | Dependencies | Est. Context | Concurrency |
|---|----------|------|-------------|-------------|-------------|
| 01 | (inline below) | leaf | none | 45-55K | A |
| 02 | (inline below) | leaf | 01 | 70K | B |

**Note:** All leaves are defined inline in this document (see "Leaf Documents" sections below).
```

## Why

The scanner walks every `master.md`/`orchestrator.md` looking for specific section headers. It doesn't understand that inline leaves exist under different headings. The `## Child Index` section is the canonical pointer the scanner uses to verify all children are accounted for.

## Verified

Session: 2026-08-04, humanplusone AI Employee Platform plan tree. Four orchestrators with inline leaves all failed the scan until `## Child Index` was added. After adding, all passed: `ALL TREES COMPLIANT: True`.
