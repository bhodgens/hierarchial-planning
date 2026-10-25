# Cross-Repo Informational Contracts (pinning repo B's read surface in repo A's plan)

Pattern for features that span two repos where repo A produces data and a
PLANNED-BUT-UNWRITTEN consumer in repo B reads it. Worked example: meept
2026-09-06 (`docs/plans/20260906-tokscale-ingest/master.md` Contract D) —
meept fixes its token-recording schema; tokscale's future `sessions/meept.rs`
parser (separate repo, separate feature branch) will read `~/.meept/metrics.db`.

## The problem it solves

Without the pin, the sibling-repo implementation must re-derive the read
surface from repo A's code at implementation time — re-opening repo A, or
worse, guessing and drift. The schema and the parser then evolve
independently and break silently.

## How to author it

In repo A's root `master.md`, under `## Interface Contracts (frozen)`, add a
contract explicitly marked informational:

- **Header note:** "informational — implemented in repo B; no repo A code
  implements this contract."
- **Exact read surface**, as actual code/SQL, not prose:
  - file/db path and table names as they exist on disk;
  - every column the consumer reads, with its EXACT on-disk name;
  - the projection/query the consumer will run (verbatim SQL if SQL);
  - mapping to the consumer's types (column → field table);
  - **zero-value semantics** (e.g. "0 = provider did not report, NOT zero
    occurred") — these are behavior, not comments;
  - dedup/identity rule for append-only sources;
  - error/filtered-row rules (e.g. "error=1 rows carry no usage; consumer
    filters them");
  - the consumer-side registry entry (client id, display name, root path)
    when repo B is a registry of clients.
- **Owner:** "no leaf — this is the pinned interface between this tree and
  repo B's feature branch." A leaf that wants to change it must STOP and
  amend the master contract instead.

## Rules

1. The informational contract is frozen with the same force as code
   contracts. If implementation discovers reality disagrees (column name,
   timestamp format), the fix is a master.md amendment + changelog note, not
   a silent local adjustment.
2. Repo A's tests should pin the contract from the A side (a projection test
   running the verbatim SQL the consumer will issue — see meept
   `tokscale_ingest_test.go` in leaf 02) so drift fails a test in A before
   it breaks B.
3. Cross-reference the consumer repo by NAME and branch/plan path in one
   place only (the contract header); leaves stay self-contained per Pitfall
   38 (no sibling-forest references — repo B is not a plan forest, but the
   same isolation logic applies).

## Anti-patterns

- Splitting the read surface across leaves (each leaf documents "its"
  columns) — the consumer cannot assemble a contract from fragments.
- Describing semantics in prose ("reasoning tokens when available") instead
  of exact zero-value rules — "when available" is unimplementable.
- Implementing half of it in repo A "to be helpful" — the contract exists
  precisely so A changes nothing beyond the schema it already needs.

## Consuming side (repo B, executed 2026-09-06 — tokscale feat/meept-ingest 75afca63)

The consumer-side session authors against the contract text, not repo A's
source:

1. **Cite the pin in the parser's doc comment:** "schema pinned by repo A's
   integration test `<path>` (Contract D in `<plan path>`); if that test
   changes, this parser changes with it." The citation IS the drift alarm.
2. **Negative test for the pre-contract schema.** A deployed producer whose
   binary predates the migration still writes the OLD schema. The parser
   must return EMPTY (quiet) on missing columns — probe `pragma_table_info`
   once, not per-install error logs. Mirror this as a unit test with a
   legacy-schema fixture.
3. **Mirror the producer's own fixture.** The B-side unit test seeds an
   in-memory DB with the SAME fixture rows the A-side pinning test asserts —
   when both pass, the two repos provably agree on the same numbers.
4. **Exhaustive-match tax.** Adding a client to a registry with
   `ClientId::COUNT`-sized arrays and exhaustive `match` arms breaks
   compilation in predictable places (display-name test arrays, hotkey
   tables, ClientFilter conversions, count assertion). Budget for ~4-6
   exhaustiveness touch points beyond the parser itself; let the compiler
   enumerate them rather than grepping.
5. **Deliverable ordering per user instruction:** producer repo first,
   consumer second — "do the X things in the X tree first" is an explicit
   sequencing directive; merge the producer branch to its main before
   starting the consumer branch when the consumer chases its schema.
