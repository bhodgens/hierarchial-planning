# Post-Authoring Audit Trio (parallel read-only subagents)


When to use: after authoring a tree/forest, before dispatching.
Lesson: parallel citation-drift, architecture-feasibility, and domain-ambiguity audits (tier 4).
Run after authoring a plan tree/forest, BEFORE dispatching implementation
agents. Complements the structural compliance scan (tier 1),
contract-verification digests (tier 2), and changelog-review digests
(tier 3): the trio audits the PLAN against the LIVE SOURCE TREE.

## Why — worked evidence (meept llm-resilience-forest, 2026-09-01)

Three parallel read-only subagents over a 26-doc forest surfaced 3
blockers, 5 risks, 4 nits, and 13 drifted citations — before any
implementation agent spent context on them:

- **Dead seam (blocker).** The plan's core mechanism — a verification
  hook returning a TurnModification that changes the next turn — existed
  in code AND tests, but the hook runner had ZERO production callers;
  the loop ran only other hook phases and never read the modification.
  Lesson: symbol-exists ≠ seam-fires. Audit prompts must demand "find
  the CALLERS of the entry point; if only tests call it, the plan is
  built on dead infrastructure."
- **Name collision (blocker).** Planned method
  `ResolveRef(ref) (string, error)` on a type that already had
  `ResolveRef(ref) *ModelConfig` — duplicate method, package would not
  compile. Freeze new method names only after grepping the receiver's
  existing method set.
- **Wrong state cardinality (blocker).** Endpoint cooldowns planned onto
  a per-alias health struct, but the feature's semantics (shared fate
  across two DIFFERENT aliases) require resolver-global state. Check
  whether state is per-X or singleton against the feature's SEMANTICS,
  not the convenience of an existing struct.
- **Risk taxonomy worth asking about every time:** one-shot vs
  persistent effects (an override cleared after first use vs a
  budget-length window); join keys too coarse (host-only key
  over-blocks distinct credentials sharing one host); missing provenance
  fields (jobs with no originating-session field make enqueue-time
  stamping dead-on-arrival); untyped payload blobs whose encoding a
  resume/serialization path needs declared up front; error classes that
  bypass the new classifier entirely (transport timeouts never reach
  HTTP status/body classification).

## The three audits (one parallel batch, all read-only)

1. **Citation-drift audit.** Input: every `file:line` anchor in the tree
   docs. The subagent re-locates each against current HEAD and returns
   ACCURATE / DRIFTED (old → new) / WRONG / STALE-CONCEPT (symbol
   renamed). Also verify count-claims ("five retry loops") by grep, and
   name-claims (field called X vs Y on struct vs catalog). Sibling
   sessions land commits mid-planning; a week-old citation is a guess.
   Corrections are mechanical: sed the anchors, re-run the scanner.
2. **Architecture audit.** Input: the tree docs plus the 6-8 mechanism
   assumptions the plans depend on. The subagent traces each in source
   and reports BLOCKERS (mechanism cannot work as designed) / RISKS
   (works but hazardous) / MINOR, each with file:line evidence and a
   one-sentence concrete fix. ALWAYS include these probes: "does the
   entry point have production callers?", "does the planned method/field
   name already exist on the receiver?", "can the planned state location
   deliver the feature's full scope?", "do the entities the plan
   stamps/reads actually carry the needed fields?", "any import cycles
   if package A starts importing B?"
3. **Domain-ambiguity audit** (only when planning hit a "which of two
   similar implementations is real?" question). One focused question.
   Worked case: a suspected "dual AGENT.md parser" resolved as
   parser + converter halves of ONE sanctioned pipeline — the fix was
   documenting the pattern and pinning ALL touch points, not picking a
   winner.

Digest every report in-session (orchestrator judgment, never delegated).
Apply amendments, record the audit in the forest as
`ARCH-AUDIT-<date>.md` with a disposition table (finding → which doc was
amended), and re-run the compliance scanner — amended docs must stay
compliant. Note: audit-record/sibling .md files at a flat tree root get
leaf-checked by the scanner (see meept-flat-plan-trees.md).

## Understanding-first brainstorm arc (feature-list sessions)

When the user hands a feature list and asks for implementation plans:

1. Recon the codebase per feature; classify each as implemented /
   partial / missing. Surface already-done items as verify-only work.
2. RESTATE understanding before authoring anything: per item, current
   behavior vs proposed behavior, with a worked end-to-end example for
   each contentious item. Ask the 4-6 scope questions that change
   designs (granularity, trigger thresholds, detection signals, failure
   semantics). The user WILL correct you — the corrections reshape tree
   boundaries.
3. Fold every correction into a forest-level `DECISIONS.md` (D# rows,
   source-attributed, dated; audit results get D# rows too). Leaves cite
   D#s. Do not author trees against uncorrected understanding — one
   session produced five material corrections (per-agent not
   per-employee; endpoint-level timeout granularity; all-turn park
   coverage; treat 402 like 429; keyword-bucketed quota detection).
4. Only then author the forest; finish with the audit trio above.
