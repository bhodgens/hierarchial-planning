# classi-fly leaf 01-reservoir-core/02-fly-format — Go `.fly` producer + Load/Classify (2026-09-11)

Fourth classi-fly session ref (02 ingest, 05 eval reader, 04 trainer; this one is the
**Go producer/runtime side** of Contract 1: `internal/flyformat` container+header,
`reservoir.Artifact`/`WriteFile`/`Load`/`Classify`/`Info`). All green:
`-race -count=10`, gofmt/vet clean, nothing committed (orchestrator commits).
Cross-language interop PROVEN: Go `WriteFile` output parsed by landed
`tools/train/states.py`; Go `Classify` and the Python reference pipeline return
identical results (class=alpha conf=0.591406) on the same file; `decay` header
extension round-trips into Python.

## 1. Landed consumers are the normative tiebreaker for contract-prose ambiguity

The leaf memo's prose suggested `in_w[i*D+j]` (neuron-major); ALL THREE landed
Python readers are EMBEDDING-MAJOR (`states.py` reshapes win as `(embed_dim, n)`,
`flyio.py` as `(d, s)`, the eval fixture generator packs `(d, n)`), with
`in_row_len = N`. Rule: when a producer lands against already-landed consumers
of the same frozen binary format, grep the landed readers'
`unpack_from`/`reshape` calls and match THEM byte-for-byte; record the
memo-prose contradiction as a documented deviation. Byte compatibility beats
prose. (The contract's payload-ORDER table was unambiguous and matched
everywhere — the ambiguity was only in the memo's layout gloss.)

## 2. Cross-language arbitration: the Go-side twin of "goldens are not goldens"

`TestClassify` failed with class=beta vs expected alpha. Instead of relaxing the
test, dumped the fixture's post-quantization arrays as JSON from a throwaway Go
main (outside the module, /tmp) and ran the SAME arrays through the landed
`states.py` reference: Python returned the same "wrong" answer → the fixture
expectation was fine and the implementation was wrong → real bug found
(**see §3**). Protocol: code-vs-expectation disagreement on a frozen format gets
arbitrated by an INDEPENDENT reference implementation of the same semantics, not
by tuning either side until green. Cheap mechanics: quantized int arrays +
embedding as JSON; Python rebuilds cfg dict and runs `states.states()` + softmax.

## 3. Contract 1 readout order: matrix FIRST, scale AFTER — buffering required

Payload order is `readout int8[N*K]` THEN `readout_scale f64`. The natural
"read the scale, then dequantize as you stream" implementation silently
transposes the order (this session's bug): you must buffer the raw int8 block,
read the f64 scale that follows it, then multiply. Symptom signature: plausible-
structure garbage — correct-ish state vector, wrong winner with non-degenerate
probabilities (off-by-lane logits). Contrast with leaf04's transposition
signature (garbage LENGTH field = your payload bytes); this variant has no
length field to trip on, only wrong numbers — which is why the independent-
reference arbitration (§2) is the reliable detector.

## 4. klauspost/compress zstd v1.20 API facts (LSP caught all three)

- `(*Encoder).EncodeAll(src, dst []byte) []byte` — SINGLE return, no error.
- Construct codec with `zstd.NewWriter(nil, opts...)` for EncodeAll use.
- No `WithDecoderCRC` option exists (only `WithEncoderCRC`); use
  `WithDecoderMaxMemory`. `(*Decoder).DecodeAll(input, dst) ([]byte, error)`.
- Trust LSP diagnostics over memory; confirm with
  `grep -n '^func' $GOMODCACHE/github.com/klauspost/compress@vX/zstd/*.go`.
- License gate re-confirmed: BSD-3-Clause (+Apache-2.0/MIT subpackages) — read
  the module-cache LICENSE before adopting (pattern: dependency-license-gate.md).

## 5. Sibling WIP caller assumes your API shape — contract owner wins

`cmd/classi-fly/pack.go` (leaf 06, UNTRACKED, same concurrency group B) already
called `reservoir.Artifact` with a different shape guess: `[]int8` weights,
`[]float32` bias/threshold, `uint8` mode constants. The leaf defining the type
KEEPS the spec shape: `Artifact` carries float64 arrays and `WriteFile` owns
quantization — Task 4 mandates the `scale/2` tolerance be documented on
WriteFile's doc comment, which is impossible if the caller pre-quantizes. Do not
contort a contract-owned type to match sibling WIP; flag the mechanical
adaptation (~6 lines: drop their quantizeTo8/maxAbs pre-step, convert
float32→float64, use `reservoir.InputModeMatrix/InputModeSeed`) in the report
for the orchestrator to reconcile with leaf 06's owner.

## 6. Seed-mode vs matrix-mode win layout (Classify dispatches on len)

Matrix mode: `win` is embedding-major `D*N` (`u[i] = sum_j in_w[j*N+i]*x[j]`).
Seed mode: `win` is neuron-major `N`, expanded from `math/rand.NewSource(int64(seed))`
as `Int31n(5)-2` per neuron; drive is scalar `u[i] = win[i]*x[0]` (matches
`core.forward` fixture semantics; the Python trainer REFUSES seed-mode files —
Go `Classify` handles both). Dispatch in Classify on
`len(win) == n*len(embedding)`; a fixed interpretation panics index-out-of-range
on the other mode.

## 7. decay header extension landed (closes leaf04's CONTRACT GAP)

`Header.Decay float64` json tag `decay,omitempty` — written when `Artifact.Decay != 0`,
validated (0,1) when present on decode; `Load` defaults 0.8 = Python
`DEFAULT_DECAY`. Verified round-trip into `states.load_states_config`
(header → kwarg → default chain both runtimes). Leaf 06's packer writes it via
`--decay` (default 0.8); readers must keep treating it as OPTIONAL.

## 8. Fixture-authoring micro-pitfalls (each cost one red cycle)

- Scale sizing: max|value|/scale must fit int8 — ReadoutScale 0.05 with readout
  value 12 → 240 overflow error. Size scales from the fixture's actual max first.
- Modulo precedence: `readout[(c+1)*k%c+c]` divides by c → panic at c=0; wanted
  `readout[((c+1)%k)*k+c]`.
- One-hot loop bound must respect BOTH dims of the `n*d` slice (`j < n && j < d`).
- Noisy filler in `in_w` keeps softmax competitors alive — a "clean lane" fixture
  wants silent (zero) off-lane entries; assert confidence ranges against what the
  fixture actually produces (cross-check via §2 first, then pin).

## 9. Session mechanics

- RED→GREEN per task per the leaf doc; write test, observe FAIL, implement rhythm
  worked as prescribed. LSP diagnostics on every write caught type errors before
  any test run (undefined symbols during RED are EXPECTED — filter to your own).
- Final compound command (test rerun + /tmp cleanup) DENIED at the consent gate →
  stopped immediately, left artifacts in place, mentioned once in the report.
  Confirms: run verification in its OWN command first; treat scratch-dir cleanup
  as a separate user-handed action, never bundled onto a verification command.
- Pre-existing failure in sibling `examples/host_judge_test.go` (leaf 07's
  package, `judgeDecide` routes on empty-label agreement) — NOT this leaf's;
  flagged in report with file:line, not fixed (not in file list).
