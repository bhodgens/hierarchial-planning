# Plain-language restatement on request ("explain that again like I'm stupid")

User preference, surfaced 2026-09-08 during the meept classifier campaign
(after a dense metrics table: coverage/precision/E2E/SCORE columns and a
fine-tune divergence diagnosis). User asked: "explain that again like I'm
stupid."

## When to trigger

- The user asks for a restatement in any form ("explain that again like
  I'm stupid", "in plain English", "I'm lost", "what does that mean
  practically").
- Proactively: when a response leans on 3+ campaign-specific metrics or
  ML jargon (precision/coverage/tau/lr underdose), offer or include a
  short plain-language recap at the end.

## The pattern that worked (shower-temperature analogy for learning rate)

1. Restate WHAT the system is for, in one sentence ("a tiny model that
   answers instantly for easy messages and says 'I don't know' for hard
   ones").
2. Restate the failure as a person-level metaphor, not math: learning
   rate = shower temperature knob; too cold = nothing happens. "Our
   steps were so small the water never warmed up. One number, 50× too
   small."
3. State the fix as an action, not a technique ("turned the knob up").
4. End with the concrete before/after in outcome terms ("caught zero
   messages before; now handles 56% instantly, 95% right").
5. No tables, no metric names, no column headers in the restatement.

## Why it matters with this user

The user is highly capable but runs many parallel campaigns; dense
metric-speak in the middle of a long session loses the thread. The
plain-language pass re-anchors the decision, not the vocabulary. Do the
dense version FIRST (they want the real numbers), then the plain
restatement on request — don't preemptively dumb everything down.

## Second confirmed use (2026-09-09, wiring decision)

The user said "I don't understand this in the least bit" about a head-
wiring recommendation (k-NN unanimity vs centroid-margin). The
restatement that worked: describe each brain as a person-level
metaphor (k-NN = "your message must look like 5 stored examples all
agree"; centroid = "compare to one average point per intent, route if
the winner clearly beats second place"), then the decision as a plain
swap ("trade the strict brain for the margin brain"), then the
concrete outcome ("routes 34-56% instead of 3.7%"). Same shape as the
first use: metaphor per component, action-oriented fix, outcome numbers.

## Related: architectural explanations also need the metaphor pass

When the user says a design concept is unclear ("I'm not sure these
lanes are correct", "I don't understand this at all"), the fix is the
same shape applied to architecture: state each option's DELIVERABLE
("what do I want to exist when this is done"), put the boundary in a
decision table keyed on observable facts, and give one worked example
per row. This produced the intent-routing decision table
(docs/workflows/intent-routing.md) that the user then asked to ship as
user-facing documentation — a metaphor-pass output became a shipped
doc.

## Third confirmed use (2026-09-10, "explain the classifier simply")

User asked for "the shape and size of the classifier in simple terms —
architecture, services/tools, resources/timing. Terse." The pattern
extended to WHOLE-SYSTEM description: (1) one metaphor for the pipeline
("3 doors, cheapest first"), (2) a components-vs-doors distinction the
user explicitly corrected — listing infra pieces (embed server,
centroid store, gate logic) as if they were separate stages confused
them; they are all PARTS of one door, (3) accuracy-as-report-card
("87% right = of every 100 messages this door classifies, 13 go to the
wrong agent — but they're recovered downstream, not lost"), and (4)
explicitly separating confidence (what the model says per message) from
accuracy (the pre-measured grade across many messages) — the user
conflated them. Then the user asked for the hierarchy flow as shipped
docs (docs/workflows/classification-architecture.md): a metaphor-pass
explanation is a repeatable source of user-facing documentation — when
the plain-language version lands, offer to commit it as a doc.

Also this turn: when the user says a previous answer confused them
("you mention qwen3 as the embed server but don't mention it as a
door"), own the conflation directly — name the error ("my component
table was a parts list, not the doors"), then restate. Don't defend
the original framing.
