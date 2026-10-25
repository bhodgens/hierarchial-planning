# Building Leaf Dispatch Contexts (orchestrator side)

Proven on llm-resilience-forest tree 01 (2026-09-01): 4 leaves, 4 commits
(178cd2b3, 53e0dd48, c88cc545, a00b76a5), zero re-dispatch iterations,
all landed amid THREE concurrent sibling trees editing the same repo.

## 0. Dispatch prompt skeleton (what worked every time)

1. "READ THE LEAF DOC FIRST, in full: <path>" — the doc carries tasks/TDD
   steps; the context carries anchors and constraints, not a restate.
2. HARD RULES block: no commit/no git add; no read_file on existing source
   (search_files or terminal sed/grep); write once, never read back; exact
   file-ownership carve-out ("You OWN ONLY: ... Nothing else.").
3. VERIFIED SOURCE ANCHORS block (see §1).
4. "REPORT: ... Deviations section (required, even if 'none')" — forcing
   the Deviations section surfaces judgment calls instead of hiding them.
5. Verify-list the implementer must run and quote in the report, so the
   orchestrator's in-session review re-runs the same gates.

## 1. Verify every file:line anchor before dispatch

Plan docs cite line numbers from audit-time HEAD; they drift. Before
dispatching, grep/sed each cited anchor in the CURRENT tree and inline the
VERIFIED shape into the context (symbol + line + a few real surrounding
lines). Session example: master cited mergeSpec ~:836-848 and
definitionToSpec ~:906; actual was :838-848 and :895. Findable either way,
but inlining the verified shape got contract-exact implementations from
every leaf with zero review rejections.

Also inline the exact contract code (struct fields with tags, function
signatures, verbatim format strings that must be preserved byte-identical)
so the implementer cannot paraphrase a frozen contract.

## 2. Ownership carve-outs are mandatory when sibling trees are live

If another plan tree is running in the same worktree, the dispatch context
must say which shared files are FORBIDDEN even where the natural
implementation reaches: "tree 05 is ACTIVELY editing internal/llm/resolver.go
and internal/daemon/components.go — use surgical patch on unique anchors,
NEVER write_file those whole files, and do not touch any line not yours."
Leaf 04 landed append-only (+51/−0) on resolver.go despite heavy sibling
churn because the context demanded patch-on-anchor. Without the carve-out,
the leaf would have whole-file-rewritten over tree-05's work.

## 3. Authorize parent-side small-gap fix-ups (avoid full re-dispatch)

The review gate exists to catch contract drift; when the drift is
diff-sized, fix it in the parent directly instead of burning a re-dispatch
iteration. Session example: bus payload `from_model` empty vs contract,
`fix_loops` raw 0 vs effective floor, two `_ =` ignored-error sites
violating the repo convention — four small patches, done in minutes.
Record it honestly in the tracking table ("ORCHESTRATOR FIX-UPS", set
iterations=1) so the audit trail shows code the implementer did not write.
Re-dispatch is for structural/wrong-design failures, not 2-line gaps.

## 4. Tell implementers (and yourself) how the repo's gates behave

If pre-commit hooks build downstream importers, a sibling's mid-flight WIP
can block the ORCHESTRATOR's own commit (leaf 01: first commit attempt
failed on internal/daemon errors from tree-05; identical command succeeded
~1 min later once the sibling settled — the staged state survives the
failed hook). Response: read the hook output for whose files the errors
point at, confirm your staged set is clean, settle-and-retry. Never
--no-verify for this class.

## 5. Close-out docs can race the user's own commits

Check `git log` for a same-topic commit before committing tracking-table
close-outs. At this tree's close the user committed their own terse
tracking update (83c4822f) while the orchestrator was composing a detailed
one; the detailed patch applied cleanly on top (re-read after the
file-changed warning, re-anchor) and the richer row became the audit
record. Verify the leaf hashes in both rows agree.
