# Plan-Tree Drift Digest — Worked Example

> Cross-reference of `docs/gdd/00-CHANGELOG.md` + 6 recent GDD commits
> (2026-07-19) against 74 tracked findings in `plans-glm/OPEN-QUESTIONS.md`.
> Captures the concrete shape of a drift digest so future agents can pattern-match.

## Context

- **Project:** rebellion-the-game (colonial-Boston immersive sim, UE5.8 + Go sidecar).
- **Plan trees:** `plans-glm/` (12 trees: 01-sandbox through 12-gamemaster), all DRAFT.
- **Tracker:** `plans-glm/OPEN-QUESTIONS.md` — 74 findings (40 original + 10 tech + 15 NPC + 9 gameplay), one blocker (Q-amend-1).
- **Plan dir is untracked** — `git status --short plans-glm/` shows `??`. Fell back to the tracker's compiled-date header ("Compiled 2026-07-19") and `master.md` "Last Updated" column.

## Source Batch (Step 1)

Read in one assistant turn:

- `docs/gdd/00-CHANGELOG.md` (full).
- `git log --oneline -30 -- docs/gdd/` (last 30 GDD commits).
- `git log --pretty=format:"%h %ai %s" -<N> -- docs/gdd/` for dated entries.
- `search_files "plans-glm/OPEN-QUESTIONS.md"` (locate tracker).
- `read_file` tracker (536 lines, paginated at 500).
- `read_file` `plans-glm/SHARED-CONVENTIONS.md` + `plans-glm/master.md`.

## Per-Commit Inventory (Step 2)

High-signal commits in the window:

| Hash | Signal | Notes |
|------|--------|-------|
| `856663f` | 7 new docs + 30+ DRAFT→DECIDED + 3 content sections | Final session; broad impact |
| `562d0f3` | Session 03 changelog append | 14 deferred items + 4 decisions |
| `eb8b580` | Adds `14-cpu-only-llm-path.md` to outline (O5) | Tree #06 source |
| `e5ab06e` | **D11: ratifies Boston hill heights via primary-source research** | Tree #10 terrain constants |
| `32b41be` | 14 deferred items + 4 open design decisions | Biggest single commit |
| `53be7fd` | Session 02 audit changelog | 18 fixes, 3 decisions |

For each: `git show <hash> --stat` to see touched files, then cross-reference
against each plan tree's "GDD Spec Source" column in `master.md`.

## Finding Classes (Steps 3 & 4)

### 🚫 Hard contradiction — Q-amend-10 (hill heights)

- **Plan value:** "Beacon 42m, Pemberton 24m, Mt Vernon 23m."
- **Current GDD value** (commit `e5ab06e`, D11, `05-history/10-boston-hills-elevations.md`):
  Beacon ~138 ft (~42 m), Fort Hill ~80 ft (~24 m), Pemberton ~110 ft (~34 m),
  Mt Vernon ~110–120 ft (~34–37 m), Copp's Hill ~50 ft (~15 m).
- **Drift:** Pemberton off by ~10 m; Mt Vernon off by ~14 m. The plan had
  misattributed Fort Hill's 24 m to Pemberton. Fort Hill itself was corrected
  in the GDD (was 40 ft, now 80 ft) — the plan never had the wrong value
  because it never listed Fort Hill.
- **Action:** amend `plans-glm/10-procgen/master.md` constants; flag Q-amend-10
  as superseded.

**Generalizable lesson:** commits titled "ratify X via primary-source research"
often *correct* values the plan tree recorded as confirmed. Always grep the
current doc; never trust the plan's stored constant.

### 🚫 False blocker-resolution — Q-amend-1 (need_states)

- **Tracker says:** Q-amend-1 is the only remaining BLOCKER (save schema
  uses `esteem/purpose/comfort`; schedule doc uses `WORK/FAITH/DUTY`).
- **Changelog says:** Session 03 commit `32b41be` "resolved D1: Tier-3
  population reconciliation".
- **Tempting conclusion:** D1 resolves Q-amend-1.
- **Actual:** D1 resolved the population tier model (MVP 75+20env / EA
  200+30env / Full 300+50env). The need_states contradiction is a *different*
  issue in adjacent docs. Verified by grep: `06-save-and-persistence.md:95`
  still has `esteem/purpose/comfort`; `07-npc-scheduling.md:42-49` still has
  `WORK/FAITH/DUTY`. Blocker stands.

**Generalizable lesson:** "related ≠ resolved." Read the cited source range
and confirm the specific contradiction is gone.

### ✅ Resolved — D-28/D-29/D-30 (distribution, fire, disease)

- D-28 (download-on-first-launch), D-29 (fire propagation CUT), D-30 (disease
  CUT). No plan tree references fire/disease as mechanics; D-28 affects
  trees #06 and #09 bundle/download logic. Quick triage: 2 of 3 require no
  action, 1 needs an amendment note.

### 📋 New info — D9 (Qwen2.5-3B Ep1) + D7 (tick budget)

- D9: Qwen2.5-3B ships at Ep1, not 1.2–1.5B. Tracker Q-amend-7 already
  matches; no amendment needed, but the tree can now cite a DECIDED value
  instead of a suggested default.
- D7: tick budget reconciled to "<5ms single-thread / <3ms goroutine-parallel
  / <10ms low-power 5Hz". `SHARED-CONVENTIONS.md` §6 has only the latter two.
  Minor drift — add the <5ms baseline.

### 📝 Status elevation — geo-foundation + navmesh

- `03-world/02-geographic-foundation.md`: [REVISED] → [DECIDED] (commit `e5ab06e`).
- `06-technical/09c-navmesh-strategy.md`: [DRAFT] → [DECIDED] (commit `32b41be`,
  expanded 65→~200 lines).

Trees #01, #07, #10 can now cite these as authoritative. The transition is
silent in the plan trees — surface it as a distinct report section so the
user knows which specs are safe to code against.

## Required-Amendments Summary (Step 5)

**Must-fix before dispatch:**
1. `plans-glm/10-procgen/master.md` — hill heights (Q-amend-10 superseded).
2. `plans-glm/10-procgen/master.md` — condition label "derelict" → "ruined" (D5).

**Should-update:**
3. `plans-glm/SHARED-CONVENTIONS.md` §6 — add <5ms single-thread baseline.
4. `plans-glm/11-embed/master.md` — reference `debug_http` build tag (D10).
5. `plans-glm/06-llm/master.md`, `09-save/master.md` — incorporate D-28.
6. Q-amend-34 — mark navmesh constants as sourced from DECIDED doc.

**No action:** D9 (Q-amend-7 matches), D-29/D-30 (out of scope), D13
(validates existing 12-tree structure), N2-N6 (out of scope).

**Still-open blocker:** Q-amend-1 (need_states contradiction). **Not fixed
by Session 03.** Flag for user.

## Report Shape Template

A drift digest report has this skeleton:

```
# GDD Changelog Cross-Reference Report — <plan-dir> Drift Digest

**Scope:** <changelog path> + <N> recent commits (<date range>)
**Cross-checked against:** <tracker path> (<count> findings), <conventions>, <master>
**Verdict:** <one-sentence summary of impact>

## 🚫 HARD CONTRADICTIONS — Plan trees currently hold wrong values
### H1. <topic> (<tree>, <finding-id>)
- **Plan value:** <X>
- **GDD change (commit <hash>, <D-number>):** <Y>
- **Impact:** <which trees, which leaves>
- **Action required:** <exact amendment>

### H2. ...

## ✅ RESOLVED OPEN QUESTIONS — Changelog closed these
### R1. <topic> (<decision-id>)
...

## 📋 NEW INFO — Changelog introduces content the plans should incorporate
### N1. <topic>
...

## 📝 STATUS CHANGES — GDD docs the plans depend on
<table>

## 🎯 Summary of Required Plan-Tree Amendments
1. Must-fix before dispatch
2. Should-update
3. No action
4. Still-open blockers

**Files NOT modified** (read-only digest). No commits made.
```

The final line is important — a drift digest is a *report*, not an edit pass.
Amendments happen in a follow-up after the user reviews.
