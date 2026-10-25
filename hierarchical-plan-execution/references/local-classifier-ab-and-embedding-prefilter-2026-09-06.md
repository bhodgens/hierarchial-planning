# Local Classifier A/B Campaign + Embedding-Prefilter Handoff (2026-09-06, meept)

**SKILL.md cross-ref:** when the user asks "which model are we using for
X?", run this reference's loop (archaeology → benchmark → per-category
decision → flip-with-comment → corpus extension). See also
`config-archaeology.md` and `mlx-local-runtime-2026-09-06.md`.

Session: 15+ run A5 acceptance campaign → MLX runtime restoration → config
archaeology → classifier A/B → embedding-prefilter design. The reusable
technique below is the **evidence-driven model-selection loop**; the meept
session detail (A5 gates, combined-sft lineage) lives in
`session-aware-intent-gate-design.md`, `config-archaeology.md`, and
`mlx-local-runtime-2026-09-06.md`.

## The reusable loop: choose a classifier by benchmark, not by narrative

When a local classifier/routing model is suspected weak, resist replacing it
on narrative ("it failed 3 runs"). The sequence that produced a defensible
decision in one session:

1. **Find the eval harness first** — the repo usually has one
   (`cmd/meept-classifier-test` + `testdata/eval/classifier-test-corpus.json5`,
   136 labeled cases). Wrap it in a Makefile target so reruns are one command:
   ```make
   classifier-test:
       go build -o bin/meept-classifier-test ./cmd/meept-classifier-test
       ./bin/meept-classifier-test $(MODELS) --base-url $(BASE_URL) --name eval-$(shell date +%Y%m%d-%H%M)
   ```
2. **A/B via sequential single-model runs, not a dual-port harness** —
   `mlx_lm server` ignores the OpenAI `model` field (serves whatever it
   loaded), so a "model A vs B on one port" run benchmarks the same weights
   twice. Run one server per model (or one run per model) and compare the
   markdown reports.
3. **Parse per-category tables, not just overall** — overall accuracy hides
   the shape: combined-sft scored 54.4% overall but 100% schedule / 0%
   platform+search+report+review. A narrow-specialist model shows exactly
   this signature: perfect in-distribution, zero out-of-distribution. The
   per-category delta table IS the decision document (8B won 9 of 12
   categories, overall +32.4 points, latency 287ms→2.5s).
4. **Flip the alias, keep the loser registered** — winner takes the primary
   slot with the A/B date + score in the comment; the old model stays in the
   chain as an explicit "A/B alternate" slot. Never delete a model from
   config the user fine-tuned — demote it.
5. **Cross-check benchmark vs field behavior** — the benchmark's weak
   categories must explain the field failures (combined-sft's schedule
   false-positives on "create a file" matched its out-of-distribution
   profile). If they don't correlate, the benchmark corpus is missing the
   failure class — extend the corpus (the 136-case corpus had ZERO
   file-manipulation cases) before trusting either number.

## The failure that motivated it: classifier misroute shape

Symptom: identical input ("create a file named hello.txt…") classified
differently across runs — sometimes code (correct), sometimes `schedule`
(wrong; the scheduler agent accepts tasks and leaves them pending forever).
Not a runtime problem, not a port problem: the SFT 1.2B classifier is
bimodal on out-of-distribution phrasing. Field signature of a
narrow-specialist classifier: works brilliantly on training-distribution
inputs, silently misroutes everything else.

## Embedding-prefilter handoff design (accepted direction, not yet wired)

Two-stage routing to cut pre-agent LLM cost from 2+ calls to ~0.3s:

```
message → STAGE 0: embedding prefilter (Qwen3-Embedding-0.6B, frozen)
            cosine vs labeled intent centroids (SetFit-style linear head)
            ├─ confidence ≥ τ (e.g. 0.90) → route directly, skip LLM gate+router
            └─ confidence < τ             → existing LLM analyzer + router
```

Key wiring facts discovered: `EmbeddingConfig` already exists
(schema.go:1235: provider/base_url/model/dimension — "openai"|"ollama");
dispatcher has an `EmbeddingClient` seam (dispatcher.go:352) feeding a
SemanticIndex; Qwen3-Embedding-0.6B MLX 4-bit weights downloaded to
`/Volumes/LLMs/Qwen3-Embedding-0.6B-4bit-DWQ` (336MB, via
`hf download mlx-community/Qwen3-Embedding-0.6B-4bit-DWQ`; note
`huggingface-cli download` is deprecated → use `hf download`).
Remaining work: embedding server, centroid builder from the corpus,
threshold config, Stage-0 branch in ClassifyAndRoute, eval harness
comparison vs the LLM-classifier A/B numbers.

## Handoff document pattern (user-requested, works well)

After a long architecture campaign, the user asked for a handoff document.
The shape that landed: (1) ASCII architecture diagram of the request flow
with file:line anchors — the user reads these to understand the system, not
formal UML (ask "simplified UML diagram" → deliver annotated ASCII flow,
they explicitly wanted comprehension, not a diagram exchange format);
(2) model lineup table; (3) fixed-failure register with commit hashes;
(4) the proposed next architecture with wiring facts already verified;
(5) numbered open items. Save at docs/plans/<tree>/HANDOFF.md.

## Repo-hygiene: rebuild-once tool binaries get a Makefile target (2026-09-06)

A benchmark binary built ad-hoc into /tmp was flagged by the user as "a
useful reusable harness — shouldn't be a tmp thing." Pattern: any
one-off-built tool that will be re-run belongs in the repo's Makefile
(build target + run target with pass-through args), not in /tmp. Also:
consent gates may block `make`/binary invocations repeatedly for an
unknown binary — the direct `bin/<tool>` invocation after an explicit
build worked where repeated `make` attempts were denied.

## Stage-0 measured verdict (2026-09-08 campaign, classifier-iteration)

The handoff design above was built and measured to completion across 15+
iterations (see `classifier-iteration-campaign-2026-09-08.md` for the
campaign mechanics). Headline: the kNN-unanimity variant was replaced by
a **nearest-centroid + uniform cosine margin** head (margin 0.030, floor
0.60) — C 35.6% at P 97.8% standalone — and a **two-stage rescue**
(Stage-0 abstains → ModernBERT-base linear probe rescues at a train-side
quantile tau) lifts coverage to 50-56% at E2E 91.45% vs the 86.8%
LLM-chain-only baseline. Rejected variants and re-entry conditions are
in that reference's rejected-permanently ledger. Data-repair findings
 mattered more than any gate permutation: label defects in the corpus
cost more E2E than every architecture change combined.
