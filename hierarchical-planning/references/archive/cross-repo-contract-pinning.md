# Cross-Repo Contract Pinning (producer-side plans serving a consumer in another repo)


When to use: producer-repo plan changes data a future consumer in another repo reads.
Lesson: freeze the consumer's read surface as an informational no-owner contract in the master.
## The pattern

When a plan tree in repo A (the PRODUCER) changes data that a present-or-future
feature in repo B (the CONSUMER) reads — an external aggregator over a local
SQLite DB, a parser over exported files, a CLI over a daemon's state store —
the producer's plan must freeze the consumer's READ SURFACE as an explicit
contract in the root master.md. Without it, the consumer-side session must
re-derive the schema from source, and every ambiguity becomes integration
drift discovered only at parse time.

Mark it informational: it has NO owning leaf in this tree. It exists so the
sibling repo's implementer can be authored against a frozen shape.

Worked example: meept→tokscale ingest (2026-09-06, `docs/plans/20260906-tokscale-ingest/`
in the meept repo). Meept widened its `llm_calls` table; tokscale (Rust,
separate repo) will add a session parser over `~/.meept/metrics.db`. The meept
master.md pinned "Contract D: tokscale read surface" — DB path + expansion
rule, exact column→parser-field mapping (tokens_sent→input, tokens_cached→cache_read,
...), the error-row filter (`error = 1` rows carry no usage; consumer skips),
the dedup rule (by monotonic AUTOINCREMENT id, NOT (timestamp, model)), the
consumer's registry entry (client id `meept`, display name, scan root) — while
stating explicitly: "No meept code implements Contract D."

## What a read-surface contract must pin

1. Location + access mode (path, path-expansion rules, read-only vs read-write).
2. Exact column/field names — lowercase snake_case frozen; the consumer parses
   stored strings, so renames break it silently.
3. Zero-value semantics: 0 = "source did not report" vs "zero occurred".
   Consumers treat absent as absent; never invent sentinel values.
4. Error/partial rows: are they written at all? How does the consumer filter them?
5. Dedup/identity rule: which column is the unique key (AUTOINCREMENT id vs a
   composite like (timestamp, model)).
6. Registry surface if the consumer has one (client id, display name, scan root,
   env-var overrides).
7. One line stating nothing in THIS tree implements it.

## Rules

1. Freeze the contract BEFORE authoring leaves — leaves implement up to it,
   never around it. Contract A/B (what leaves build) and Contract D (what the
   consumer reads) must describe the same on-disk result.
2. Contract changes are master.md edits with a dated note in the Notes
   section — never silent leaf-level drift.
3. Do not duplicate the full contract text into leaves; leaves reference the
   master section and restate only the fields they touch.
4. The consumer-side plan (in repo B) cites the producer's contract as its
   source of truth — and per Pitfall 38 cites the repo/spec, not the sibling
   plan tree directory.

## Related notes from the same session

- **Flat trees pass the scanner with a benign warning.** A small tree
  (master.md + leaves at the root, no branch subdirectories) triggers
  `check_template_compliance.py`'s "WARNING: no subdirectories found — Is
  this a plan-tree root?" but still returns `ALL TREES COMPLIANT: True`.
  Do not restructure the tree into a fake branch directory to silence it.
- **Sequential dispatch for same-file leaves** is already governed by the
  Session Pitfall Additions in SKILL.md ("Serialize leaves that edit the same
  shared file") — restated here only because it interacted with this pattern:
  the producer's two leaves both touched the store file that defines the
  pinned schema, so they ran as one wave, strictly ordered.
