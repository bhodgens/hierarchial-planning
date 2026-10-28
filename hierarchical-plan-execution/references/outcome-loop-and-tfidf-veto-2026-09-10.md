# Ooutcome loop and tfidf veto 2026 09 10
When to use: outcome-loop tree + tfidf-veto closure.
Lesson: L1-L4 schema/observer/harvest leaves, plan-dir name collision check, hujson traps.

# Outcome-loop tree execution + tfidf-veto closure (2026-09-10)

Session: authored + executed the classifier-outcome-loop tree (L1-L4)
and the tfidf-veto leaf, closing the campaign's metrics gap. Distinct
shapes beyond existing pitfalls:

## 1. Name-collision on plan directories: check the directory BEFORE writing master.md

`docs/plans/classifier-observability/` already contained a COMPLETE
tree from Sep 5 (different scope, same domain — provenance/fail-fast/
digest-cwd). Writing the new outcome-loop master.md there would have
clobbered a finished tree's orchestrator. The write tool's
sibling-modification warning caught it mid-flight; recovery was
`git checkout <path>` + relocate the new tree to
`docs/plans/classifier-outcome-loop/`. Rule: before creating
`docs/plans/<name>/master.md`, `ls docs/plans/<name>*` and read any
existing master.md's Meta/scope — a same-domain predecessor means
relocate AND cross-reference ("design.md in the earlier tree is this
tree's spec input").

## 2. Privacy + outcome capture are one schema change, not two features

Closing the "can we improve accuracy from logs?" gap surfaced a live
privacy hole: `dispatch_log.input_summary` already persisted the first
100 chars of verbatim user messages. The fix and the feature are the
same ALTER: drop the raw column's payload, add salted-hash +
outcome/corrected_agent columns. Doing privacy "later" would mean
migrating twice and leaving plaintext in a 30-day-retention table in
the meantime. Salted hash = SHA-256(salt_id || 0x00 || message), first
16 hex; per-install salt files (0600) in the config dir; error strings
truncated to 200 chars with key/token-shaped content scrubbed.

## 3. Capture gate-internal telemetry at the gate, not by re-derivation

Door-1 abstentions discarded the kNN margin entirely (Match returned
nil). Re-embedding later to recompute margins is costly AND
nondeterministic across model versions. Pattern: a verdict observer
(`SetVerdictObserver`, nil-guarded) on the gate emits
{Routed, AssertedIntent, Confidence, Margin, Suppressed} on EVERY
return path — routed, abstained, cue-suppressed, empty index. The
dispatcher persists margin for all verdicts. Suppressed-vs-abstain is
distinguishable, which the harvest needs (cue-suppression is
intentional, abstention is a near-miss candidate).

## 4. Two correction signals, no NLP needed

- Signal A (implicit): in recordDispatch, resolve the most recent
  'pending' row for the session — if the CURRENT dispatch's agent
  differs and is within N turns, prior = 'corrected' with
  corrected_agent; else 'ok'. Non-classified dispatches (method='',
  e.g. short-message guard) resolve prior to 'ok' only — they are
  never correction sources.
- Signal B (explicit): failure/replan hooks (Escalate on step failure,
  quickplan fallback) set outcome='failed_replan' by task_id.
- Free-text "no I meant X" parsing explicitly out of scope — the
  mechanical proxy suffices, and a human adjudicates the harvest.

## 5. Scratch-daemon config traps (hujson) — cost 6 daemon restarts

- hujson (meept's JSON5) requires quoted keys EVERYWHERE: top-level,
  nested, AND inline (`{ "enabled": false }` not `{ enabled: false }`).
  The line/column error points at the first unquoted key.
- `transport.http.rest` is a BOOL. Omitted → daemon assigns
  `false` over the code default → every /api/v1/* route 404s while
  /health still answers. Symptom is baffling (health OK, all REST 404
  with CORS headers present). Set `"rest": true` explicitly.
- dev_key auth and agent discovery use os.UserHomeDir() — the REAL
  home, NOT MEEPT_HOME. A scratch MEEPT_HOME does not isolate them:
  scratch daemons authenticate against the real ~/.meept/dev_key and
  discover agents from the real ~/.meept/agents. To override an agent
  for a scratch run, copy config/agents into the scratch CWD
  (resolveBundledPath checks CWD then exe dir).
- Old scratch binaries silently lack new routes/behavior — rebuild the
  scratch binary after pulling commits and compare mtime to the commit.
- Two daemon instances on one config → "daemon already running (PID x)"
  from the pidfile; kill old PIDs (and bash wrappers) first.
- The daemon adopted the USER'S live runtime on :8082 ("observed, not
  owned") — point scratch configs' provider baseURL at it rather than
  spawning a second mlx_lm, and never kill the user's runtime.

## 6. tfidf-veto: mechanism ships, effect honestly unvalidated

Char n-gram TF-IDF + logistic as an agreement veto measured 87.35% on
the 48-case gold replay — but that decomposes to 2/48 routes plus
chain credit; a 2-case sample is meaningless (a sibling audit
correction exists: results/alt-methods-correction.md). Ship pattern:
stdlib-Go inference (idf-weighted vectors, softmax argmax) + a python
training script writing JSON weights; missing model file = veto
disabled = byte-identical legacy. Commit message and docs say
"SHIPPED, effect UNVALIDATED — re-validate on harvested traffic."
Measured costs: train 0.24s/370 docs, ~2 MB model, ~0.4ms inference.

## 7. Subagent verification loop that worked for parallel leaves

L2 (prefilter observer) and L3 (outcome capture) dispatched in
parallel with DISJOINT file lists (L2: embedding_prefilter + prefilter
block of dispatcher; L3: store methods + tactical/strategic hooks +
dispatcher non-prefilter region). Explicitly fenced the shared
dispatcher.go by line-region ("parallel leaf owns :767-798 only").
Both landed without collision; orchestrator reviewed and committed
each separately (git reset to split the shared files between commits).

## 8. M4 acceptance honesty

The acceptance run doubled as a policy bake-off: the previously
"adopted" double-confidence policy FAILED the 86.8% gate (84.56%) and
tfidf-veto PASSED (87.35%) — but the pass is 2-route-dominated. Both
results and the sample-size caveat are in
results/m4-gold-acceptance.md and m4-gold-acceptance.json. The FINAL
REPORT states the unvalidated status rather than the happy number.

## 9. Late duplicate completion notices (post-close pattern)

After the tree was declared COMPLETE and the FINAL REPORT committed,
three more completion notices arrived — one per parallel leaf (L1, L2,
L3), each 30 min–3 h after its work was already committed. Protocol
that worked, per notice, without re-dispatching or re-committing:

1. `git log --all -- <leaf files>` — confirm the commit exists (the
   notice's quoted sha may be stale; match on file path).
2. `git diff HEAD -- <files>` — empty = fully landed; report "already
   reviewed and committed as <sha>", NOT a re-review.
3. Check the subagent's claimed deviations against the commit — e.g.
   L1's INSERT-omits-input_summary (stronger than the leaf's write-""),
   L3's immediate-prior-row semantics, L2's peek/take verdict transport
   were all already folded into 1a68a9b5/c5e018f3/5b2b32e4.
4. One-sentence close-out to the user pointing at the ledger table; do
   not re-enter the review loop. Also ignore stale wrapper-exit notices
   (`[IMPORTANT: Background process proc_... exited]` from old bash
   wrappers around killed daemons) — verify the live process once and
   state that it's a queued duplicate.

Only open question these notices raised that was worth answering: none
— but one DID surface a user-visible docs nit worth fixing while
open (the centroid-builder's raw input_summary removal landed in L1;
a stale scratch-daemon binary predating L1-L3 shows empty harvest
counts, which is the tool degrading gracefully, not a bug).
