# Orchestrator fix passes and dispatch contracts

Condensed from a real run: a static marketing site built by four parallel subagents, followed by two orchestrator-side reconciliation/tuning rounds driven by terse numbered user feedback. This file is also the fallback home for lessons that exceed the 100K SKILL.md cap or belong to protected skills.

## 1. Count-asserted batch edit pattern

Why: hand-sequenced patch calls fail on ambiguous anchors (duplicate strings elsewhere in the file) and on hunks whose old-string assumes an earlier hunk already applied. One scripted pass with exact expected counts either applies everything or writes nothing.

Template (run via execute_code):

```python
def edit(path, reps, append=None):
    s = open(path).read()
    errs = []
    for old, new, exp in reps:
        n = s.count(old)
        if n != exp:
            errs.append(f"count {n} != {exp} for {old[:60]!r}")
        else:
            s = s.replace(old, new)
    if errs:
        print("ABORT", path); [print(" ", e) for e in errs]; return None
    if append: s += append
    open(path, "w").write(s)
    return s
```

Rules:
- `exp` is the EXACT expected occurrence count. Use 1 almost always; higher only for deliberate replace-all with a known count.
- Assert all counts against the ORIGINAL text, then replace. Never include a hunk whose old-string only exists after an earlier hunk applied - split those into a second pass.
- Substring anchoring: when removing an element that also appears elsewhere (e.g. a footer `<img class="logo">` identical to the header's), anchor on surrounding unique context, not the tag alone.
- After writing, re-verify: brace balance for CSS, `node --check` for JS, grep for leftover old selectors/strings.
- Commit per logical pass; put the user-visible changes in the commit message.

## 2. Parallel dispatch across a shared naming contract

Failure seen: the CSS subagent (index.html not yet on disk) wrote selectors against anticipated names (.site-header, .logo-link, .nav-links); the HTML subagent emitted different ones (bare `<header>`, .brand, #navLinks with a nested `<ul>`). Cost: a 40-replacement reconciliation pass. A second gap: neither task owned the `<script>` tags, so the site loaded zero JS until the orchestrator wired it.

Preference order:
1. Serialize the contract-definer first (the HTML skeleton), then parallelize dependents against it.
2. Pin the contract in both briefs: a literal list of every class/id the files must agree on, verbatim, marked "do not rename".
3. Assign entrypoint wiring explicitly: the final task of the wave (or the orchestrator) owns importing/loading the pieces; put the exact wiring lines in its brief.
4. If already burned: reconcile CSS selectors toward the HTML (the HTML is the spec of record) using the count-asserted pass; commit as `fix(scope): reconcile selectors with actual markup`.

Also reconcile secondary contracts the same way: aria state (JS must set aria-expanded when the CSS animation keys on it), z-index layering, scroll-margin-top vs fixed header height, image paths the HTML assumes exist.

## 3. Consent-gated verification in subagent briefs

Profiles that deny compound commands will halt a subagent whose verify step chains (`python3 -m http.server ... &` + `curl` + `kill`). The work sits uncommitted on disk.

Brief wording that works:
- "Verify with ONE simple command per check (node --check <file>; curl <url> | head -5). Never chain commands with && or ;."
- "If a command is denied, do NOT retry or rephrase it. Report what is complete and stop."

Parent-side protocol when a subagent halts on denial:
1. Read the produced file in-session and spec-review it directly.
2. Re-run verification with simple, single-purpose commands.
3. Commit the work yourself (single-path git add, never -A on shared repos).
4. A command denied for the subagent is denied for you too - do not re-attempt the same outcome via a different command unless the user explicitly approves; ask instead.

## 4. Entrypoint wiring ownership

The last integration gap is always "the pieces exist but nothing loads them." Prevent it:
- The final task in the wave carries the exact wiring lines in its brief (e.g. `<script src="js/sea.js"></script>` + `<script src="js/main.js"></script>` before `</body>`), or
- The orchestrator applies them post-wave with the count-asserted pass and commits as `fix(scope): load scripts from <entry>`.

## 5. Long single writes degrade mid-generation

Authoring very long content in one tool call can degrade mid-generation: duplicated headers, mangled file references, half-typed sentences, meta-commentary injected into the artifact. Observed twice in one session: a ~25KB plan file write, and a long delegate_task context/goal string (the corrupted dispatch failed schema validation before running - which is the system working, but the content was lost).

Rules:
- Keep single file writes under ~20KB. For larger artifacts, write a precise structural spec instead of full listings: blocks in order, invariants, hard gates, expected behaviors. Embed complete copy-pasteable code only for small files (under ~100 lines).
- Keep delegate_task goal/context compact; point at plan files rather than restating them.
- After any large write, re-read or grep the artifact before trusting it. Tell-tale mangling: repeated section headers, half-words, stray meta-text about the writing process.
- If corrupted, REWRITE the file wholesale in one clean shorter write; do not patch fragments out of a mangled file.
- A corrupted delegation dispatch that failed validation dispatched NOTHING - just re-dispatch compact.

## 6. Terse user tuning rounds

Post-build user feedback often arrives as a numbered list of small perceptual fixes across several files (sizing, spacing, copy swaps, a new stub behavior). Handle as ONE count-asserted batch pass with per-file sections, then a single commit whose message enumerates the points. Verify syntax (node --check) and balance in the same pass. Perceptual items (animation feel, logo size, density) usually need one more nudge - name the exact dial (constant name + file) in the reply so the user can direct the next nudge precisely.
