#!/usr/bin/env python3
"""verify_sizes.py - char budgets, pitfall registry format, diary-section ban.
RED against pre-refactor corpus; GREEN after leaves 02-04 land."""
import argparse, os, re, sys

ROOT = os.path.expanduser("~/.hermes/skills/software-development")

BUDGETS = {
    "hierarchical-planning/SKILL.md": 42000,
    "hierarchical-plan-execution/SKILL.md": 12000,
    "subagent-driven-development/SKILL.md": 25000,
    "writing-plans/SKILL.md": 15000,
    "hierarchical-plan-execution/references/INDEX.md": 8000,
    "hierarchical-planning/references/INDEX.md": 4000,
    "hierarchical-planning/templates/leaf-template.md": 5000,
    "hierarchical-planning/templates/master-template.md": 8000,
}

REGISTRY_FILES = [
    "hierarchical-planning/SKILL.md",
    "subagent-driven-development/SKILL.md",
]
REGISTRY_MAX = 500

failures = []

def fail(item):
    failures.append(item)
    print(f"FAIL {item}")

def check_budgets(root):
    for rel, cap in BUDGETS.items():
        p = os.path.join(root, rel)
        if not os.path.exists(p):
            fail(f"budget {rel}: missing")
            continue
        n = os.path.getsize(p)
        if n > cap:
            fail(f"budget {rel}: {n} > {cap}")

def check_registry(root):
    for rel in REGISTRY_FILES:
        p = os.path.join(root, rel)
        if not os.path.exists(p):
            fail(f"registry {rel}: missing")
            continue
        text = open(p, encoding="utf-8").read()
        m = re.search(r"^## Pitfall Registry\s*$", text, re.M)
        if not m:
            fail(f"registry {rel}: no '## Pitfall Registry' section")
            continue
        # section runs until next ## heading
        rest = text[m.end():]
        nxt = re.search(r"^## ", rest, re.M)
        section = rest[:nxt.start()] if nxt else rest
        # entries start with "N. **" at line start
        starts = [mm.start() for mm in re.finditer(r"^\d+\. \*\*", section, re.M)]
        if not starts:
            fail(f"registry {rel}: zero registry entries")
            continue
        bounds = starts + [len(section)]
        for i in range(len(starts)):
            entry = section[bounds[i]:bounds[i + 1]].strip()
            num = entry.split(".", 1)[0]
            if len(entry) > REGISTRY_MAX:
                fail(f"registry {rel}: entry #{num} {len(entry)} chars > {REGISTRY_MAX}")

def check_diary(root):
    checks = [
        ("hierarchical-planning/SKILL.md", "## Session Pitfall Additions"),
        ("hierarchical-plan-execution/SKILL.md", None),  # dated-heading count
        ("subagent-driven-development/SKILL.md", None),
    ]
    for rel, literal in checks:
        p = os.path.join(root, rel)
        if not os.path.exists(p):
            continue  # budget check already reported missing
        text = open(p, encoding="utf-8").read()
        if literal and literal in text:
            fail(f"diary {rel}: contains '{literal}'")
        dated = re.findall(r"^#{2,4} .*\((20\d\d-\d\d-\d\d)", text, re.M)
        if len(dated) >= 3:
            fail(f"diary {rel}: {len(dated)} dated sub-headings >= 3")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=ROOT)
    args = ap.parse_args()
    check_budgets(args.root)
    check_registry(args.root)
    check_diary(args.root)
    print(f"EXIT {len(failures)} failures")
    sys.exit(1 if failures else 0)

if __name__ == "__main__":
    main()
