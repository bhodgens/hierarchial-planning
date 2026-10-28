import os, re

refs = sorted(f for f in os.listdir('references') if f.endswith('.md') and f != 'INDEX.md')
idx = open('references/INDEX.md').read()
bullets = [l for l in idx.splitlines() if l.startswith('- ')]
print(f"refs on disk: {len(refs)}  INDEX bullets: {len(bullets)}")
listed = set()
problems = []
for i, b in enumerate(bullets, 1):
    if len(b) > 200:
        problems.append(f"INDEX line {i}: {len(b)} chars > 200")
    m = re.match(r'-\s+([\w.\-]+\.md)', b)
    if not m:
        problems.append(f"INDEX line {i}: no filename")
        continue
    fn = m.group(1)
    listed.add(fn)
    if not os.path.exists(os.path.join('references', fn)):
        problems.append(f"INDEX line {i}: {fn} missing on disk")
        continue
    head = "\n".join(open(os.path.join('references', fn)).read().splitlines()[:5])
    if "When to use:" not in head or "Lesson:" not in head:
        problems.append(f"{fn}: lacks C4 trigger header")
unlisted = set(refs) - listed
print("unlisted refs:", sorted(unlisted) if unlisted else "none")

sk = open('SKILL.md').read()
reg = sk.split('## Pitfall Registry')[1].split('## Maintenance')[0]
entries = re.findall(r'^\d+\. \*\*.*?(?=^\d+\. \*\*|\Z)', reg, re.S | re.M)
over = [(e.split('.')[0], len(e.strip())) for e in entries if len(e.strip()) > 500]
det = re.findall(r'DETAIL: (\S+)', reg)
missing = [d for d in det if not os.path.exists(d)]
print(f"registry entries: {len(entries)}, over-500: {over or 'none'}")
print(f"registry DETAIL targets: {len(det)}, missing: {missing or 'none'}")
print("problems:", problems if problems else "none")

dashes = 0
for root, _, files in os.walk('.'):
    for f in files:
        if f.endswith('.md'):
            p = os.path.join(root, f)
            for n, line in enumerate(open(p, encoding='utf-8'), 1):
                if '\u2013' in line or '\u2014' in line:
                    dashes += 1
                    print(f"  dash: {p}:{n}")
print("dash lines found:", dashes)
