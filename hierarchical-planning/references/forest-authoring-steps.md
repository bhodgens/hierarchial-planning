# Forest Authoring Recipes - Steps 6.5-6.8 Detail

When to use: authoring a forest of 5+ plan trees, deciding inline-vs-separate leaves, naming forests, or resolving open questions with the user.
Lesson: forests share conventions through SHARED-CONVENTIONS.md siblings, default to inline leaves, name the forest's purpose, and bifurcate open questions into mechanical fixes and user decisions.

Detail home for SKILL.md Planning Process Steps 6.5-6.8. Worked examples: `references/multi-tree-forest-pattern.md` (12-tree forest), `references/open-questions-walkthrough.md` (Step 6.8 recipe).

## Step 6.5 - Authoring a forest (5+ trees)

Re-stating identical conventions, wire types, pitfalls, and commit policy in every master.md causes massive duplication and drift. Create a `SHARED-CONVENTIONS.md` sibling to the root master.md holding: project layout, language coding conventions, frozen IPC/wire types, the numeric/scale contract, test strategy, pitfalls list, commit policy. Every master.md and leaf REFERENCES it ("see SHARED-CONVENTIONS.md §3") rather than re-declaring its contents. Benefits: one source of truth for cross-tree contracts; a contract evolution edits ONE file; leaf dispatch contexts inline the relevant section rather than re-deriving conventions.

Also create a single `OPEN-QUESTIONS.md` sibling collecting every tree's open questions, sorted by tree, with a "summary: N questions, M needing decisions" footer - that is what the user reviews to amend plans before execution.

## Step 6.6 - Inline vs separate leaf files

- **Separate leaf files** when: the tree is the critical-path/de-risk milestone AND has 3+ leaves with complex inter-leaf dependencies. Full TDD task expansion is warranted because execution is imminent and leaves dispatch verbatim.
- **Inline leaf definitions in master.md** when: the tree has 2-3 moderate leaves (~60-90K each) AND task detail will be obvious once the orchestrator reads the spec at dispatch time. Each leaf gets a `## Leaf NN-name` section with scope, dependencies, estimated context, files-touched, interface contract, self-verification pointer, "Do NOT commit", and a one-line dispatch instruction. The executing orchestrator expands it into a full TDD task list AT DISPATCH TIME.

Inline is the default for forests; expand to separate files when execution of that specific tree is next. Scanner behavior for inline leaves: `references/inline-leaf-compliance.md`.

## Step 6.7 - Differential / convergence plan naming

A `plans-<label>/` directory signals a forest authored for a specific session or purpose: differential/convergence implementation (same leaf, multiple agents/models, outputs compared - freeze wire types, signatures, paths; state the purpose in the root master.md) vs session-specific doc completion (archived once done). If the user names a directory `plans-<something>/`, ask which purpose it serves before authoring - differential forests need tighter contracts.

## Step 6.8 - Resolving open questions with the user

- **Mechanical vs user-facing split.** Mechanical corrections (spec values the plan got wrong, confirmations where the spec is authoritative) - apply yourself in a batch and report. User decisions (genuine forks: scope cuts, format choices, separate-tree vs in-tree) - collect into a walkthrough.
- **Walkthrough format (10 or fewer per batch):** Q# (one-line title), Rec (recommendation - the user wants extrapolation, not just a question), Impact (what breaks the other way), Options (lettered a/b/c when alternatives exist beyond rec-vs-not).
- **Re-establish technical context before asking.** If a question asks the user to choose between technical artifacts (e.g. "GGUF vs ONNX"), give a 1-3 sentence orientation first: what it is, what it does in the system, why the format matters.
- **Terse answers may hide scope changes - confirm before executing.** A short answer to a framed blocker may be a deeper cut ("No hunger, thirst!" is not picking a source; it is removing 2 of 8 needs). Read the answer back ("I read this as cutting X and Y, giving result Z - confirm?") before editing multiple docs and trees.
- **Apply the changelog rule for any spec edits** the decision causes (see `design-plan-consistency` skill).
