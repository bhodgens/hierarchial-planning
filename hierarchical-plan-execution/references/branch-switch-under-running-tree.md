# Branch switched under a running plan tree (shared checkout)

## The shape (meept, transcript-large-corpus tree, 2026-09-06)

Mid-tree, `git commit` returned `[feat/tokscale-ingest 81753289]` when every
prior commit in the session was on `main`. A sibling session had run
`git checkout feat/tokscale-ingest` on the SHARED checkout between the
orchestrator's dispatches. Two more tree commits landed on the sibling's
branch before the drift was noticed.

## Protocol

1. **Read the branch name from commit output every time** (`[branch sha]`
   prefix). `git branch --show-current` at session start proves nothing
   about the branch ten minutes later.
2. **Do NOT switch branches back.** The checkout is shared; the sibling is
   actively working there. Switching to main stomps their in-flight editor
   state, staged files, and untracked work. A denial-risk git operation that
   helps you and breaks them is the wrong trade.
3. **Check ancestry before deciding.** If your commits are based on a commit
   that is an ancestor of main, they are portable (cherry-pick or
   fast-forward later, zero conflicts from your side).
4. **Keep working on the branch you find yourself on** for the rest of the
   tree — committing leaves 02/03/04 across two branches is worse than
   committing all of them on one non-main branch. Note the drift in the
   tracking table the moment it is discovered, and tell the user in the
   same turn.
5. **Reconcile at the integration gate**, not mid-tree: cherry-pick the
   tree's commits onto main (or fast-forward if main has not diverged past
   the branch point). Never rebase or reset the sibling's branch.
6. The integration gate's build+test runs must execute on the branch the
   commits actually landed on — run gates AFTER reconciliation.

## Why "just switch back" tempts

The orchestrator's commits "should" be on main. But on a shared checkout
the branch pointer belongs to whoever most recently claimed it; the
correctness target is "tree commits form one coherent, reconcilable
sequence", not "commits are on main right now".
