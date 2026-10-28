#!/usr/bin/env python3
"""verify_index.py - INDEX.md one-line format, link integrity, ref trigger headers."""
import argparse, os, re, sys

ROOT = os.path.expanduser("~/.hermes/skills/software-development")
INDEXES = [
    "hierarchical-plan-execution/references/INDEX.md",
    "hierarchical-planning/references/INDEX.md",
]
MAX_LINE = 200

failures = []

def fail(item):
    failures.append(item)
    print(f"FAIL {item}")

def entries(text):
    """Yield (start_line_idx, entry_text) for each '- ' bullet, spanning
    continuation lines (indented or non-bullet non-blank) until next bullet/blank."""
    lines = text.split("\n")
    out = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("- "):
            start = i
            buf = [lines[i]]
            j = i + 1
            while j < len(lines) and lines[j].strip() and not lines[j].startswith("- "):
                buf.append(lines[j])
                j += 1
            out.append((start, "\n".join(buf)))
            i = j
        else:
            i += 1
    return out, lines

def check_index(root, rel):
    p = os.path.join(root, rel)
    if not os.path.exists(p):
        fail(f"index {rel}: missing")
        return
    text = open(p, encoding="utf-8").read()
    es, lines = entries(text)
    if not es:
        fail(f"index {rel}: no bullet entries")
        return
    multi = sum(1 for _, e in es if len(e.split("\n")) > 1)
    refs_dir = os.path.dirname(p)
    listed = []
    for ln, e in es:
        if len(e) > MAX_LINE:
            fail(f"index {rel}: entry at line {ln+1} is {len(e)} chars > {MAX_LINE}")
        m = re.match(r"-\s+([\w.\-]+\.md)", e)
        if not m:
            fail(f"index {rel}: entry at line {ln+1} does not start with a filename")
            continue
        fname = m.group(1)
        listed.append(fname)
        if not os.path.exists(os.path.join(refs_dir, fname)):
            fail(f"index {rel}: {fname} listed but missing on disk")
    # one-line-format compliance gates the header check (per leaf 00T)
    if multi == 0:
        # every listed md file must open with trigger header
        for fname in listed:
            fp = os.path.join(refs_dir, fname)
            if not os.path.exists(fp):
                continue
            head = "\n".join(open(fp, encoding="utf-8", errors="replace").read().split("\n")[:5])
            if "When to use:" not in head or "Lesson:" not in head:
                fail(f"index {rel}: {fname} lacks trigger header (When to use:/Lesson:)")
    else:
        print(f"NOTE index {rel}: {multi} multi-line entries; header check deferred")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=ROOT)
    args = ap.parse_args()
    for rel in INDEXES:
        check_index(args.root, rel)
    print(f"EXIT {len(failures)} failures")
    sys.exit(1 if failures else 0)

if __name__ == "__main__":
    main()
