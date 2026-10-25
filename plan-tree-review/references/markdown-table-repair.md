# Repairing malformed markdown tables (build-plan-index, GDD, plan tracking)

The plan-tracking docs (build-plan-index.md, plans-godot/master.md completion
tables, orchestrator child tables) are hand-edited tables that corrupt over
time — usually by merging an entire row into another row or grafting the
wrong column count onto a row. A corrupted table still *renders* in most
viewers but mis-aligns columns and swallows cells. Proven 2026-08-15 fixing
build-plan-index.md (both the Implementation Plan Trees and the
Implementation Record tables). This is a STRUCTURAL repair — every row must
have the exact paper count of its table, and embedded bare `|` inside prose
cells are the enemy.

## Step 1 — establish the reference count per table

A markdown table row's `|` count = (number of cells) + 1. So:
- A 7-column table (e.g. `| # | System | GDD | Plan Tree | Status | Changelog | Notes |`) = **8 pipes/row**.
- A 6-column table (e.g. impl record `| Plan Tree | Impl Date | Agent | Last Check | Drift | Action |`) = **7 pipes/row**.

Don't eyeball the header — count it programmatically.

## Step 2 — scan every table row, flag outliers

Use a tiny Python script (execute_code) that walks the file, tracks which
"table" each `|`-starting line belongs to (header row = the one containing
the column titles), and reports every row whose `count("|")` differs from
its table's reference.

```python
from pathlib import Path
lines = Path("docs/gdd/09-pm/02-build-plan-index.md").read_text().splitlines()
# find the two headers
def header_for(l): return "System / Milestone" in l or "Implemented Date" in l
# then for each region print pipe counts, flag != reference
for idx, l in enumerate(lines, 1):
    if l.lstrip().startswith("|") and not header_for(l):
        n = l.count("|")
        # 8 for the 7-col plan table, 7 for the 6-col impl record
        expect = 8 if <is_in_plan_table> else 7
        if n != expect: print(f"L{idx}: pipes={n} :: {l[:70]}")
```

Two subtle cases that `count("|")` alone gets wrong:
- **Pipes inside backtick code spans** are harmless (they don't delimit
  cells). Before trusting a high count, distinguish bare vs code-span pipes:
```python
def bare_outside_code(row):
    in_code = False
    for ch in row:
        if ch == '`': in_code = not in_code
        elif ch == '|' and not in_code: yield
```
  In practice the plan docs have NO pipes inside code spans — every extra is
  bare. If your scan shows a high count and there ARE code-span pipes, only
  the bare ones matter.
- **A row with an EMPTY first cell** legally renders as a leading `||`
  (e.g. tree-01, which has no plan-tree number → `| | 01-sandbox ... |`).
  Don't "fix" a correct empty-first-cell row into a wrong one; the reference
  count already accounts for it.

## Step 3 — classify the failure modes

| Symptom | Pipes | Cause | Fix |
|---|---|---|---|
| Leading `||` or `|||` | +1/+2 over | A row got a stray leading pipe (often a copy-paste or an empty-cell row that lost its cell) | Normalize to one leading `|`. If it's a numbered row (`| 15 |`) use `| 15 |`; if truly numberless (`Phase 0`) use `| | 01-sandbox |` (empty first cell). |
| Embedded `\|` swapped into a prose cell | +1 | Two notes got merged with a bare pipe (`...shaders promoted). \| **2026-08-06 (leaf 06 done):** ...`) | Remove ONLY that bare pipe so the two notes live inside ONE Notes cell. This is the common "giant row is actually one row + a spliced sentence". |
| Wrong column count entirely | far off | A row was built for a DIFFERENT table (e.g. an Implementation-Record-shaped row living inside the Plan table, carrying Agent/date/drift columns it shouldn't) | Strip the columns that don't belong in this table; fold their info into the Notes cell with an `(Agent, date)` suffix. |
| Missing a cell | −1 | Legacy row predates the current column set (e.g. a 5-cell impl row standing in a 6-column table — no Action-Taken cell) | The tail sentence that reads like the missing column's content (`...recorded per Rule 4 ...`) IS the missing cell: insert a ` | ` before it. |
| Line got truncated to a bare `| X |` | way short | A prior over-greedy patch ate the tail | Re-read the original text (from context) and restore the full row. |

## Step 4 — splice with surgical single-context patches

Watch out: identical malformed rows CAN exist twice (a stray row duplicated
into both the Plan table and the Implementation Record, byte-identical). A
`patch(old_string)` will then error "Found 2 matches". Disambiguate by
including the ROW AFTER it as trailing context (the neighbor differs between
the two tables) — e.g. `...gossip conflict resolution |` then the malformed
row then `| 16 | Asset generation (GENERATED)` to pin the Plan-table copy.

## Step 5 — re-scan until clean, then sanity-read

Re-run the Step-2 scan; it must report 0 outliers on every table. Then read
the repaired header + a few rows to confirm each still carries its content
(the scan proves pipe counts, not that you didn't drop a cell's text).

## Guardrails

- **Whole-line replace is riskier than a targeted cell edit.** Replacing an
  entire giant row (like the 6500-char `18-godot-port` port row) risks a
  tool clip truncating the tail. Prefer `patch` on the small offending
  substring (the stray pipe, the leading `||`), not the whole line.
- **Never invent replacement content.** You may re-arrange cell membership
  (move a sentence into the missing cell) but must not author new prose.
  If you can't tell which cell text belongs in, leave the ambiguity and ask.
- **Verify with a fresh re-read after every patch** — a regex/script fix on
  markdown tables can silently eat a cell if the row is longer than the
  matcher expected.