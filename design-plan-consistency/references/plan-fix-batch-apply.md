# Plan Document Fix Batch-Apply Pattern

> Post-reconciliation fix application: after drift-digest verdicts are assigned,
> apply all content fixes in one tight read-patch-verify cycle.
> Rebellion GDD, 2026-07-19, 19 files changed across 2 plan directories + GDD.

## Context

After a drift digest or reconciliation audit identifies plan-tree content errors
(stale GDD references, wrong constant values, status mismatches, broken links),
the fixes need to be applied to the actual plan documents. The naive approach
(one patch per file, sequential) works but is slower and risks losing state
between edits. This pattern applies all fixes in a single tight cycle.

## The Batch-Apply Pattern

### Step 1: Batch read ALL target files first (one turn)

Read every file that needs editing BEFORE touching any of them. This prevents
stale-read-state problems (Pitfall 19 in hierarchical-planning: "orchestrator
patches a file a subagent already edited = stale read-state mismatch"). Since
you're the only agent editing here, the stale-read risk is low — but the
real benefit is **planning efficiency**: you see all the exact strings at once
and can construct every patch command without interleaving reads with writes.

```python
# One batch: 5 reads, all independent
read_file("08-schedule/master.md", limit=30)
read_file("11-embed/master.md", limit=100)
read_file("plans-glm/master.md", limit=10, offset=85)
read_file("SHARED-CONVENTIONS.md", offset=32, limit=40)
# ... etc
```

### Step 2: Fire all patches in parallel (one or two turns)

Use parallel `patch()` calls for independent files. Most fixes are on different
files, so they have no interaction risk. Batch groups of ~5-6 per turn.

```python
# Turn 1 — critical fixes (6 parallel patches on different files)
patch(path="08-schedule/master.md", old_string="8 needs...", new_string="6 needs...")
patch(path="11-embed/master.md", old_string="Q8_0 GGUF", new_string="ONNX format")
patch(path="plans-glm/master.md", old_string="06-semantic/", new_string="06-technical/")
# ... etc
```

Turn 2 handles the remaining priority items. Turn 3 handles any collateral
fixups (like the `replace_all` regression below).

### Step 3: Grep-verify each fix in a single sweep

After all patches are applied, run a single `execute_code` block that greps for
every old pattern and confirms zero hits:

```python
checks = [
    ("08-schedule: no '8 needs' prose", "grep -cE '8 needs' 08-schedule/master.md"),
    ("11-embed: no 'GGUF' remaining", "grep -c 'GGUF' 11-embed/master.md"),
    ("master.md: no '06-semantic/' broken link", "grep -c '06-semantic/' master.md"),
    ("SHARED: no '8-need scheduler'", "grep -c '8-need scheduler' SHARED-CONVENTIONS.md"),
    # ... etc
]
```

### Step 4: Fix regressions from aggressive replace_all

`replace_all=True` on a `patch()` call can over-patch when the old_string is
too generic. In this session, `DRAFT` → `PLANNED` with replace_all=True also
changed the status-values legend (`NOT_STARTED → DRAFT → PLANNED` became
`NOT_STARTED → PLANNED → PLANNED`). Catch this in the grep-verify sweep and
issue a targeted `patch()` to restore the correct value.

```python
# Detect: the status-legend line should say DRAFT but says PLANNED
grep("NOT_STARTED → PLANNED → PLANNED")
# Fix: restore the correct legend
patch(path="master.md", old_string="NOT_STARTED → PLANNED → PLANNED",
      new_string="NOT_STARTED → DRAFT → PLANNED")
```

### Step 5: Update changelog + audit documents last

After all file fixes are applied and verified, update the changelog with a
single entry describing the reconciliation. Then update any audit documents
that referenced the old state to reflect what was fixed and what remains.

## Worked Example: 19-file reconciliation in 4 turns

From this session's reconciliation pass (see `docs/gdd/00-CHANGELOG.md` Row 20):

| Turn | Action | Files touched |
|------|--------|---------------|
| 1 | Read all target files (batch) | 12 tree master.md files, SHARED-CONVENTIONS.md, GDD schedule doc, plans-ds4f orchestrators |
| 2 | Apply critical+high patches (parallel) | 11 files: tree #08 goal prose, tree #11 GGUF→ONNX (3 spots), master.md broken link + status header, 2 child table rows, tracking table rows, SHARED-CONVENTIONS line 36, 8-schedule line 24 |
| 3 | Apply remaining high patches + fix replace_all regression | 14 files: remaining 10 tree status headers (batched via execute_code), 4 plans-ds4f orchestrator Coding Conventions, GDD schedule doc 8→6, changelog entry |
| 4 | Grep-verify all fixes + write audit docs | 14-check verification sweep → all pass. Write 3 audit documents (629 lines total). |

## When to Use This Pattern

Use this when:
- A drift digest, reconciliation audit, or changelog cross-reference identified 5+ fixes across 3+ files
- The fixes are mechanical (find-and-replace, not creative writing)
- You've already read enough to know the exact old→new pairs
- You want to avoid the "patch, re-read, patch next file" sequential loop

Don't use when:
- Only 1-2 fixes needed (sequential is fine)
- Edits require creative judgment (content to add, not just replace)
- The same file is patched by multiple agents/subagents (serialize to avoid stale-read collisions)

## Pitfalls

1. **replace_all over-match.** Always verify the scope of a replace_all after
   application. A script that finds "8" and replaces with "6" will hit version
   numbers, byte counts, and unrelated references.

2. **Grep-verify expects zero — but zero means success.** A check like
   `grep -c 'GGUF'` returning 0 means zero occurrences = fix applied. But in a
   scripting language, `0` tests falsy. Explicitly check `output.strip() == "0"`
   when the intent is "zero matches = pass."

3. **Batch-parallel patches on the same file.** Two parallel patches on the same
   file can conflict. Only parallelize edits on different files. When a file needs
   multiple patches (e.g., tree #11 embed had 3 GGUF→ONNX spots), apply them
   sequentially or use execute_code for same-file batch work.

4. **Changelog table formatting.** When inserting a changelog row, table-pipe
   alignment (`|| date | scope |`) is easy to get wrong. Rows should start with
   exactly `|| ` (the markdown table requires leading pipe + space). The patch
   function can mangle this if the old_string omits the leading pipes. Always
   read the current last row and match its exact pipe-count.
