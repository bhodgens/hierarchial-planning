#!/usr/bin/env python3
"""verify_canon.py - canon file exists with frozen C1-* section IDs."""
import argparse, os, re, sys

ROOT = os.path.expanduser("~/.hermes/skills/software-development")
CANON = "hierarchical-planning/references/plan-tree-canon.md"
SECTIONS = ["C1-Nodes", "C1-Status", "C1-Commit", "C1-Dispatch",
            "C1-Review", "C1-Sizing", "C1-State", "C1-WritePath",
            "C1-Dialect", "C1-Trace"]
MAX_CANON = 6000

failures = []

def fail(item):
    failures.append(item)
    print(f"FAIL {item}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=ROOT)
    args = ap.parse_args()
    p = os.path.join(args.root, CANON)
    if not os.path.exists(p):
        fail(f"canon: missing at {CANON}")
        print(f"EXIT {len(failures)} failures")
        sys.exit(1)
    text = open(p, encoding="utf-8").read()
    for s in SECTIONS:
        if not re.search(rf"^## {re.escape(s)}\s*$", text, re.M):
            fail(f"canon: missing section '## {s}'")
    n = os.path.getsize(p)
    if n > MAX_CANON:
        fail(f"canon: {n} chars > {MAX_CANON}")
    print(f"EXIT {len(failures)} failures")
    sys.exit(1 if failures else 0)

if __name__ == "__main__":
    main()
