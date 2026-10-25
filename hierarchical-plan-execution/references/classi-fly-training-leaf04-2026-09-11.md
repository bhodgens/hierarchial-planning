# classi-fly training leaf 04 (2026-09-11) — condensed session bank

Repo: `~/git/classi-fly`. Leaf 04 (readout trainer + calibration)
implemented as direct implementer; NOT committed (orchestrator owns git).
Companion same-day refs: classi-fly-connectome-ingest-2026-09-11.md
(leaf 02) and classi-fly-eval-harness-2026-09-11.md (leaf 05 built a
Contract 1 READER; leaf 04 built the fixture-grade WRITER — both from
master.md text alone, before the Go packer exists).

## Files (all under tools/train/, 13 tests green via `python3 -m pytest tools/train -q`)

`states.py` (pure `states()` mirroring the Go recurrence
`s = tanh(decay*s + W*s + win*x)`; `.fly` reader + adjacency-dict config,
numpy path + stdlib fallback), `train_readout.py` (closed-form ridge
`W = (SᵀS + λI)⁻¹SᵀY`, logistic fallback at the 1e-3 lr floor, CLI,
Contract 3 export + report), `calibrate.py` (`choose_thresholds`),
`flybytes.py` (fixture-grade .fly WRITER), `fixture.py` (deterministic
hardcoded 6-neuron artifact, no RNG).

## Golden-vector lesson: hand arithmetic is not a golden

Leaf asked for a "self-consistent golden generated in the test". I
hand-computed the expected states and got them WRONG (0.2925/0.1354; true
values 0.8049/0.5262 — my mental tanh chain dropped the recursive term).
The implementation matched an INDEPENDENT one-off script exactly. Rule:
compute goldens with a throwaway script (fresh transcription of the
recurrence, separate process), paste the repr; when code and a
hand-derived expectation disagree, suspect the hand math first and
arbitrate with the independent script. Implementer-time twin of
verify-with-your-own-golden.md (that one catches orchestrator-side
code-vs-spec drift; this catches implementer-vs-their-own-arithmetic).

## Contract 1 field-order transposition signature

master.md's binary layout puts `in_w int8[D*S]` BEFORE `in_row_len
uint32`; I wrote the reader row_len-first. Failure signature:
`in_row_len 16973061 != neurons 6` — 16973061 = 0x01030505 = the first
in_w BYTES (5,5,3,1 little-endian). **Garbage in a length/size field that
decodes as your actual payload bytes = field-order transposition**;
re-transcribe the layout directly from the contract text, not memory.
(Writer and reader were both mine, so they agreed with each other —
agreement of two artifacts by one author proves nothing; see
verify-with-your-own-golden.md.)

## Python mechanics

- `bytes(list)` REJECTS negative int8 values (ValueError); use
  `struct.pack("<%db" % len(v), *v)` for int8 value lists.
- zstd dual path (improves on leaf-05's "decompress only if zstandard
  importable"): Python 3.14+ stdlib `compression.zstd` → `zstandard` →
  `pyzstd` → raw; reader auto-detects the frame by magic 0x28 B5 2F FD,
  so a committed fixture can be stored either way.
- numpy 2.4.6 present; both solver paths still tested — the logistic
  fallback IS the deliverable when numpy is absent, and the underdose
  guard (mean loss < ln(K), else hard fail) is asserted on BOTH paths.

## Calibration semantics (quantile search matching the leaf's intent)

Candidates = quantiles (0..1 step 0.025) of the class's OWN train
scores; lane precision counts OTHER-class rows crossing the threshold as
FP; chosen = LOWEST candidate meeting `target_precision` (max coverage),
fallback = max observed score. Fixture design: to force a high
threshold, contamination must land INSIDE the class's own score band
(leak scores above the band bottom) — leak rows merely scoring low never
push the threshold up.

## Cross-leaf contract gap for the orchestrator

Contract 1's frozen header has NO `decay` field, but the recurrence
needs one. Trainer resolution: optional header `"decay"` extension →
`decay` kwarg → `DEFAULT_DECAY=0.8` (documented in states.py). **Leaf 06
packer MUST write the decay header extension or train/runtime decay
disagree.** Until 01's Go golden lands, state extraction is verified
self-consistent only (.fly path == dict path == independent script).

UPDATE 2026-09-11 (leaf 01/02 Go producer landed — this gap is CLOSED,
ref: classi-fly-flyformat-go-2026-09-11.md): the Go writer now emits the
`decay` header extension (omitempty; validated (0,1) on decode; Load
defaults 0.8 = this trainer's DEFAULT_DECAY), and leaf04's writer-side
transposition signature got its producer-side twin: the Go Load initially
read `readout_scale` BEFORE the readout matrix (Contract 1 order is
matrix-first) — no length field trips this variant, only wrong winners
with plausible probabilities, so the reliable detector is running the
same quantized arrays through this trainer's `states.py` as an
independent reference (it returned the identical "wrong" answer, proving
the implementation wrong and the fixture right).
