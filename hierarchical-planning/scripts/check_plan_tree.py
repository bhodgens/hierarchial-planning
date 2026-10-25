#!/usr/bin/env python3
"""
Structural completeness checker for hierarchical plan trees.

Validates:
1. Every orchestrator (master.md, orchestrator.md) has required sections
2. Every leaf document has required sections
3. No line-number corruption (e.g., "   42|code" baked into source)

Usage:
    python check_plan_tree.py <plan_root_dir>

Example:
    python check_plan_tree.py docs/plans/phase1-mvp/

Exit codes:
    0 = all checks passed
    1 = issues found (printed to stdout)
"""

import os
import re
import sys

REQUIRED_ORCHESTRATOR_SECTIONS = [
    "## Dispatch Protocol",
    "## Interface Contracts",
    "## Review Checklist",
    "## Coding Conventions",
    "## Completion Tracking Table",
    "## Integration Test Plan",
]

REQUIRED_LEAF_SECTIONS = [
    "## Meta",
    "## Goal",
    "## Tasks",
    "## Self-Verification Checklist",
]

# Matches line-number prefixes like "  42|code" that get baked into
# source files when agents copy from read_file output
LINE_CORRUPTION_RE = re.compile(r"^\s+\d+\|", re.MULTILINE)


def check_tree(root: str) -> list[str]:
    """Scan all .md files in the tree. Return list of issues (empty = pass)."""
    issues = []
    orchestrators = []
    leaves = []

    for dirpath, dirnames, filenames in os.walk(root):
        for fname in sorted(filenames):
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(dirpath, fname)
            is_orchestrator = fname in ("master.md", "orchestrator.md")

            with open(fpath, "r") as fh:
                content = fh.read()

            file_size = len(content)

            if is_orchestrator:
                orchestrators.append(fpath)
                for section in REQUIRED_ORCHESTRATOR_SECTIONS:
                    if section not in content:
                        issues.append(
                            f"MISSING in orchestrator {fname}: {section}"
                        )
            else:
                leaves.append(fpath)
                for section in REQUIRED_LEAF_SECTIONS:
                    if section not in content:
                        issues.append(
                            f"MISSING in leaf {fname}: {section}"
                        )

            # Check for line-number corruption
            corruption = LINE_CORRUPTION_RE.findall(content)
            if corruption:
                issues.append(
                    f"LINE-NUMBER CORRUPTION in {fname}: "
                    f"{len(corruption)} matches"
                )

    # Summary print
    print(f"Scanned: {len(orchestrators)} orchestrators, "
          f"{len(leaves)} leaves, "
          f"{len(orchestrators) + len(leaves)} total files\n")

    if issues:
        print(f"ISSUES FOUND ({len(issues)}):")
        for issue in issues:
            print(f"  X {issue}")
    else:
        print("All structural checks passed. No issues found.")

    return issues


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <plan_root_dir>")
        sys.exit(1)

    root = sys.argv[1]
    if not os.path.isdir(root):
        print(f"Error: {root} is not a directory")
        sys.exit(1)

    issues = check_tree(root)
    sys.exit(1 if issues else 0)
