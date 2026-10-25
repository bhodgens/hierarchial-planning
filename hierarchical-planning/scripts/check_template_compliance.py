#!/usr/bin/env python3
"""
Structural compliance scan for a hierarchical plan tree (or forest of trees).

Walks every master.md / orchestrator.md under the given root and verifies that
each orchestrator document contains the required template sections. Optionally
also checks that every leaf document (any .md that is not an orchestrator)
contains a "Do NOT commit" instruction and a "Self-Verification" checklist.

This is the deterministic scan referenced by SKILL.md Pitfall 20 and the
"Verify the Tree" step. Run it AFTER authoring the whole tree (or forest) and
BEFORE dispatching any implementation or review agents. Patch any missing
section, then re-run until clean.

Usage:
    python3 check_template_compliance.py <plans-root> [--strict-leaves]

Exit code:
    0 = all orchestrators compliant (and all leaves compliant if --strict-leaves)
    1 = one or more documents missing required sections (details printed)

The required orchestrator sections (checked case-insensitively):
    ## Dispatch Protocol
    ## Interface Contracts        (also matches "## Interface Contract")
    ## Child Index                (also matches "## Child Document Index")
    ## Review Checklist
    ## Coding Conventions
    ## Completion Tracking Table
    ## Integration Test Plan
    ## Test Gate                  (tests-first gate coverage matrix; docs-only
                                  and ops trees carry the heading with
                                  "N/A — <tree type>" + substitute verification)
    ## Open Questions             (recommended; not strictly required by the
                                  template but every good orchestrator has one)

If your tree legitimately omits a section (e.g. a trivially-small branch has
no Open Questions), the report still flags it so the omission is deliberate,
not accidental.
"""

import argparse
import os
import sys

REQUIRED_ORCHESTRATOR_SECTIONS = [
    "## Dispatch Protocol",
    "## Interface Contracts",
    "## Child Index",
    "## Review Checklist",
    "## Coding Conventions",
    "## Completion Tracking Table",
    "## Integration Test Plan",
    "## Test Gate",
]

RECOMMENDED_ORCHESTRATOR_SECTIONS = [
    "## Open Questions",
]

LEAF_REQUIRED_MARKERS = [
    "Do NOT commit",  # commit policy; every leaf must carry this
]


def is_orchestrator(filename: str) -> bool:
    return filename in ("master.md", "orchestrator.md")


def scan_tree(root: str, strict_leaves: bool) -> tuple:
    """Returns (all_ok, report_lines)."""
    report = []
    all_ok = True
    trees = sorted(
        d for d in os.listdir(root)
        # Skip hidden/dot directories (e.g. .claude, .git) — they are
        # tooling state, not plan trees. An ERROR on them is pure noise.
        # Also skip "archive" — archived/historical plans are deliberately
        # kept in their original (non-template) form and are not live trees.
        if not d.startswith(".")
        and d != "archive"
        and os.path.isdir(os.path.join(root, d))
    )
    if not trees:
        report.append(f"WARNING: no subdirectories found under {root}")
        report.append("  (Is this a plan-tree root? It should contain master.md plus")
        report.append("   one subdirectory per tree.)")
        # Fall through to check the root's own master.md below.

    # Check the forest root master.md if present
    root_master = os.path.join(root, "master.md")
    if os.path.exists(root_master):
        ok, lines = check_orchestrator(root_master, "(forest root)")
        if not ok:
            all_ok = False
        report.extend(lines)

    for tree in trees:
        tdir = os.path.join(root, tree)
        files = sorted(os.listdir(tdir))
        master = os.path.join(tdir, "master.md")
        if not os.path.exists(master):
            # Maybe orchestrator.md for a branch-only subdir
            master = os.path.join(tdir, "orchestrator.md")
        if not os.path.exists(master):
            report.append(f"{tree}: ERROR no master.md or orchestrator.md — files: {files}")
            all_ok = False
            continue
        ok, lines = check_orchestrator(master, tree)
        if not ok:
            all_ok = False
        report.extend(lines)

        # Leaf checks
        leaves = [f for f in files if f.endswith(".md") and not is_orchestrator(f)]
        for leaf in leaves:
            leaf_path = os.path.join(tdir, leaf)
            ok, lines = check_leaf(leaf_path, f"{tree}/{leaf}", strict=strict_leaves)
            if not ok:
                all_ok = False
            report.extend(lines)
    return all_ok, report


def check_orchestrator(path: str, label: str) -> tuple:
    with open(path) as f:
        content = f.read()
    lower = content.lower()
    missing = []
    for sec in REQUIRED_ORCHESTRATOR_SECTIONS:
        # Allow "Interface Contract" to match "Interface Contracts", and
        # "Child Index" to match "Child Document Index".
        key = sec.lower()
        if key == "## interface contracts":
            ok = "## interface contract" in lower
        elif key == "## child index":
            ok = "## child index" in lower or "## child document index" in lower
        else:
            ok = key in lower
        if not ok:
            missing.append(sec)
    missing_recommended = [s for s in RECOMMENDED_ORCHESTRATOR_SECTIONS if s.lower() not in lower]
    if missing:
        lines = [f"{label}: MISSING required sections: {missing}"]
    elif missing_recommended:
        lines = [f"{label}: OK (recommended but missing: {missing_recommended})"]
    else:
        lines = [f"{label}: OK"]
    return (not missing), lines


def check_leaf(path: str, label: str, strict: bool) -> tuple:
    with open(path) as f:
        content = f.read()
    lower = content.lower()
    missing = [m for m in LEAF_REQUIRED_MARKERS if m.lower() not in lower]
    if strict:
        if "self-verification" not in lower and "self verification" not in lower:
            missing.append("Self-Verification checklist")
    if missing:
        return False, [f"{label}: MISSING leaf markers: {missing}"]
    return True, [f"{label}: OK (leaf)"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", help="Path to the plans/ forest root (contains master.md + per-tree subdirs)")
    ap.add_argument("--strict-leaves", action="store_true",
                    help="Also verify every leaf has a Self-Verification checklist")
    args = ap.parse_args()

    if not os.path.isdir(args.root):
        print(f"ERROR: {args.root} is not a directory", file=sys.stderr)
        return 2

    all_ok, report = scan_tree(args.root, args.strict_leaves)
    print("\n".join(report))
    print()
    if all_ok:
        print(f"ALL TREES COMPLIANT: True")
        return 0
    else:
        print(f"ALL TREES COMPLIANT: False — patch the missing sections and re-run")
        return 1


if __name__ == "__main__":
    sys.exit(main())
