---
name: writing-plans
description: "Write implementation plans: bite-sized tasks, paths, code."
version: 1.1.0
author: Hermes Agent (adapted from obra/superpowers)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [planning, design, implementation, workflow, documentation]
    related_skills: [subagent-driven-development, hierarchical-planning]
---

# Writing Implementation Plans

> **ROUTING:** For any feature requiring multiple files, subsystems, or
> concurrent implementation, use the `hierarchical-planning` skill instead.
> It produces a tree of documents designed for multi-agent dispatch with
> automated review loops. Only write a flat single-file plan (this skill)
> for trivial single-component work.

## Overview


> Shared model and write-path policy: references/plan-tree-canon.md (C1-* sections). Read once; this skill assumes it.

Write comprehensive implementation plans assuming the implementer has zero context for the codebase and questionable taste. Document everything they need: which files to touch, complete code, testing commands, docs to check, how to verify. Give them bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

Assume the implementer is a skilled developer but knows almost nothing about the toolset or problem domain. Assume they don't know good test design very well.

**Core principle:** A good plan makes implementation obvious. If someone has to guess, the plan is incomplete.

## When to Use

**Always use before:**
- Implementing multi-step features
- Breaking down complex requirements
- Delegating to subagents via subagent-driven-development

**Escalate to hierarchical-planning when:**
- Feature scope exceeds what one agent can implement in 128K context
- Multiple subsystems can be built concurrently
- The work has natural architectural seams (modules, layers, packages)

In that case, use the `hierarchical-planning` skill instead - it produces a tree of plan documents where leaves fit one agent and orchestrators dispatch, review, and commit.

**Don't skip when:**
- Feature seems simple (assumptions cause bugs)
- You plan to implement it yourself (future you needs guidance)
- Working alone (documentation matters)

## Bite-Sized Task Granularity

**Each task = 2-5 minutes of focused work.**

Every step is one action:
- Write the failing test
- Run it to make sure it fails
- Implement the minimal code to make the test pass
- Run the tests and make sure they pass
- Commit

**Too big:**
```markdown
### Task 1: Build authentication system
[50 lines of code across 5 files]
```

**Right size:**
```markdown
### Task 1: Create User model with email field
[10 lines, 1 file]

### Task 2: Add password hash field to User
[8 lines, 1 file]

### Task 3: Create password hashing utility
[15 lines, 1 file]
```

## Plan Document Structure

### Header (Required)

Every plan MUST start with:

```markdown
# [Feature Name] Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

---
```

### Task Structure

Each task follows this format:

````markdown
### Task N: [Descriptive Name]

**Objective:** What this task accomplishes (one sentence)

**Files:**
- Create: `exact/path/to/new_file.py`
- Modify: `exact/path/to/existing.py:45-67` (line numbers if known)
- Test: `tests/path/to/test_file.py`

**Step 1: Write failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

**Step 2: Run test to verify failure**

Run: `pytest tests/path/test.py::test_specific_behavior -v`
Expected: FAIL - "function not defined"

**Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

**Step 4: Run test to verify pass**

Run: `pytest tests/path/test.py::test_specific_behavior -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

## Writing Process

### Step 1: Understand Requirements

Read and understand:
- Feature requirements
- Design documents or user description
- Acceptance criteria
- Constraints

### Step 2: Explore the Codebase

Use Hermes tools to understand the project:

```python
# Understand project structure
search_files("*.py", target="files", path="src/")

# Look at similar features
search_files("similar_pattern", path="src/", file_glob="*.py")

# Check existing tests
search_files("*.py", target="files", path="tests/")

# Read key files
read_file("src/app.py")
```

### Step 2b: Verify External API/Service Assumptions

When the plan integrates with named external services (third-party APIs,
job boards, payment gateways, data feeds), verify the API actually exists
in the form described BEFORE writing tasks around it. Users may name an
API from memory that has since changed, been deprecated, or never had the
shape they recall.

Check:
- Does the named vendor/product exist at all? A name recalled from memory can be
  wrong or conflated with a different product (real case: "Speedly" payment router -
  no such product; searches return Spreedly and speedy.io, both different product
  classes). Search the bare NAME before comparing alternatives, flag near-matches
  to the user as an Open Question, and never silently substitute a close-named
  product.
- Does the named endpoint/path exist? (`web_search` the provider's docs.)
- Is the auth scheme what the user said? (OAuth vs API key vs custom
  headers - e.g. USAJobs uses `Authorization-Key: <apikey>` + `User-Agent:
  <email>` + host `data.usajobs.gov`, which no amount of guessing from the
  name "USAJobs API" would reveal. The original plan assumed literal
  `Basic email:key` and shipped a fetcher+tests that passed against mock
  fixtures but would 401 against the real API.)
- Is the transport what they assumed? (Real example: a user asked for an
  "Arbeitnow GraphQL" integration; no public GraphQL API exists - the
  feed is a REST JSON endpoint. A plan written around a GraphQL query
  would have failed at implementation.)
- Is there a reference implementation in the source repo to port from?
  If the plan claims "ports logic from engine.py", `ls` the cited path.
- Is the external provider open-source? Clone the PINNED upstream at a
  fixed ref into a scratch dir and treat its source as field-level ground
  truth: grep its request/response structs, endpoint paths, and webhook
  event-type strings, citing file:line in the leaf. Live docs and pinned
  source can disagree (real case: docs showed `created_lt` query params;
  the pinned checkout's serde renames use dotted `created.gte` keys; also
  `payment_id` vs `id` field names) - the pinned source wins because it is
  what you deploy; record the delta as a named staging verification item.
  For webhook signatures, check for compatibility layers BEFORE writing
  verification code: some providers ship a Stripe-compatible signature
  format (`Stripe-Signature: t=,v1=`) alongside a native scheme, and
  reusing proven Stripe verification logic beats porting a new scheme.

When a discrepancy surfaces, do NOT silently "fix" the plan. Surface it
as an Open Question at the top of the plan doc and proceed with
your best-guess default so the user can override. Discovering a non-existent
endpoint mid-implementation is far more expensive than a one-line flag.

For whole-PROJECT feasibility (many unverified external sources, novel
methods, an unproven hypothesis), escalate to the research-gated tree
pattern in the `hierarchical-planning` skill
(`references/research-gated-plan-trees.md`): a Phase 0 research branch
gates all buildout behind a user decision, and kill criteria become
executable commands rather than prose.

### Step 3: Design Approach

Decide:
- Architecture pattern
- File organization
- Dependencies needed
- Testing strategy

#### Optional: Dual-Track Milestone Planning

When there's fundamental uncertainty about which subsystem is the
riskiest or which build order will prove viability fastest, present
**two competing tracks** in the plan instead of committing to one:

```
Track A (Conventional): Build the obvious thing first.
  - Assumption: the risk is in X subsystem
  - Phases: A1 -> A2 -> A3 (each independently testable)
  - Convergence point: both tracks meet at the same milestone

Track B (Risk-First): Build the weird/hard part first.
  - Assumption: the risk is actually in Y subsystem
  - Phases: B1 -> B2 -> B3 (prove the hard thing, then build the easy stuff)
  - Convergence point: same milestone as Track A

Either track hits the same vertical slice. The recommendation
should state which track is preferred and why, but keep both
alive until the uncertainty resolves.
```

Use this when:
- The project has a novel system with no proven precedent (e.g., an
  LLM-driven gossip simulation in a historical FPS)
- The two build orders have significantly different failure modes
  (Track A fails late, Track B fails early)
- Stakeholders disagree on what to build first

Document both tracks in the plan with:
- Phase-by-phase deliverables and verification criteria for each
- A schedule summary comparing weeks-to-vslice for both
- Clear statement of which is recommended and why
- Note that both converge on the same final deliverable

Example: In a social-simulation FPS, Track A builds movement and combat
first (prove the FPS feel), Track B builds the gossip engine first
(prove the social simulation). If the gossip engine doesn't work,
Track B produces a `go test` failure in week 4 vs a broken prototype
in month 6 under Track A.

### Step 4: Write Tasks

Create tasks in order:
1. Setup/infrastructure
2. Core functionality (TDD for each)
3. Edge cases
4. Integration
5. Cleanup/documentation

### Step 5: Add Complete Details

For each task, include:
- **Exact file paths** (not "the config file" but `src/config/settings.py`)
- **Complete code examples** (not "add validation" but the actual code)
- **Exact commands** with expected output
- **Verification steps** that prove the task works

### Step 6: Review the Plan

Check:
- [ ] Tasks are sequential and logical
- [ ] Each task is bite-sized (2-5 min)
- [ ] File paths are exact
- [ ] Code examples are complete (copy-pasteable)
- [ ] Commands are exact with expected output
- [ ] No missing context
- [ ] DRY, YAGNI, TDD principles applied

### Step 7: Save the Plan

```bash
mkdir -p docs/plans
# Save plan to docs/plans/YYYY-MM-DD-feature-name.md
git add docs/plans/
git commit -m "docs: add implementation plan for [feature]"
```

## Principles

### DRY (Don't Repeat Yourself)

**Bad:** Copy-paste validation in 3 places
**Good:** Extract validation function, use everywhere

### YAGNI (You Aren't Gonna Need It)

**Bad:** Add "flexibility" for future requirements
**Good:** Implement only what's needed now

```python
# Bad - YAGNI violation
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
        self.preferences = {}  # not needed

# Good - YAGNI
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
```

### TDD (Test-Driven Development)

Every task that produces code should include the full TDD cycle:
1. Write failing test
2. Run to verify failure
3. Write minimal code
4. Run to verify pass

See `test-driven-development` skill for details.

### Frequent Commits

Commit after every task:
```bash
git add [files]
git commit -m "type: description"
```

## Common Mistakes

### Vague Tasks

**Bad:** "Add authentication"
**Good:** "Create User model with email and password_hash fields"

### Incomplete Code

**Bad:** "Step 1: Add validation function"
**Good:** "Step 1: Add validation function" followed by the complete function code

### Missing Verification

**Bad:** "Step 3: Test it works"
**Good:** "Step 3: Run `pytest tests/test_auth.py -v`, expected: 3 passed"

### Missing File Paths

**Bad:** "Create the model file"
**Good:** "Create: `src/models/user.py`"

### Long-Output Degradation (authoring discipline)

A single write_file carrying ~20KB+ (a long plan with several full code listings) can
degrade mid-generation: duplicated section headers, mangled file references, self-referential
noise, broken code snippets. Observed twice in one session (a 25KB plan doc, then a long
delegate_task brief). The same failure mode applies to any very long single output.

- Embed complete code ONLY for small critical blocks (~100 lines or less per listing). For
  larger files, write a precise structural spec (ordered blocks, exact tokens, exact commands,
  expected outputs) instead of a full listing. "Complete code, copy-pasteable" applies
  per-block, not per-plan.
- If a write degrades, do NOT patch over the noise and do NOT keep appending. Rewrite the
  file wholesale in one compact pass, then verify with a content search for the mangled
  fragments until 0 matches before handing the plan to anyone.
- Keep delegation briefs compact (see Execution Handoff). A corrupted dispatch fails schema
  validation and dispatches nothing - re-dispatch clean with a shorter brief.

### Manual Steps for Pipeline/Ops Tasks

**Bad:** A pipeline plan with 20 manual curl/ssh steps - the agent must execute
each sequentially, error recovery is ad-hoc, and re-running from a mid-point
failure means re-reading the whole plan to find which step failed.

**Good:** A reusable idempotent script (`generate_images.py`, `repair_manifests.py`)
that reads state from a manifest/dataset, skips completed items, and can be
stopped and resumed. The plan's leaf produces the script; execution is one command.

When the user asks for an "LLM-executable plan" for a pipeline or ops task
(asset generation, data retrieval, batch processing), the deliverable is a
script - not a sequence of manual terminal commands. The script should:
- Track state (manifest.json, prompts.json) so it's idempotent
- Support `--dry-run` for preview
- Support `--path`/`--output-dir` for flexibility
- Report coverage (N done / N total) on completion

## Execution Handoff

After saving the plan, offer the execution approach:

**"Plan complete and saved. Ready to execute using subagent-driven-development - I'll dispatch a fresh subagent per task with two-stage review (spec compliance then code quality). Shall I proceed?"**

When executing, use the `subagent-driven-development` skill:
- Fresh `delegate_task` per task with full context
- Spec compliance review after each task
- Code quality review after spec passes
- Proceed only when both reviews approve

## Remember

```
Bite-sized tasks (2-5 min each)
Exact file paths
Complete code (copy-pasteable)
Exact commands with expected output
Verification steps
DRY, YAGNI, TDD
Frequent commits
```

**A good plan makes implementation obvious.**

> Maintenance: references/skill-maintenance.md.
