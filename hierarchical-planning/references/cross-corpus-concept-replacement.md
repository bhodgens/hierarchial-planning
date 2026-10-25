# Cross-Corpus Concept Replacement

> Recipe for sweeping design changes that touch a concept appearing across the
> entire corpus — "this is third-person now, not first-person", "rename all
> instances of X to Y", "cut feature Z everywhere". See SKILL.md Pitfall 23.

## Why this needs a special pattern

A naive `sed` find-and-replace produces three failure modes on a real corpus:

1. **Under-corrects:** changes the literal phrase but misses semantic
   equivalents. "First-person" → "third-person" misses: "FPS" as genre
   shorthand, "through the eyes" as idiom, "viewmodel" as a technical
   assumption implying first-person, "player's body from a first-person
   overhead angle" (UI description), `# ACharacter — FPS body` (code comment).
2. **Over-corrects:** changes references that should stay. "First-person" in
   a competitor's row of a comparison matrix (Thief IS first-person — that's
   accurate). "First-person" as narrative-grammatical voice in a tone bible
   ("loading screens use period-first-person voice" — I/we, not camera).
   "First-person" in the user's journal authoring instruction ("write in
   first person, as if the player is writing").
3. **Misses technical consequences:** a perspective change isn't just prose —
   it changes FOV values (1P ~90-100 vs 3P ~75-85), the camera rig component
   tree (spring-arm vs direct-attach), viewmodel scope (1P arms rig vs
   full-body world mesh), LOD chain scope (1P viewmodels need their own LOD
   chain), interaction-trace origin (camera position vs capsule), and
   crosshair-vs-reticle framing.

The pattern that works: **parallel digest subagents categorize every hit
before any edit is made.** Then the orchestrator applies all amendments in
one verified batch.

## When to use this pattern

- A perspective / camera / viewpoint change (first↔third person, top-down↔iso).
- A sweeping rename that has semantic equivalents (not just one literal phrase).
- A feature cut that has diffuse technical consequences (not just deleting a section).
- Any change where the user says "update everything to reflect X" and X appears
  in 10+ files.

Do NOT use this for:
- A single-file rename or section move (just edit the file).
- A literal-only find-and-replace with no semantic equivalents (use `sed`).
- A localized feature change (edit the 1-2 affected docs).

## The pattern (proven in `plans-glm/` first-person→third-person pivot)

### Step 1: Dispatch 2 parallel read-only digest subagents

One scans the design corpus (GDD), one scans the plan corpus. Each returns a
structured report grouping every hit by category. They run in parallel because
neither depends on the other.

**Subagent A (GDD scan) prompt sketch:**
```
Find every reference to <concept> in <gdd_dir>/. For EACH hit return:
1. File path + line number
2. The exact sentence/phrase containing the reference
3. Category:
   (a) HARD DESIGN STATEMENT — a declaration of what the game IS
   (b) GAMEPLAY ASSUMPTION — describes behavior assuming the old concept
   (c) COMPETITIVE/GENRE COMPARISON — refers to another product or the genre
   (d) TECHNICAL/CAMERA SPEC — load-bearing technical references
   (e) OUT-OF-SCOPE — false positive (e.g. narrative-grammatical "person",
       framerate "fps", feet-per-second "fps")
4. Suggested amendment

Also find <technical-consequences>: FOV values, camera rig descriptions,
viewmodel assumptions, crosshair assumptions, etc.

Be exhaustive. Quote exact text. Do NOT modify files.
```

**Subagent B (plan scan)** — same shape, scoped to `plans-*/`.

### Step 2: Digest in-session, categorize every hit

The orchestrator reads both reports and builds the amendment list. Critical
sub-step: **decide the disposition of each category** before applying anything.

| Category | Disposition (for first→third person pivot) |
|----------|---------------------------------------------|
| HARD DESIGN STATEMENTS | Must change — factually wrong now |
| GAMEPLAY ASSUMPTIONS | Reword to be perspective-aware |
| COMPETITIVE/GENRE | Context-dependent: keep references to *other* games; keep the *genre label* if it spans perspectives; add a self-row to comparison matrices |
| TECHNICAL SPECS | Must change — load-bearing (component tree, FOV, viewmodel scope) |
| OUT-OF-SCOPE false positives | Leave alone (narrative voice, framerate, ballistics fps) |

The hardest judgment call is the genre label. "Immersive sim" is a *genre*
that spans both perspectives (Death of the Outsider is 3P; Thief is 1P). Keep
it. "FPS" as shorthand for "first-person-shooter-style engine layer" should
become "action/character base" since UE5.8 ships both templates. When unsure,
ask: does this phrase describe *our game's camera* (change it) or *a category
our game belongs to* (usually keep)?

### Step 3: Apply all amendments in one `execute_code` batch

Use `execute_code` with a list of `(path, old_string, new_string, label)`
tuples. The script reads each file, verifies the old_string is present and
unique, replaces it, and writes back. Report per-edit success/failure.

```python
edits = [
    ("docs/gdd/01-vision/01-executive-summary.md",
     "Rebellion is a first-person immersive sim",
     "Rebellion is a third-person-default immersive sim (first-person toggle)",
     "A1: exec summary"),
    # ... 30+ more
]
applied = 0; failed = []
for rel, old, new, label in edits:
    path = os.path.join(BASE, rel)
    with open(path) as f: content = f.read()
    if old not in content:
        failed.append((label, "not found")); continue
    if content.count(old) > 1:
        failed.append((label, f"{content.count(old)}x")); continue
    content = content.replace(old, new, 1)
    with open(path, "w") as f: f.write(content)
    applied += 1
print(f"{applied}/{len(edits)} applied")
```

**Why `execute_code` and not N `patch` calls:**
- One tool call vs N round-trips.
- Per-edit verification (uniqueness check) catches stale old_strings before
  they silently fail or corrupt.
- The failure report tells you exactly which edits need their old_string
  re-read (often a line-wrap or punctuation difference).

**Failed edits:** re-read the exact line with `terminal grep -n`, then apply
those few via individual `patch` calls with the corrected old_string.

### Step 4: Verify post-application

Run a grep that distinguishes intentionally-kept references from stale ones:

```python
# Should be 0 stale hard statements
r = subprocess.run(["grep", "-rn", "first-person immersive sim",
                    "docs/gdd/", "plans-glm/"], capture_output=True, text=True)
# The only hit should be the changelog entry describing the change itself.

# Remaining 'first-person' hits — review each for category
r2 = subprocess.run(["grep", "-rn", "first-person",
                     "docs/gdd/", "plans-glm/"], capture_output=True, text=True)
# Filter out amended lines (those containing 'toggle' or 'default')
stale = [h for h in r2.stdout.split("\n")
         if h.strip() and "toggle" not in h.lower()
         and "default" not in h.lower()]
# Manually confirm each is an intentionally-kept reference.
```

Also run the line-number corruption check (`grep -rcE '^\s+[0-9]+\|'`).

### Step 5: Changelog entry + commit

Per AGENTS.md Rule 1, record a changelog entry listing every file touched and
the nature of the change. Commit with a descriptive message.

## The false-positive categories (do not change these)

From the `plans-glm/` first→third person pivot, these matched the grep but
were correctly left alone:

- **Framerate "fps":** "60 FPS", "30 FPS", "muzzle velocity 1,500 fps" —
  frames/second or feet/second. Untouched.
- **Narrative-grammatical "first person":** tone-bible entries about loading-
  screen voice ("period-first-person voice", "first-person future tense") —
  I/we grammatical person, not camera. Untouched.
- **Journal authoring voice:** "Write in first person, as if the player is
  writing in their journal" — instruction for prose voice. Untouched.
- **Competitor perspectives:** "The foundational text for first-person
  stealth" (about *Thief*) — accurate description of another game. Untouched.
- **Genre labels:** "immersive sim" / "immersive simulation" (~40 hits) —
  a genre that spans both perspectives. Untouched.

The verification grep in step 4 is what confirms these were intentionally
kept, not missed.

## Technical consequences to check (perspective pivot specifically)

When changing camera perspective, these technical specs need explicit
amendment beyond the prose:

| Spec | 1P assumption | 3P amendment |
|------|---------------|--------------|
| FOV | ~90-110° | ~75-85° (add 1P companion value if toggle exists) |
| Camera rig | `UCameraComponent` direct on capsule | `USpringArmComponent` + boom-mounted camera |
| Character mesh | first-person arms only (hidden body) | full-body skeletal mesh (visible) |
| Viewmodel | separate arms/weapon LOD chain | world weapon mesh; 1P viewmodel LOD only if toggle |
| Interaction trace | from camera/eye position | from camera OR capsule (follows active perspective) |
| Crosshair | center-screen dot | OTS reticle (3P) or iron-sights (1P) |
| Lean | eye-position shift | camera orbit + upper-body tilt (capsule stays put) |
| Component tree (coding standards) | `Mesh — first-person arms`, `Camera — first-person camera` | `Mesh — full body`, `SpringArm`, `Camera — boom-mounted` |

Missing these is the most common cause of "we changed the docs but the
implementation still assumes the old perspective."
