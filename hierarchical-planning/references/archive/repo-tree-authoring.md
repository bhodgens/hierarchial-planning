# Repo-Convention Tree Authoring (planning hygiene for index-tracked plan trees)


When to use: repos with an AGENTS.md + build-plan-index + plans-* convention.
Lesson: check tree numbering before naming the directory; index-tracked planning hygiene.
Learned authoring rebellion-the-game tree 30 (water/shores/swimming) after
tree 18's harbor-water leaf and a user feature request. For repos with an
AGENTS.md + build-plan-index + per-tree `plans-*/` convention.

## 1. Check tree numbering BEFORE naming the directory

Tree numbers are manually assigned rows in the build-plan index; the
sequence is not contiguous and gaps get backfilled. Grep the index for
`| <n> |` rows before creating `plans-godot/<n>-<slug>/`. Collision after
authoring = `mv` the dir + sed every leaf's `Parent:` header, the index
row, and the changelog row — all before committing (else grep-verified
cross-refs dangle).

## 2. Asset survey table in the master ("existing assets — do NOT re-research")

Most trees in a mature repo EXTEND existing systems. The master should
open with a table: asset path, current state, which leaf extends it. Two
payoffs: leaf agents start coding instead of re-reading the engine
directory, and "this already exists — extend, don't rewrite" becomes a
planning decision instead of a mid-implementation discovery. (Tree 30
reused a v1 water shader, swim mode, splash FX, follow plane, and Go tidal
bands; every leaf extends, none rewrites.)

## 3. Binding architecture decisions live in the MASTER, not in leaves

Cross-leaf contracts go in a numbered "Architecture decisions (binding for
all leaves)" section that leaves cite:

- Single-writer discipline (e.g. only the day/night cycle writes water
  level/ice/wave state; bodies subscribe).
- Render-contract locks (e.g. water stays OPAQUE per the SDFGI rule;
  shallow readability via depth tint + foam, never alpha) — plus any
  exemptions (decal layers above the body are exempt; the BODY isn't).
- "One shader with parameter sets, not shader permutations."
- No global sim where a local region suffices (dynamic water only ~24 m
  around the player; rest is pure shader).

Leaves independently reinventing these is the classic multi-agent drift
source.

## 4. Parallel-leaf file-collision warnings in the dependency block

State explicitly: "leaves 02/03/04 share no files — safe for concurrent
dispatch; 03/04 both touch X — merge order or surgical patch." The
dispatcher (or a future session) can't hold this from memory.

## 5. Spec-first leaf (00) for feature requests born from chat

When the requested feature's GDD/spec text doesn't exist yet, leaf 00
writes the spec — including the VERBATIM numbers implementers need
(tables: per-body wave/foam/tint, wade-tier speeds, ice freeze windows,
ripple ring lifetimes) — and every later leaf cites the sections it added.
Otherwise leaves implement against chat history their dispatched agents
never saw. In AGENTS.md-convention repos this also satisfies Rule 1
(changelog) and de-risks Rule 4 (drift) for the whole tree.

## 6. User visual gate as a BLOCKING leaf

When the requester is the visual gate (per-item verdicts, terse tuning
notes applied directly), the integration leaf enumerates the demo-cycle
items (e.g. 6 numbered look/feel checks + the F-key demo hooks that make
each inspectable on demand: pin-tide toggle, date jump, fly-to camera).
Tree status flips COMPLETE only on that verdict; failed verdicts go back
to the offending leaf in-session — fixes, not re-planning.

## 7. Known-cosmetic-gaps note in seasonal/variant leaves

A leaf that changes one season/state while other actors visibly interact
with it (rowboats sitting on a frozen river) gets an explicit "leave it,
note it in the leaf notes, do NOT fix here" line — this stops a dispatched
agent from scope-creeping into another tree's system mid-winter-leaf.
