# Plan Forest Assessment  -  Worked Example

When to use: a worked reference for cross-plan forest surveys.
Lesson: tracking tables showed 12/12 PLANNED while code inspection showed 10/12 complete - ground every assessment in tests, git history, and the filesystem.

> Rebellion game project: 14 Go packages, 12 plan trees, 3 parallel dispatches.
> This session demonstrated the Cross-Plan State Assessment pattern documented
> in the subagent-driven-development skill's "Cross-Plan State Assessment (Forest Surveys)" section.

## Context

Project: rebellion-the-game (UE5 immersive sim, Go sidecar NPC simulation)
Plan trees: 12 under `plans-glm/`, tracked in `docs/gdd/09-pm/02-build-plan-index.md`
Go sidecar: 14 packages under `sidecar/internal/`
UE5 project: `unreal/Rebellion/` with C++ files under `Source/Rebellion/`

## Step 1  -  Survey the plan forest (from the build-plan-index)

Read the build plan index and all 12 `plans-glm/*/master.md` tracking tables:
- All 12 trees showed status PLANNED
- Tree 01 (sandbox) showed IN_PROGRESS with leaves 04-05 PENDING
- Trees 02-12 showed PLANNED with PENDING leaves
- Implementation Record showed trees 02-12 "re-verified 2026-07-20, no drift"

## Step 2  -  Ground-truth code state

Three signals used in parallel:

**Signal A  -  Test status:**
```
go test ./... -short -race -count=1 2>&1 | tail -15
```
Result: ALL 14 packages passed. 211+ tests green.

**Signal B  -  Git history (96 commits total):**
```
git log --oneline --all
```
Key findings from commit messages:
- `feat(gamemaster): implement gamemaster agent (tree #12)  -  ALL 12 GO TREES COMPLETE`
- `feat(save): implement save/load persistence (tree #09)`
- `feat(procgen): implement Stages 0-4 (tree #10 leaf 01)`
- `feat(dialogue): implement dialogue pipeline (tree #05)`
- `feat(schedule): implement NPC scheduling (tree #08)`
- `feat(perception): implement vision/hearing/attention/stranger/recognition (tree #07)`
- `feat(llm): implement LLM bridge with dual-model routing + CPU cascade (tree #06)`
- `feat(identity): implement deterministic NPC identity generation (tree #04)`
- `feat(ipc): implement Go side IPC protocol + simulation tick loop + cmd/sim`
- `feat(embed): implement embedding model + vector index (trees #11 leaf 01+02)`
- `feat(testharness): implement adversarial gossip harness (trees #13)`
- Plus iterative fix commits for gossip, testharness, sandbox

**Signal C  -  Filesystem:**
```
ls -d sidecar/internal/*/
```
14 directories: alignment, api, dialogue, embed, gamemaster, gossip, identity, llmbridge, perception, procgen, save, schedule, testharness, world

```
find unreal/Rebellion/Source -name "*.h" -o -name "*.cpp" | sort
```
16 C++ files: PlayerCharacter, RebellionCharacterMovementComponent, RebelionMovementMode, IInteractable, SandboxGameMode, CoverIdentityData, SandboxFlowState, FarmerNPCController, CoverIdentityMenuWidget, Rebellion module + editor module.

Plus compiled binaries (dylibs) in `Binaries/Mac/` and content assets (Blueprints, Input Mapping, Sandbox.umap) in `Content/`.

## Step 3  -  Cross-reference table

| Tree | Plan Status | Go Pkgs | Test Pass | Git Evidence | Real Status |
|------|-------------|---------|-----------|--------------|-------------|
| 02-gossip | PLANNED | gossip/ | YES | feat(gossip) + 4 fix commits | COMPLETE |
| 03-ipc (Go) | PLANNED | ipc.go, api/ | YES | feat(ipc): Go IPC | COMPLETE |
| 03-ipc (UE5) | PLANNED | No SidecarClient files | N/A | No commit | NOT DONE |
| 04-identity | PLANNED | identity/ | YES | feat(identity) | COMPLETE |
| 05-dialogue | PLANNED | dialogue/ | YES | feat(dialogue) | COMPLETE |
| 06-llm | PLANNED | llmbridge/ | YES | feat(llm) | COMPLETE |
| 07-perception | PLANNED | perception/ | YES | feat(perception) | COMPLETE |
| 08-schedule | PLANNED | schedule/ | YES | feat(schedule) | COMPLETE |
| 09-save | PLANNED | save/ | YES | feat(save) | COMPLETE |
| 10-procgen | PLANNED | procgen/ (4 files) | YES | feat(procgen) stages 0-4 | PARTIAL (stages 5-13 missing) |
| 11-embed | PLANNED | embed/ | YES | feat(embed) | COMPLETE |
| 12-gamemaster | PLANNED | gamemaster/ | YES | feat(gamemaster)  -  "ALL 12 GO TREES COMPLETE" | COMPLETE |
| 13-adversarial | (not in index) | testharness/adversarial/ | YES | feat(testharness): 3 leaves | COMPLETE |
| 01-sandbox (Go) | IN_PROGRESS | sim tick wired | YES | docs(changelog): sandbox wave 1 | COMPLETE |
| 01-sandbox (UE5) | IN_PROGRESS | 16 C++ files, Blueprints, Map | N/A | C++ files exist, dylibs compiled | PARTIAL (leaves 04-05 missing) |
| Sim phases 6-9 | (not tracked) | stubbed in simulation.go | N/A | "phases 6-9 are no-ops" | STUBBED |

## Step 4  -  Real gaps identified

Only 3 trees had genuine remaining work:

1. **Tree #03 leaf 02**  -  UE5-side IPC (FSidecarClient + USidecarSubsystem). The Go side IPC is complete; the UE5 half that connects to it in PIE does not exist. Blocks sandbox integration testing.

2. **Tree #01 leaf 04**  -  Portal items (M_ModernItem with stencil, M_PortalShimmer, Niagara NS_PortalShimmer, PortalItemSpawner C++). The anachronism visual treatment spec is complete; the C++ implementation does not exist.

3. **Tree #10 leaf 02**  -  Procgen stages 5-7 (building generation, interior generation, furniture placement). Only stages 0-4 exist; stages 5-13 are all unimplemented. Stages 5-7 are the largest contiguous gap.

Plus low-priority gaps:
4. **Tree #01 leaf 05**  -  TTS playback (PiperPlaybackComponent)
5. **Memory package**  -  sim phase 6 currently a no-op
6. **Economy package**  -  sim phase 8 currently a no-op
7. **Procgen stages 8-13**  -  vegetation, NPC spawn, lighting, audio, timeline

## Step 5  -  Dependency-wave analysis

The build plan index's Phase 0 (sandbox) was the joint Track A+B deliverable. The sandbox master.md's dispatch protocol said "do NOT dispatch until trees #2,3,4,5,7,9 are COMPLETE." Since all those were actually COMPLETE (despite the tracking tables), the remaining gaps were:

```
Round 1 (independent, dispatch immediately):
  - Tree #03 leaf 02  -  UE5 IPC (5 C++ files)  -  blocks sandbox PIE
  - Tree #01 leaf 04  -  Portal items (2-3 C++ files)  -  standalone content
  - Tree #10 leaf 02  -  Procgen stages 5-7 (3-4 Go files)  -  independent Go work

Round 2 (after R1 review):
  - Tree #01 leaf 05  -  TTS playback
  - Tree #10 leaf 03  -  Procgen stages 8-10
  - Memory package + sim phase 6

Round 3:
  - Economy package + sim phase 8
  - Tree #10 leaf 04  -  Procgen stages 11-13
  - Sim phase 9 (quest check)
```

## Step 6  -  Context composition for dispatch

For each of the 3 parallel Round 1 dispatches, context was composed from:

| Source | Purpose |
|--------|---------|
| Plan leaf spec (from master.md) | Exact interface contracts, file paths, architectural intent |
| GDD design document | The authoritative spec (procgen stages, anachronism treatment) |
| Existing source code patterns | Coding conventions from SHARED-CONVENTIONS.md, existing function signatures, Build.cs |
| Transport/layer conventions | IPC wire types, NDJSON framing, port numbers |

The dispatch context for each subagent was 1500-2500 words with the exact code snippets inlined  -  no `read_file` required.
