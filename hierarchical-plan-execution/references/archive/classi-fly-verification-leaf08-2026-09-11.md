# Cclassi fly verification leaf08 2026 09 11
When to use: adversarial verification + license audit leaf.
Lesson: run every boundary case a hand-off asserts; PIN-test + inverting repro script shape.

# classi-fly leaf 08 — adversarial verification + license audit (2026-09-11)

Direct implementer role, Python. Deliverables: `tools/verify/{recompute,quant_drift,license_audit}.py`
+ tests + `tools/verify/ridge_orientation_repro.py` + `docs/VERIFICATION.md`.
Seventh classi-fly session (after 01/02, 02-ingest, 04-training, 05-eval-harness, 06-cli, 07-integration).

## 1. Hand-off "known issue" claims are hypotheses — run the boundary case BEFORE encoding them

The orchestrator's hand-off flagged the ridge orientation bug
(`ridge_fit` returns W[N][K] per Contract 3; `score_readout`/`_class_scores`
consume it class-major via `zip(W, bias)`) **with an exception claim**:
"correct only when N == K". Empirical test at N==K=4 (seed 5, 24 clustered
samples): production train accuracy **0.75** vs **1.00** under the correct
`h @ W + bias` orientation. The exception is FALSE — the two interpretations
coincide only when the fitted W happens to be symmetric, and a ridge fit on
clustered data is not symmetric. The hand-off's parenthetical was derived
from a code read, never run.

Consequences if encoded unverified: VERIFICATION.md would have documented a
false boundary condition, and the "incidentally correct at N==K" test would
have been vacuous (and would FAIL once someone "fixes" the non-bug it
asserts). The empirical check also made the finding STRONGER (bug
unconditional → fix scope larger). Protocol: a hand-off names the bug; you
own the trigger conditions. Run every boundary case the claim asserts before
writing any doc or test that states when the bug applies.

## 2. "Verify, don't fix" leaf shape: pin test + inverted-exit repro script

The leaf was instructed to verify, not fix, the trainer bug. The closeable
shape that worked:

- **Pin test** (`test_ridge_orientation.py`) asserting the BUGGY signature
  (production acc < 0.5, divergence > 0.2, fit-RMSE < 0.1 to prove the fit is
  sound and only the scoring is wrong), with a failure message telling the
  next session what to do: "the fix likely landed; update VERIFICATION.md
  and this pin."
- **Standalone repro script** (`ridge_orientation_repro.py`) whose exit code
  INVERTS on fix: 0 = bug reproduced, 1 = not reproduced (fix landed). The
  doc cites the exact command, so finding-closure later is: run script,
  see exit 1, flip pin test, close finding.

Never pin a bug by asserting correct behavior "is wrong" — pin the
measurable signature and make both artifacts cross-reference.

## 3. Quant twin artifacts: identical bytes INCLUDING reader-side RNG expansion

Task: measure float-vs-int8 drift by loading two `.fly` twins through the
reference reader. First attempt measured max state delta 0.666 — fixture
error, not drift: the float artifact's input projection is expanded by the
READER at load time (`np.random.default_rng(seed).integers(-2, 3, (d, n)) *
in_scale`), while the twin writer drew its matrix with `integers(-3, 3)` —
different range, different matrix, diverging by construction.

Rules for twin-based drift/isolation fixtures:
- Every byte except the single intended difference must match — including
  values the reader DERIVES (seed-mode expansions consume the same RNG
  stream; burn identical draws before drawing shared blocks like the
  readout so both files carry identical readouts).
- Before trusting any drift number, diff the two artifacts' dequantized
  input projections directly (`u = x @ win_f` vs `u = x @ in_w_i * in_scale`
  on a probe) — a nonzero u-delta means the fixture is broken, not the model.
- A PASS with max delta exactly 0.0 is the expected result when twin values
  already live on the int8 grid; it verifies container-mode interchangeability,
  not producer quantization policy (say so in the report).

## 4. Absence of evidence artifacts is itself a finding

Zero committed `results.json` in the repo ⇒ every real-data headline verdict
(E1/E2/E3/E5) is **UNVALIDATED**, and the report says so per-experiment with
the evidence line "no campaign results exist" instead of manufacturing
numbers. The verification tooling is still fully exercised via a
hand-computed synthetic fixture (19 cases, counts derivable by hand:
P=17/19, E2E=(17+0.868·0)/19, judge E2E=(14+0.868·5)/19), plus TAMPER tests
proving the tool flags what it exists to flag: cooked E2E/P vs per-case
rows, a lying route count, a tampered stored value. A verifier's
false-negative resistance is part of the deliverable — a recompute tool
that agrees with everything proves nothing.

## 5. Independent policy restatement + fail-closed defaults (license audit)

- The audit restates the license policy table locally and must NOT import
  the producer's registry (`tools/ingest/registry.py`) — a check importing
  the producer's policy can be silently relaxed by the producer. Same
  independence rule as recompute never importing the harness's aggregator.
- Fail-closed classification: unknown license strings → UNKNOWN (not
  shippable); CC-BY variants shippable ONLY with non-empty header
  attribution, else demoted to UNKNOWN; any CC-BY-NC variant → BENCHMARK-ONLY.
- Header fields may be absent/empty: `str(header.get(field) or "")` —
  `str(None)` would produce the string "None" and pass a truthiness check.
- NOTICE cross-check maps artifact source strings to NOTICE source FAMILIES
  (`larval-connectome` → `larval`); match against the family, and test the
  gap case against a NOTICE file that deliberately omits a family.

## 6. CLI entry points bypass conftest sys.path shims

Tests passed via `conftest.py`'s sys.path setup, but `python3 tools/verify/quant_drift.py`
raised ModuleNotFoundError — direct CLI runs never load conftest. Any module
intended to run both as test-import and as a script needs its own guarded
bootstrap:

```python
_EVAL = Path(__file__).resolve().parent.parent / "eval"
if str(_EVAL) not in sys.path:
    sys.path.insert(0, str(_EVAL))
```

Catch this by running every new CLI's `main()`/`__main__` path once directly,
not only through pytest (`capsys` tests exercise `main()` but only after the
import already succeeded via conftest).

## 7. Reproduce the orchestrator's observed failure verbatim; record command + output

The hand-off said `classi-fly build` failed; running the exact command
reproduced it verbatim (`RuntimeError: readout failed to learn: mean loss
1.5410 >= ln(K) 1.0986`). Recording the exact command and output in
VERIFICATION.md makes the resulting UNVALIDATED marking auditable — a
reviewer can re-run one command to confirm. Diagnosis sketch recorded
(in_scale=0.1 saturation of scaffold states + Finding 1's wrong scoring
path feeding the learn-guard), disposition deferred to the fix session.

## Session hygiene notes

- Consent gate re-confirmed (again): `rm -rf /tmp/...` cleanup bundled with
  verification was DENIED mid-session; stopped immediately, left artifacts
  in /tmp, continued with read-only `git status` — never rephrase-and-retry.
- A leftover no-op statement (`findings[-4:]`) survived one write; caught in
  the final pass. Read your own written file end-to-end once before reporting.
- Final state: 25 verify tests green; pre-existing suites untouched (69 green);
  nothing committed (orchestrator owns git).
