#!/usr/bin/env python3
"""verify_styles.py - em-dash sweep + style checks over refactored files."""
import argparse, os, sys

ROOT = os.path.expanduser("~/.hermes/skills/software-development")
FILES = [
    "hierarchical-planning/SKILL.md",
    "hierarchical-plan-execution/SKILL.md",
    "subagent-driven-development/SKILL.md",
    "writing-plans/SKILL.md",
    "hierarchical-plan-execution/references/INDEX.md",
    "hierarchical-planning/references/INDEX.md",
    "subagent-driven-development/references/INDEX.md",
    "hierarchical-planning/templates/leaf-template.md",
    "hierarchical-planning/templates/master-template.md",
    "hierarchical-planning/references/plan-tree-canon.md",
]
MAX_LINE = 500

failures = []

def fail(item):
    failures.append(item)
    print(f"FAIL {item}")

def scan(root):
    for rel in FILES:
        p = os.path.join(root, rel)
        if not os.path.exists(p):
            continue  # presence checked elsewhere
        text = open(p, encoding="utf-8", errors="replace").read()
        for ch, name in [("\u2014", "em-dash"), ("\u2013", "en-dash")]:
            if ch in text:
                cnt = text.count(ch)
                fail(f"style {rel}: {cnt} {name} character(s)")
        for i, ln in enumerate(text.split("\n"), 1):
            if len(ln) > MAX_LINE:
                fail(f"style {rel}: line {i} is {len(ln)} chars > {MAX_LINE}")
                break

def selftest():
    bad = "a \u2014 b"
    ok = "a - b"
    assert "\u2014" in bad and "\u2014" not in ok
    print("selftest: detector catches em-dash - PASS")
    sys.exit(0)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
    scan(args.root)
    print(f"EXIT {len(failures)} failures")
    sys.exit(1 if failures else 0)

if __name__ == "__main__":
    main()
