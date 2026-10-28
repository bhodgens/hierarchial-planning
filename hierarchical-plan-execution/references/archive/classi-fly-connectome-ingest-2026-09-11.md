# Cclassi fly connectome ingest 2026 09 11
When to use: connectome ingest leaf.
Lesson: corpus layout, fixture pinning, ingest-contract verification.

# classi-fly connectome-ingest leaf 02 (2026-09-11) — condensed session bank

Repo: `~/git/classi-fly` — Go runtime (pure-Go reservoir core + `.fly`
artifact) + Python offline tooling under `tools/` (ingest/train/eval).
Plan forest: `plans/classi-fly/` (master.md + SHARED-CONVENTIONS.md +
leaves 01-08). This session implemented leaf 02 (connectome ingest) as
direct implementer; NOT committed (orchestrator owns all git).

## Contract 1 adjacency export (frozen field names, master.md §Interface Contracts)

`{name, neurons, edges, indptr[N+1], indices[E], weights[E] int signed,
source, license, attribution}` — column-oriented CSR; `indptr` length
`neurons+1`; weights carry polarity as sign. The `.fly` packer (leaf
01/02-fly-format) copies these verbatim into the binary container.

## License registry (exact strings — single source: tools/ingest/registry.py)

- **larval** → source `"larval-connectome"`, license `"CC-BY-4.0"`,
  attribution `"Winding et al. 2023, Science 379:eadd9330"` — shippable.
  Data mirror: `github.com/tingshanL/BPU`,
  `data/signed_connectivity_matrix.csv` (~35 MB; stream row-by-row, do
  not slurp into a dense list).
- **hemibrain** → source `"hemibrain"`, license `"CC-BY"`,
  attribution `"Janelia FlyEM Hemibrain (CC-BY)"` — shippable; reached
  via the neuPrint API (neuprint.janelia.org).
- **flywire** → source `"flywire"`, license `"CC-BY-NC-4.0"` —
  NON-COMMERCIAL, benchmark only, never shipped. `guard()` raises
  `NonCommercialError` unless `allow_noncommercial=True`
  (`--allow-noncommercial`; rc=2 with an actionable message otherwise).
  FlyWire covers FAFB/BANC/MCNS/MANC — all benchmark-only per
  RESEARCH.md §4.

## Implemented files (leaf 02, all tests green)

`tools/ingest/{registry,larval,hemibrain,flywire}.py` +
`test_larval.py` + `test_hemibrain.py` + `test_license.py` +
`conftest.py` (sys.path shim for pytest from any cwd). 37 tests pass
via `python3 -m pytest tools/ingest -q`. Design points:

- hemibrain CLI is dry-run by default (rc=0, no file); `--live` issues
  the real neuPrint query. The urllib import is LOCAL to
  `fetch_connectivity` so no test can load it.
- hemibrain transform sorts column indices within each row (CSR
  convention); larval is naturally row-ordered.
- larval CSV handling: labeled (header row + label column) AND bare
  square matrices; header detection = first row's value cells
  non-numeric → skip; integral floats → int; zeros skipped; sign kept;
  non-square/malformed → ValueError.
- Fixtures are inline; no downloads (gated by OPEN-QUESTIONS Q3 +
  owner approval).

## Environment (2026-09-11)

`python3` = 3.14.7 brew (spec says 3.12 — code kept 3.12-compatible),
pytest 9.1.1 present, ruff ABSENT (leaf gate is "clean if present" →
skipped, never installed).

## Deviations / leftover for orchestrator

- Stray file from a crossed write:
  `/Users/caimlas/hrm-sandbox-1759301548447-b4nntk/brainstorm/comfy-mcp`
  (hemibrain-module copy). User DENIED the `rm`; cleanup left to the
  orchestrator. Not inside the repo — no impact on the tree.

## Relevance to remaining leaves

- 03-synthetic-reservoir: emits the same export shape from a seed (a
  "seed" entry will need its own registry row or an extension of
  `registry.py`).
- 04-training: consumes the adjacency export; emits readout export
  `{classes[], W[N][K], bias[K], threshold[K], weight_scale,
  readout_scale}`.
- 06-cli-package: `classi-fly pack` consumes both exports into the
  `.fly` artifact (Contract 1 header field names are frozen there —
  ingest and synthetic must not invent new keys).
- Any future FlyWire-adjacent work MUST go through
  `registry.guard()`; never write a FlyWire export with a shippable
  license string.
