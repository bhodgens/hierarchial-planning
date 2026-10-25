# Leaf Review: Catching Missing Scope When Tests Pass

> Worked example for `hierarchical-plan-execution` Step 3c item 8 and
> Pitfall 21. A leaf returned with 125 passing tests, clean `go vet`,
> clean `-race`, zero stray artifacts — and was missing a core GDD algorithm
> the spec required. Documents the technique that caught it and the worksheet
> used.

## Session

- **Date:** 2026-07-19
- **Project:** rebellion-the-game sidecar (Go)
- **Plan tree:** `plans-glm/02-gossip/` (Gossip & Reputation engine)
- **Leaf reviewed:** 02-propagation (already marked COMPLETE in the tracking
  table — this was a post-hoc audit, not a pre-COMPLETE gate)
- **Source spec:** `docs/gdd/04-npc/04-gossip-and-reputation.md`

## What the standard review found

Every checklist item in Step 3c (1-7) passed:

| Check | Result |
|-------|--------|
| File existence (15 source + 4 test files present) | ✅ |
| Read changed files (fact.go, network.go, propagate.go, transfer.go, …) | ✅ structurally sound |
| Interface contracts (`Fact`, `NPCKnowledge`, `GossipNetwork`, `Config` all match master.md) | ✅ |
| Tests (`go test ./internal/gossip/... -short -race -v`) | ✅ 125 RUN / 125 PASS / 0 FAIL, 1.529s |
| Artifacts (`fmt.Println\|TODO\|FIXME\|PLACEHOLDER\|HACK` zero hits) | ✅ |
| Lint (`go vet` clean) | ✅ |
| Build (`go build ./internal/gossip/...`) | ✅ |

The tracking table said the leaf was COMPLETE at 100%. Every signal the
review was designed to capture said APPROVED.

## What the spec-section → impl-file mapping caught

### Step 1 — Inventory the spec's named artifacts

Reading the GDD sections this leaf's master.md cited as scope, list every
function, constant, and algorithm the spec names:

| Spec section | Named artifacts |
|--------------|-----------------|
| §Propagation Algorithm | `gossip_tick`, `process_gossip_pair`, `transfer_fact`, `determine_direction` |
| §Social Compatibility | `get_social_compatibility`, `GOSSIP_THRESHOLD=0.3` |
| §Shareable-Facts Filter | 6 filter rules (secret, intro, damaging, importance, relevance, hops) |
| §Fact Transfer | `ACCURACY_DECAY=0.15`, alignment-conflict ×0.8 |
| §Fact Decay, Merging, Deduplication | `decay_memory(npc, delta_time)`, `FACT_DECAY_BASE=0.01`, `PRUNE_THRESHOLD=0.15`, emotional-weight halving, importance scaling |
| §Importance, Lifespan, Range | `calculate_importance`, `calculate_max_hops`, `calculate_lifespan_days` |
| §Celebrity Multiplier | fact-count bands table (0-5 / 5-10 / 10-20 / 20+) |
| §Reputation Layer | `compute_player_reputation`, 5 dims (Trust/Danger/Political/Notoriety/Criminal) |

### Step 2 — Search the impl for each named artifact

```
search_files pattern="FACT_DECAY_BASE|PRUNE_THRESHOLD|decay_memory|DecayMemory"
            path="sidecar/internal/gossip"
→ total_count: 0
```

Zero hits. The entire §Fact Decay algorithm — the constants, the function,
the pruning behavior — is absent from the implementation.

### Step 3 — Verify the file that should contain it

```
read_file path="sidecar/internal/gossip/decay.go"
→ 29 lines total. Contains ONLY `reinforceLowConfidence`.
   No `FACT_DECAY_BASE`. No `PRUNE_THRESHOLD`. No importance-scaled decay.
   No prune-on-low-confidence removal.
```

The file name matches the spec (`decay.go`), but its contents cover ~10% of
what the spec's §Fact Decay requires.

## Why the standard checks missed it

- **Tests pass:** the implementer wrote no tests for `decay_memory` because
  they wrote no `decay_memory`. You cannot test what doesn't exist.
- **vet/build clean:** a missing function is not a compile error; nothing
  references it.
- **File exists:** `decay.go` exists, which satisfies checklist item 1.
  Its *contents* are a stub, but the standard review reads the file, sees
  valid Go, and moves on.
- **Tracking table said COMPLETE:** the prior session's reviewer trusted the
  implementer's "all tasks done" report and marked the leaf 100%.

## The technique in general form

After the standard review (items 1-7) passes cleanly, do one more pass:

1. **Re-read the leaf's scope statement** (the bullet list at the top of the
   leaf doc saying what it implements).
2. **For each scope bullet, name the spec artifact(s) it implies.** Write
   them down. "Fact decay" is not an artifact; `decay_memory` is.
3. **`search_files` the impl directory for each artifact name.** Zero hits
   for a spec-named function or constant = Critical finding.
4. **For spec sections without a named function** (e.g., "alignment-conflict
   bias ×0.8"), grep for the numeric constant or behavior. Zero hits =
   Critical finding.
5. **Do not accept "it's inlined elsewhere" without verification.** Open the
   file you think implements it and read the function.

## What this session's full review found beyond the standard checks

In addition to the missing `decay_memory` algorithm (Critical), the mapping
technique surfaced:

- **Missing benchmark** — the master.md review checklist required "per-tick
  budget under 2ms with 50 NPCs (benchmark)"; no `Benchmark*` function
  existed in the package. De-risk criterion #4 was unverifiable.
- **Contract drift** — `ComputeStanding` in the impl had an extra
  `scopeFilter func(NPCRef) bool` parameter vs the frozen signature in
  master.md's "Interface Contracts" section. Frozen contract changes require
  updating SHARED-CONVENTIONS.md §3 first; that hadn't happened.
- **Spec-mandated behavior not wired** — GDD §Celebrity Multiplier says the
  multiplier is "applied to a fact's MaxHops and Lifespan **at creation** if
  the subject is the player"; `CreateFact` never calls `ApplyCelebrity`.
- **gofmt failures** on two files the implementer claimed were clean
  (`options.go`, `propagate.go`) — would have been caught by running the
  plan's literal checklist command.

## Verdict

**NEEDS_FIXES** — not APPROVED. The standard review (items 1-7) would have
returned APPROVED. The spec-section → impl-file mapping is what surfaced
the missing-scope Critical. Without it, the leaf would have stayed marked
COMPLETE and the downstream reputation-aggregation consumer (Tree 09) would
have inherited a system where facts never lose confidence and never get
pruned at runtime.

## Worksheet template

Copy this into any leaf review where tests pass:

```
SPEC-SECTION → IMPL-FILE MAPPING
Leaf: <name>
Spec source: <path>

| Spec section | Named artifact(s) | Impl file / function | Status |
|--------------|-------------------|----------------------|--------|
| §X.Y | `func_name` | <file>:<func> | ✅ / ❌ MISSING |
| §X.Y | `CONST_NAME` | grep result | ✅ / ❌ MISSING |
| §X.Z | behavior (e.g. ×0.8) | <file>:<line> | ✅ / ❌ MISSING |

Searches run:
- `search_files pattern="<const1>|<const2>|<func>"` → N hits
- `search_files pattern="<behavior>"` → N hits

Critical (missing scope, blocks COMPLETE):
- ...

Important (contract drift, unrun plan checklist items):
- ...
```
