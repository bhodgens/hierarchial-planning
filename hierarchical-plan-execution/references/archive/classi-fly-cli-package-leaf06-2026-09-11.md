# Cclassi fly cli package leaf06 2026 09 11
When to use: CLI + packaging leaf as direct implementer.
Lesson: flag/parse patterns, packaging gates, consent-denial handling leaf-side.

# classi-fly leaf 06 (CLI + packaging) — 2026-09-11, direct implementer

Sixth classi-fly session ref (after 02-ingest, 01/02-flyformat,
04-training, 05-eval, 07-integration). Leaf 06 built `cmd/classi-fly`
(pack/info/classify/build), README/NOTICE/Makefile/LICENSE, against
sibling leaf 02's `reservoir` package which was NOT yet landed at start
and LANDED MID-SESSION. 16 leaf tests green under `-race -count=2`;
release binary 6,826,898 bytes; eval fixture .fly 535 bytes.

## Mid-session sibling landing: author to contract, re-align when it lands

Distinct from RED-BUILD-BLOCKED (integration-leaf ref): the missing
package arrived WHILE the consumer leaf was in flight.

1. Write consumer code to the FROZEN contract signatures only
   (`reservoir.Load/Classify/Info/WriteFile(path, Artifact)`). Expect the
   landed shape to differ from the leaf-doc sketch — leaf 02's real
   `Artifact` was float64 PRE-quantization arrays + named `InputMode`
   type + embedding-major `InW`, not the spec sketch's int8/float32/uint8.
   The landed shape wins (contract-owner rule from the flyformat ref);
   re-align your call sites when it lands, don't argue.
2. Sibling edits appear as MYSTERY build errors in YOUR package (`serve.go`
   from leaf 07 materialized; transient `readoutScalePending` undefined
   errors from their in-flight fly.go edit). Protocol: `ls cmd/<pkg>/`,
   `git status --short` to identify foreign files, then poll
   `go build ./...` on a 10s loop until green instead of touching their
   files. NEVER stub or "fix" sibling symbols.
3. Check sibling test files for helper-name collisions early (same
   package!). `grep '^func ' sibling_test.go` before writing your own
   helpers; also adopt their runner signature when wiring their subcommand
   into YOUR main.go dispatch (`runServe(argv []string) int` here).

## Round-trip test = cross-leaf Contract-1 integration probe

The CLI leaf's pack→Load round-trip test is the first REAL producer/
consumer pair for the frozen container format. It caught a sibling bug
the sibling's own tests missed: WriteFile (per Contract 1 text +
flybytes.py) writes readout bytes THEN readout_scale; the landed Load
read the scale BEFORE the readout block → first 8 readout bytes decoded
as the scale → `bad readout_scale 0` on every packed file. Protocol:
diagnose the misalignment from the reader source, decode your own output
file with the independent Python flybytes/state reader to confirm YOUR
bytes are contract-correct, report the exact wrong-order walk to the
sibling/orchestrator, and do NOT re-order your WriteFile call to match
their bug. (Sibling fixed fly.go mid-session; the fix surfaced as
transient compile errors — poll for green, re-run, move on.) Also found
same-day and reported, not fixed: tools/train/train_readout.py consumes
ridge_fit's W[N][K] (Contract 3 neuron-major) as class-major in
score_readout/_class_scores — only correct when K==N.

## stdlib flag + contract CLI syntax: reorder must be VALUE-AWARE

Contract syntax puts flags AFTER the positional
(`classify model.fly --embedding 0.1,0.2`), but Go's `flag` stops at the
first positional. Naive fixes both fail:

- Reorder AFTER fs.Parse: too late, Parse already stopped.
- Move positionals to FRONT naively: `--embedding 0.5,0.25` — the flag's
  VALUE doesn't start with `-`, so it gets classified positional and the
  path is parsed as the embedding value ("...model.fly is not a number").

Correct: build a value-taking map from the FlagSet BEFORE Parse
(`fs.VisitAll`; a flag whose Value implements `IsBoolFlag() bool` takes
no value), then one pass: flags (with their next arg re-attached unless
`--name=value`) go first, positionals after, `--` terminator preserved.
Three runs to green; write the pitfall into the helper's doc comment.

## Pack-block contract extension (bridge, don't silently drift)

Contract 3's adjacency + readout exports carry no `embed_dim`/`steps`/
input-projection, which Contract 1's payload requires → a valid .fly is
UNASSEMBLABLE from the two exports alone. Bridged with a third `--pack`
JSON block (`{embed_dim, steps, input_mode: seed|matrix, seed?, in_w?,
in_scale?}`), documented in README as an extension; per SHARED-CONVENTIONS
the master.md Contract 3 edit is the orchestrator's call. Same pattern as
leaf04's decay-header gap (INDEX): the packer writes what the frozen
format needs that the exports don't carry; name it an extension, never
rename frozen fields.

## Landed Artifact.InW is DEQUANTIZED (byte × scale), not raw bytes

WriteFile requantizes `v / InScale`, so Artifact.InW must carry
dequantized values for the round trip to be byte-exact: pack-block byte
40 × in_scale 0.1 → InW 4.0 → stored back as byte 40. Passing raw bytes
inflates them 1/scale× → `value 400 exceeds int8 range after scaling`
(the library fails loud — good). Scale conventions to respect: trainer
writes weight_scale/readout_scale = max|v|/127 floored at 1e-6; pack uses
max|adjacency|/127 for the graph and takes the readout export's
readout_scale verbatim.

## build subcommand: provisional matrix-mode artifact + fixture scheme

The trainer reads states from a .fly and REJECTS seed mode → build packs
a provisional matrix-mode artifact (per-lane in_w, placeholder zero
readout) with the trainer, then repacks the final artifact with the
trained readout; provisional and final share graph/projection/steps/decay
so train-time states == runtime states. Scaffold pairs lesson: the
label-consistent 6-variant lane-rotation scheme (each class ci sweeps
lanes (ci+variant) mod D, mixing term on even variants) trains; the
"cleaner" single-direction-per-class schemes (sin-derived unit vectors,
amplitude families) FAIL the trainer's learn-guard (mean loss ≥ ln K)
because sub-saturated drives leave tanh states nearly collinear. Don't
beautify a working fixture scheme without re-running the end-to-end —
the passing e2e test WAS the evidence the rotation scheme works.
Saturation (drive ~4) separates; unit drives collapse; the guard failing
at 0.698 vs ln(2)=0.6931 looks like a rounding problem but is a
representativeness problem (probe against the REAL synthetic graph via
the Python states module before touching Go again).

## Verbatim info over a parsed API

Public Contract-2 API exposes only parsed Info(), but the contract says
`info` prints the header JSON VERBATIM → tiny framing-only reader in the
cmd package (magic 8B + LE uint32 len + raw JSON bytes; payload never
decoded) + a byte-identity test (stdout minus trailing newline ==
header bytes on disk). Reusable shape for any "print it as stored"
subcommand over a structured container.

## Consent-gate confirmation (recurring)

Final cleanup (`rm -rf` of /tmp probe scripts + smoke dir, compound
command) was denied — matches the standing protocol exactly: stop the
class, leave artifacts in place, mention once in the report. Verified
again this session: keep verification and cleanup in SEPARATE commands,
and leave /tmp evidence for the user.
