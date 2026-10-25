# INDEX.md — pointer index (SKILL.md refs line now points here; add new reference entries in this file, not in SKILL.md)

- classi-fly-verification-leaf08-2026-09-11.md — NEW (2026-09-11, classi-fly
  leaf 08 adversarial verification + license audit, direct implementer,
  Python): (1) hand-off "known issue" claims are hypotheses — the
  orchestrator's ridge-orientation bug claim came with an exception
  ("correct only when N == K") that was empirically FALSE (N=K=4: prod 0.75
  vs correct-orientation 1.00; W non-symmetric) — run every boundary case a
  hand-off asserts BEFORE encoding trigger conditions into docs/tests, or
  the verification doc records a fiction and the pin test goes vacuous;
  (2) "verify, don't fix" leaf shape: PIN test asserting the buggy
  signature (with a failure message naming the closure steps) + standalone
  repro script whose exit code INVERTS on fix (0=bug present, 1=fixed) —
  finding closure becomes one command; (3) twin-artifact drift fixtures:
  every byte except the intended difference must match INCLUDING
  reader-derived values (seed-mode input projection is expanded by the
  reader from the RNG — a writer that draws with a different range
  manufactures drift; first attempt measured delta 0.666 from a fixture
  bug, real answer 0.0) — sanity-diff the twins' dequantized projections
  before trusting any drift number; (4) zero committed evidence artifacts
  (results.json) is itself a finding → all real-data verdicts UNVALIDATED
  with per-experiment evidence lines, never manufactured numbers; verify
  the verifier itself with TAMPER tests (cooked headline, lying route
  count, edited stored value must all be flagged); (5) verification tools
  must restate policy independently (never import the producer's
  registry/aggregator) and classify fail-closed (unknown license → not
  shippable; CC-BY without attribution → UNKNOWN; `str(x or "")` for
  optional header fields); (6) CLI entry points bypass conftest sys.path
  shims — modules that run as both test-import and script need a guarded
  `if <path> not in sys.path` bootstrap, caught by running each CLI's
  main() once outside pytest; (7) reproduce the orchestrator's observed
  failure VERBATIM (exact command + output recorded) so UNVALIDATED
  markings are auditable.

- classi-fly-cli-package-leaf06-2026-09-11.md — NEW (2026-09-11, classi-fly
  leaf 06 CLI+packaging, direct implementer, Go): sixth classi-fly session
  ref. (1) MID-SESSION sibling landing — author consumer code to frozen
  contract signatures, expect the landed Artifact shape to differ from the
  leaf-doc sketch (real: float64 pre-quantization arrays + named
  InputMode + embedding-major InW; landed shape wins, re-align call
  sites); sibling files materialize in your package (serve.go) and
  transient build errors from their in-flight edits — identify foreign
  files, poll go build on a 10s loop, never stub/fix sibling symbols;
  grep sibling test funcs for helper-name collisions before writing your
  own. (2) The pack→Load round-trip test is the first REAL producer/
  consumer pair for a frozen container format — caught the sibling's
  Load reading readout_scale BEFORE the readout block (Contract 1 +
  flybytes.py say matrix-first scale-after): diagnose the walk from
  reader source, confirm your own bytes via the independent Python
  reader, report, don't mirror their bug; same-day report:
  train_readout.py consumes ridge_fit's W[N][K] as class-major (only
  correct when K==N). (3) stdlib flag vs `cmd path --flag value` syntax:
  reorder BEFORE Parse and make it VALUE-AWARE — a flag's value doesn't
  start with '-', so naive positional-detection eats `--embedding
  0.5,0.25`'s value; build the value-taking map via fs.VisitAll +
  IsBoolFlag(). (4) Contract-3 exports lack embed_dim/steps/input-
  projection → pack takes a third --pack JSON block as a documented
  extension (bridge the gap, name it, never rename frozen fields). (5)
  Landed Artifact.InW is DEQUANTIZED (byte × in_scale) — WriteFile
  requantizes v/InScale, raw bytes → int8-range failure; scales =
  max|v|/127 floored 1e-6, readout_scale taken verbatim from the export.
  (6) build packs a provisional matrix-mode .fly (trainer rejects seed
  mode) then repacks after training; scaffold fixture: the 6-variant
  lane-rotation scheme trains, single-direction/amplitude schemes FAIL
  the learn-guard (sub-saturated tanh states are collinear) — don't
  beautify a working fixture without re-running e2e. (7) Verbatim-header
  `info` over a parsed-only API: framing-only reader + byte-identity
  test. (8) Consent gate re-confirmed: /tmp cleanup rm -rf denied —
  separate commands, leave evidence, mention once.

- classi-fly-flyformat-go-2026-09-11.md — NEW (2026-09-11, classi-fly leaf
  01-reservoir-core/02-fly-format, Go producer/runtime side of Contract 1:
  internal/flyformat container+header, reservoir Artifact/WriteFile/Load/
  Classify/Info; -race -count=10 green, cross-language interop proven):
  landed consumers are the normative tiebreaker when contract PROSE
  contradicts landed code (memo said in_w[i*D+j]; all three Python readers
  are embedding-major in_w[j*N+i] — grep their unpack_from/reshape and match
  byte-for-byte); cross-language bug arbitration (Go test failed vs
  expectation → ran the same quantized arrays through landed states.py →
  Python reproduced the "wrong" answer → implementation bug, not fixture);
  Contract 1 readout order matrix-FIRST scale-AFTER needs buffering, and the
  transposed variant shows NO length-field garbage — only wrong winners with
  plausible probabilities, so the independent-reference run is the detector;
  sibling WIP caller (leaf 06 pack.go, untracked) assumed int8/float32/uint8
  Artifact shape — contract owner keeps the spec shape (WriteFile owns
  quantization per Task 4 tolerance doc) and flags the ~6-line caller
  adaptation; seed-vs-matrix win layout (Classify dispatches on
  len(win)==n*len(embedding) or panics); decay header extension landed
  (omitempty, (0,1) validated, Load defaults 0.8) closing leaf04's contract
  gap; klauspost/compress v1.20 facts (EncodeAll single-return, NewWriter(nil)
  for EncodeAll, no WithDecoderCRC); fixture micro-pitfalls (int8 scale
  sizing, modulo precedence panic, n*d loop bound, noisy filler keeps softmax
  competitors alive); consent-gate: verification and scratch cleanup must be
  SEPARATE commands (a test rerun bundled with rm -rf /tmp was denied — stop,
  leave artifacts, mention once).

- classi-fly-training-leaf04-2026-09-11.md — NEW (2026-09-11, classi-fly
  leaf 04 readout trainer, direct implementer, Python): third classi-fly
  session ref (02 ingest, 05 eval-harness reader; 04 built the Contract 1
  fixture WRITER since the Go packer doesn't exist yet). Lessons:
  hand-computed golden vectors are not goldens — the implementer's hand
  tanh-chain dropped the recursive term (0.2925 vs true 0.8049); compute
  goldens with a throwaway independent script and paste the repr,
  arbitrating code-vs-expectation disagreements with it first
  (implementer-time twin of verify-with-your-own-golden.md); Contract 1
  field-order transposition signature — garbage in a length field that
  decodes as your actual payload bytes (16973061 = 0x01030505 = the in_w
  bytes) = reader layout written from memory instead of the contract
  text; bytes(list) rejects negative int8 → struct.pack("<%db");
  zstd dual-path upgrade (3.14 stdlib compression.zstd → zstandard →
  pyzstd → raw, frame-magic auto-detect); quantile calibrate semantics
  (lowest own-score quantile meeting target lane precision, FP =
  other-class rows crossing; contamination must sit inside the class's
  own score band to raise a threshold); CONTRACT GAP for leaf 06 —
  frozen header has no decay field but the recurrence needs one, packer
  must write a decay header extension (trainer: header → kwarg →
  DEFAULT_DECAY=0.8).

- classi-fly-eval-harness-2026-09-11.md — NEW (2026-09-11, classi-fly leaf 05
  eval harness, direct implementer, Python): consuming a frozen binary
  artifact format whose PRODUCER doesn't exist yet — fixture-grade reader of
  the exact Contract 1 layout (FLYRES01 magic, CSR, int8 projection/readout,
  f32 bias+thresholds, trailing-bytes check) mirroring Contract 2 Classify
  semantics, documented as the harness's REFERENCE forward pass; dual-path
  zstd reader (decompress only if `zstandard` importable; committed fixture
  stored uncompressed, named deviation); fixture tuning that makes tanh
  lanes saturate (in_scale 0.25 × int8 12 → coordinate at 12.0, weight_scale
  0.5); deterministic-credit protocol enforcement (CHAIN_BASELINE=0.868
  named constant, E2E recomputed independently in tests, OOD scored not
  skipped, route count disclosed in table+headline+results.json, sha256-only
  text in predictions); consent-gate variant: a CLI invocation with an
  embedded http:// URL arg is denied as a network probe and an IDENTICAL
  retry trips the tool-loop guard — park the command for the orchestrator
  and point at the test-proven e2e path instead.

- classi-fly-connectome-ingest-2026-09-11.md — NEW (2026-09-11, classi-fly
  leaf 02, direct implementer, Python): condensed project bank for the
  classi-fly plan forest — frozen Contract 1 adjacency-export field names
  {name, neurons, edges, indptr, indices, weights, source, license,
  attribution}, the exact license-registry strings (larval CC-BY-4.0
  Winding 2023 / hemibrain CC-BY FlyEM / flywire CC-BY-NC-4.0
  benchmark-only via registry.guard()), CSR design points, env facts
  (python3.14 + pytest 9.1.1 + ruff absent → skip), stray-file deviation
  left for the orchestrator, and per-leaf relevance (03-synthetic needs a
  registry row; 04-training's readout export; 06 packer consumes both).
  Python mechanics (conftest sys.path shim, crossed-write detection via
  write-result lint, --live network gating) live in the Python addendum
  of direct-single-leaf-execution.md.

- orchestrator-committed-leaf-during-execution.md — NEW (2026-09-10, meept
  outcome-loop leaf 01, direct implementer): the orchestrator committed the
  leaf MID-EXECUTION from the same session's stream — dispatch found its
  work already on HEAD, identical design, ~35 min after dispatch start.
  New attribution class between sibling-commit-sweep (commit contains only
  YOUR files, message names your leaf — not foreign) and phantom commit
  (disk matches HEAD because HEAD IS the work). Triage protocol: verify
  sha+stat, diff your leaf paths vs HEAD, classify residual hunks
  (hardening/deviation/divergence), report dual provenance, never
  re-land. Includes: residual-diff hardening pass (INSERT column removal,
  ASCII sweep of YOUR files, spec self-conflict regex bridging — leaf's
  own test case is normative over its prose), scoped stash A/B warning
  (HEAD alone may not compile on sibling-WIP branches — A/B/A the failing
  tests instead), and parallel-load full-suite flakes (two consecutive
  green focused reruns = flake).

- classifier-campaign-2026-09.md — NEW (2026-09-09, meept quickplan-mode +
  classifier-campaign session): (1) meept hujson scratch-config authoring:
  ALL keys must be quoted (inline `{ enabled: true }` fails too — quote
  with `([{,]\s*)(\w+)(\s*:)`, not a ^-anchored pass); `transport.http.rest`
  is a BOOL and daemon.go OVERWRITES DefaultServerConfig() with the config
  value, so an omitted key = REST routes 404 despite "default true"
  comments; dev API key lives at real ~/.meept/dev_key (os.UserHomeDir,
  NOT MEEPT_HOME) — scratch-daemon smokes read that for the Bearer token;
  404-with-CORS-headers = auth passed/RESTEnabled false, 404-without-CORS
  = mux-level miss. (2) Agent-definition overrides: discovery tiers use
  os.UserHomeDir (real ~/.meept/agents), NOT MEEPT_HOME — per-scratch
  agent overrides need config/agents copied into the daemon CWD
  (resolveBundledPath stats CWD first) or a user-tier write (ask first);
  `max_conversation_tokens` frontmatter key merges via
  mergeAgentDefinition when > 0; the coder-died-at-50k signature means
  the budget never got raised. (3) Fine-tune diagnosis protocol: flat
  loss at exactly ln(K) + uniform predictions = optimization underdose,
  not feature poverty — check head lr (1e-3, not 2e-5 = 50x underdose)
  and run a one-fold forced-route probe (forced acc >> chance proves
  features) BEFORE retraining; quantile tau beats fixed tau for
  tiny-data softmax heads; CPU over MPS for training. (4) QuickPlan
  adjudicated semantics (normative): review-and-correct (autonomous) =
  quickplan; verdict-only no-changes = review; execute-existing-plan =
  quickplan; "help me..." = quickplan signal; research = survey without
  testable criteria vs analyze = judged against criteria; quickplan
  requires an orchestration-cue regex guard (session-state signal, not
  message-text decidable). (5) B-route policy sweeps: matrix of tau x
  guard (cue/conf/cue-or-conf) over cached embeddings — converts
  subjective guard choice into a table; the winning policy in iter-20 was
  tau 0.152 + conf-guard 0.15. (6) Capability-aware allotment tree
  authored (docs/plans/allotment/): tactical scheduler is COUNT-capped
  only — nothing reads the executor model's context window; the window
  source already exists (llm.Resolver ResolveRef → ModelConfig.ContextLimit,
  fed by models.json5 + ContextDiscovery). User's double-confidence gate
  (both stages > 0.7) ADOPTED: 84.56% vs 83.97%, simpler, and correctly
  zeroes B-rescue while its precision sits below the chain.

- openbot-parity-campaign-shape.md — NEW (2026-09, humanplusone openbot-parity
  campaign, 10 issues → 9 waves → 16 leaves; EXTENDED 2026-09-09 with leaf-side
  lessons from wave 3 leaf 3.1): CAMPAIGN SHAPE for issue-batch
  plans — one master.md + one wave file per dependency tier (no branch
  orchestrators; the wave file IS the dispatch context). Key additions over
  plain trees: (1) FROZEN CONTRACTS at planning time — exact SQL DDL, JSON
  payload shapes, replacement-format strings, and naming conventions for
  anything two waves share (audit_log table, redaction scrubber output,
  policy JSON), numbered Contract A/B/C so leaves reference rather than
  restate; (2) frozen-signature placeholder bodies — when wave N needs a
  function wave N+1 fully implements, wave N creates the module with the
  frozen signature + pass-through body + `# wave-N+1 replaces` marker
  (signature lands once, body swaps, zero rework); (3) duplicated-by-design
  worker twins — vendor a mirror module with `# vendored mirror of
  control.<mod> — keep in sync` and duplicate test fixtures rather than
  cross-package imports; (4) shared-file region ownership written at PLAN
  time ("own ONLY the 2 router-include lines"), because the wave author sees
  all waves' claims at once; (5) verification bars for leaves whose stacks
  can't run in the leaf env (GH Actions/SPIRE/n8n): YAML-parse + SHA-pin
  regex + referenced-targets-exist checks, with live verification deferred
  to the wave gate and the leaf doc saying so — never let a leaf claim
  "CI works" when it can only claim "CI file is valid"; (6) master wave
  table carries a WHY column per tier so mid-campaign repriorization has a
  safety-reference. Leaf 3.1 extension: exact-set sibling test assertions are
  coupled to your leaf (grep the registry surface, e.g. `get_jobs`, in tests/
  before final green); byte-cap truncation guarantees valid UTF-8 not
  parseable JSON (orphan-lead-byte trim); "reuse const X" satisfied by equal
  value → land a new named const and record the deviation; format-gate
  attribution by tool version — a newer ruff flags pre-2025-formatted sibling
  files as pre-existing drift, scope the FORMAT gate to the leaf's own file
  list, keep lint repo-wide. Leaf 5b 5.3 extension (worker PolicyGate +
  policy/audit routes, 2026-09-09): contract fallback literals must pass the
  campaign's own validator (deny-default doc lacks `version` → worker
  normalizes the exact literal at the fetch boundary, strict validation for
  real docs — planner rule: run contract literals through the sibling
  validator at PLANNING time); fail-closed fallbacks MASK wire-shape
  mismatches (parse the shape the contract TEXT names; happy-path tests
  assert policy CONTENT, deny-outcome-only tests pass vacuously on an
  always-deny gate); per-task refresh gates need sync + awaitable entries
  (sync-only refresh() under a running loop races its own fetch task);
  pytest-asyncio mode is PER-PACKAGE (worker has no asyncio_mode → STRICT →
  explicit `@pytest.mark.asyncio`; control-plane's asyncio_mode=auto does
  not transfer); vendored-twin drift guard asserts mirror == header +
  control_source with the sibling tree path-resolved inside the guard test
  (bare equality fails on the mandated banner; import-path pollution breaks
  sibling tests); audit-ingest tenant binding deliberately asymmetric vs
  task-result (unknown client ACCEPTED — the deny trail survives stale
  workers; task-result 404s because its rows drive usage/value).

- classifier-iteration-campaign-2026-09-08.md — NEW (2026-09-08, meept
  classifier-iteration master.md campaign, 14 iterations in one session;
  EXTENDED same session iters 15+ — divergent-fine-tune diagnosis
  protocol, research→retrain recipe, brew half-install/metadata-husk
  repair): CAMPAIGN MECHANICS for multi-iteration eval campaigns
  (companion to local-classifier-ab... which covers model selection). (1)
  Iteration 1 is BASELINE RECONCILIATION — the plan's asserted baseline
  (C 14.7%) matched only a warm-index self-included protocol; honest
  5-fold was 3.7%; annotate the log row + write a delta report before any
  improvement claims or every delta is measured against fiction. (2)
  Compaction-proof state = master plan + one-row-per-iteration log +
  results/iter-N/report.md; mechanical sweeps in-session over a disk
  embedding cache, subagents only for judgment work; fold-assignment
  cache is campaign state — COMMIT it (user ordered results/ + fold
  cache un-ignored via .gitignore negation). (3) Corpus-growth iterations
  mechanically dip E2E (new cases enter TEST folds before their index
  contribution lands) — read the precision-compliant frontier, not raw
  E2E deltas. (4) Data repair beats gate tuning: two label repairs gave
  +2.0 E2E vs +1.1 from ALL head/embedder permutations combined. (5)
  Harness bug classes: fitted heads get GLOBAL case indices while the
  index matrix is fold-local (use a module-level full view), OOD rows
  must never enter the train index or OOD-R is fake, and GPU fine-tunes
  need a sanity gate — check loss vs ln(n_classes) + confidence
  distribution before trusting a tau sweep (this session's fine-tune
  never trained: loss flat at ln(12), confidence uniform 1/12). (6)
  Rejected-permanently ledger with re-entry conditions (instruction
  prefix, k-majority, logistic, per-class margins, two-stage, length
  floors, raw ModernBERT) so future sessions don't re-test. (7) Iter-15
  addendum: when a fine-tune diverges, the user's directive is research →
  retrain → reattempt (not abandon) — arithmetic-first diagnosis (lr ×
  steps vs zero-init head = the 50x underdose signature), cheap
  falsification probe (linear probe at head-appropriate lr proves/
  disproves feature quality in minutes), quantile tau instead of fixed
  tau for tiny-data softmax heads, CPU over MPS for training. Same
  architecture went from "0 routes added" to the campaign's best config
  (C 56.4%, E2E 91.45%). Same-session extension iters 16-18 + audit:
  (8) never sample Bernoulli draws for expected-credit metrics — a seeded
  0.868 draw realized 89.9% and manufactured a false "clears bar"
  headline; an external audit sibling recomputed deterministically from
  committed per-stage counts and superseded the verdict in the shared
  ITERATION-LOG (re-read shared logs before every patch). (9)
  real-transcript silver validation protocol: harvest user messages from
  Hermes session JSONs into an UNTRACKED corpus (gitignore-before-commit
  — ignore rules don't untrack; the adjudication sheet committed then
  needed git rm --cached), deployment-shape validation (train on all
  gold, test on held-out silver), and the canonical finding: synthetic
  92.8% did NOT transfer (silver 84.7% < the 86.8% chain floor) because
  of TAXONOMY gaps, not gate defects. (10) label quality caps
  measurement — after a wave fixes one boundary, flat silver E2E means
  adjudicate the silver labels (cascade-vs-label disagreement sheet,
  disagreements sorted first) before more anchor waves. (11) user
  architecture directive: 3-stage cheapest-first cascade scored on
  AGGREGATE system accuracy; per-stage precision floors match it; a
  global-P≥97% constraint is unsatisfiable once the chain is a stage.
  (12) user concepts queued: per-stage ≥30% correct-route share;
  `quick_plan` mode (plan+execute, no approval loop) as a dispatcher
  MODE triggered only by explicit phrasing — parked behind
  adjudication.

- local-classifier-ab-and-embedding-prefilter-2026-09-06.md — NEW (2026-09-06,
  meept classifier-observability + MLX restoration): the evidence-driven
  model-selection loop for local classifier/routing models. (1) Config
  archaeology first (what was chosen vs what migrated). (2) If an in-repo
  eval harness exists (cmd/meept-classifier-test + 136-case labeled corpus),
  wrap it in a Makefile target and A/B candidates via SEQUENTIAL single-model
  runs — `mlx_lm server` ignores the OpenAI model field, so one-port
  dual-model runs benchmark the same weights twice. (3) Decide on
  per-category deltas, not overall: narrow-specialist signature is 100%
  in-distribution / 0% elsewhere (combined-sft: 100% schedule, 0% platform/
  search/report/review, 54.4% overall vs 8B MLX 86.8% — overall hid a 32-point
  gap). (4) Flip the alias with the A/B date+score in the comment; demote the
  loser to an explicit alternate slot; never delete a user-fine-tuned model.
  (5) Extend the corpus if its categories don't cover the observed field
  failure (zero file-manipulation cases). Also: the accepted SetFit-style
  embedding-prefilter Stage-0 design (Qwen3-Embedding-0.6B MLX 4-bit at
  /Volumes/LLMs, ~0.3s gate before the LLM analyzer; EmbeddingConfig at
  schema.go:1235 + dispatcher EmbeddingClient seam are the wiring points;
  `hf download` not the deprecated `huggingface-cli download`), the
  user-requested HANDOFF.md pattern (ASCII flow diagram with file:line
  anchors, model table, fixed-failure register, verified next architecture,
  numbered open items — saved at docs/plans/<tree>/HANDOFF.md), and the
  Makefile-target pattern for one-off tool binaries a user flags as
  reusable ("should we save this? this sounds like a useful reusable
  harness" = build+run Makefile target, not a /tmp binary).

- templates/scratch-daemon-config.json5 — NEW (2026-09-07): minimal
  scratch-daemon config template paired with live-tool-path-smoke.md
  (socket + data_dir + the transcript/summarize gates); substitute the
  placeholders, copy models.json5 and config/{agents,skills} into the
  scratch layout (CWD-first resolution means no config/ dir = no
  custom agent roster).

- live-tool-path-smoke.md — NEW (2026-09-07, meept transcript chain live
  smoke; EXTENDED same session with the fifth layer + watchdog rescue):
  a green tool unit suite proves the TOOL, not the PATH. The first live
  run exposed FIVE stacked defects, one per layer above the tool: (1)
  LLM classifier misrouted a YouTube-URL request to coder (no grant) —
  fix: deterministic media_url_guard ahead of the LLM classifier for
  structural input patterns; (2) ToolActionMap lacked the tool →
  "Unknown action" denial — a seeded security rule and an action-map
  entry are TWO separate registrations, neither automatic (except when
  seed-rule Action == tool name, where the fallback resolves by naming
  luck); (3) indexed schema mode stubbed the tool to a one-liner with
  an EMPTY parameter schema → model called with no args — multi-param
  tools cannot live behind indexed mode, add to
  DefaultAlwaysFullTools(); (4) the embedded python script targeted the
  pre-1.0 API while fake-runner tests are API-shape-agnostic by design
  — embedded scripts need a real-subprocess probe test or their drift
  is invisible until production; (5) DEEPEST: the LFM2.5 marker-recovery
  shim was wired only in the non-streaming Chat path, but the agent
  loop ALWAYS streams — any response-recovery shim must be applied to
  EVERY transport variant (Chat + doStreamRequest), and the
  reasoning-only watchdog now runs one disable-thinking rescue turn
  before terminating (thinking-mode local models put the whole reply in
  reasoning_content; retrying unchanged re-fails identically). Includes
  the layer-isolation probe pattern (direct-LLM probe with the exact
  registry schema, direct-tool probe with the real runner, daemon-log
  layer evidence) and scratch-daemon env gotchas (pip --user installs
  are $HOME-dependent; agent-spec resolution is CWD-first so scratch
  daemons see no custom roster; stale smoke binary; session persistence
  across restarts resumes stale strategy; a live TOOL-path smoke needs
  a model that can emit tool-call JSON; smoke debris removal is
  consent-gated — leave it, name it, hand the rm to the user; the user
  may flip model slots between runs — pin smoke expectations to the
  scratch config copy).

- live-seal-validation-and-revision-deadlock.md — NEW (2026-09-07, meept
  plan-compiler live validation): (1) a tree whose deliverable is a NEW
  user pipeline (opt-in flag → CLI → RPC → existing executor) is not done
  at suite-green — budget one live smoke with the orchestrator playing the
  user; proved the problems-as-result seal UX and caught a real deadlock
  the integration tests couldn't see. (2) Reviewer-revision deadlock
  signature: original step stuck `reviewing` + created revision `pending`
  depending on it = silent stall with no error; reconstruct via log
  timestamp → sqlite row states; fix = guarded re-write of SetState after
  revision creation + never revise FAILED steps (fail them outright).
  (3) Any pipeline handing off to an EXISTING subsystem should live-test
  one forced-rejection scenario. (4) Forensics discipline: write the
  event sequence down once instead of looping greps; sqlite rows over
  CLI views; log-timestamp ↔ DB updated_at correlation.

- meept-tool-result-ceilings.md — EXTENDED (2026-09-06, tool-result-budget
  tree): what shipped against the caps — ResultSizer floor interface
  (cap in the loop, not the helper: import cycle), the CRITICAL rule
  that a budget value's DESTRUCTIVE consumer (compressionPipeline
  rewrites result.Result) is the binding wiring site and nil-pipeline
  test harnesses make it unobservable, deterministic metadata-preserving
  compressMapResult, slices sized to the 600-tok floor, and two
  test-observability traps (json marshal sorts keys → sorted-order
  assertions pass vacuously; ToCompressedJSON's 200-char wrapper
  reserve breaks naive budget math; m["output"]-only extraction
  asymmetry).

## References directory index (2026-09-06 addition, tool-result-budget tree execution)

- reviewing-parallel-tool-leaves.md — EXTENDED (§6.1-§6.3, from the
  tool-result-budget tree): (1) a value with MULTIPLE consumers (the
  compression pipeline AND ToCompressedJSON both consume the result
  budget; the pipeline DESTRUCTIVELY rewrites result.Result) must have
  the new behavior wired at the destructive consumer too — leaf wired
  only the read-side one and the harness couldn't catch it because it
  ran with compressionPipeline==nil; when claiming budget/cap coverage,
  state which consumers the harness exercises. (2) Spec test assertions
  must be OBSERVABLE: encoding/json sorts map keys on marshal, so
  "assert sorted emission order" passes vacuously — replaced with
  tight-budget byte-identical x100 + all-keys-present assertions; also
  ToCompressedJSON's ~200-char wrapper reserve broke the spec's
  example arithmetic (fix the example, implement the intent, record
  under Deviations). (3) New sibling-sweep variant: the sweep landed
  while the orchestrator's own commit was in flight and PARTITIONED the
  leaf's files across two commits — on an unexpectedly-short commit,
  `git log --all -- <missing files>` first; content-verify, cite both
  shas, never re-land.

## References directory index (2026-09-06 addition, plan-compiler tree orchestration)

- verify-with-your-own-golden.md — NEW (2026-09-06, orchestrator-side,
  meept plan-compiler tree): when a tree has a shared NORMATIVE document
  (dialect spec, wire format) and ≥2 leaves implement different sides of
  it (compiler/renderer, producer/consumer), each leaf's own tests only
  prove code-agrees-with-tests — a shared misreading of the spec passes
  every leaf test. At review time, before committing either leaf,
  extract one normative example from the spec VERBATIM (python fence
  extraction), feed it through one implementation as a temporary
  in-package `zz_*_test.go` probe asserting the SPEC-stated outcomes,
  delete in the follow-up command, and record "orchestrator golden
  check against spec §N: PASS" in the tracking table. Worked: spec 8.1
  example compiled first-run through the freshly landed compiler.

## References directory index (2026-09-06 addition, plan-compiler leaf 03)

- leaf-spec-conflicts-and-sibling-red-build.md — NEW (2026-09-06, meept
  plan-compiler leaf 03 EmitTree, direct single-leaf implementer role while
  sibling leaf 02 was IN FLIGHT): (1) exact-line section-presence scans
  (sectionPresent pins bare `## <name>`) force BARE headings — house
  decorations like `(frozen)`/`(root)`/`(From Parent)` move into body text,
  or the pinned test list fails; grep the leaf's pinned section list FIRST
  for any emitter/doc-generator. (2) Hand-simulate sizing/partition formulas
  against EVERY pinned case before implementing — the leaf pinned
  "2 steps, cap 3 ⇒ FLAT" which the literal ceil share formula contradicts
  (⌈2/3⌉=1 < 2 ⇒ "tree"); consistent resolution: gate fits = steps ≤ cap,
  partition share = min(n, ceil(n/cap)); fixture leaf-counts come from the
  formula, not intuition. (3) Sibling's RED test file (types declared in
  test, impl not yet landed) breaks the whole-package build with ONLY
  `undefined: <pinned-type>` errors — verify own code via gofmt syntax
  check + LSP diagnostics filtered to sibling-symbol undefineds (go build
  stays authoritative; LSP was observed STALE once this session), then
  bounded-poll for the sibling's file and close with a blocked-leaf report
  (verbatim build output IS the evidence; unblock condition names the
  sibling's missing file). (4) Do NOT build an out-of-repo /tmp overlay
  sandbox with stub types to unblock — consent-denied command class; the
  static checks plus the blocked-run report are the honest path.

## References directory index (2026-09-06 addition, tool-result-budget tree wave-A review)

- self-poisoning-test-fixtures.md — NEW (2026-09-06, found during
  transcript-large-corpus wave-A review): a test fixture that temp-dirs
  a component's ROOT but not $HOME lets $HOME-derived default resolution
  (UserHomeDir-walking tier discovery) seed a fixture-named artifact
  into the USER'S REAL tree; resolution then prefers the real-tier seed
  forever — the test fails permanently on every later run ("path should
  mention <tmpdir>"). Two-phase poisoning (seed passes, lock-in fails)
  makes it look flaky/random. Fix: `t.Setenv("HOME", dir)` in the
  fixture helper BEFORE the component's first operation (lazy discovery
  built on sync.Once exists precisely for this). Detection checklist:
  grep the component for UserHomeDir/Join(home, treat plausible
  product-name fixtures as collision-prone, baseline with git stash to
  attribute pre-existing vs wave-caused, hand the real-tree debris rm to
  the user.

## References directory index (2026-09-06 addition, transcript-large-corpus tree)

- branch-switch-mid-tree-reconciliation.md — NEW (2026-09-06, meept
  transcript-large-corpus tree): a sibling session switched the SHARED
  checkout from main to a feature branch MID-TREE (between waves); all
  four leaf commits landed there. Protocol: never checkout back while
  the sibling may hold in-flight tracked edits (git status --short
  tracked-files check first); map topology with double-dot logs;
  cherry-pick ONLY your own commits onto main in original order; RE-RUN
  the integration gate on main (gate results don't transfer across
  bases); leave duplicates on the sibling branch and note them. Same
  reference: (2) pre-commit analyzer gates blocking on files you never
  touched — sibling-staged index state drags committed packages into
  scope; commit by EXPLICIT PATH and never unstage the sibling's files.
  (3) Subagent "not committed" reports going stale — a sibling swept the
  leaf's working-tree output into its own commit minutes later; diff
  the landed sha against the subagent's file list, adopt when content
  matches, record the true hash in the tracking table. (4) rm cleanup
  stays consent-gated for the orchestrator even after verbal user
  approval — hand the exact commands to the user in the report, list
  scratch paths under Observations, no alternate-route attempts.

## References directory index (2026-09-06 addition, tokscale-ingest retention leaf)

- config-gate-wrong-reason-red.md — NEW (2026-09-06, meept tokscale-ingest
  leaf 02 retention test): TDD RED fails at the CONTROL assertion, not the
  target one — the behavior under test is behind a zero-value config gate
  (`if s.retentionDays > 0`) and the test-store helper omitted
  `RetentionDays`, so the constructor (which does NOT apply the package
  default; only `DefaultStoreConfig()` does) silently no-op'd the whole
  purge block. Rule: RED must fail at the TARGET assertion with the
  expected message; a control/setup failure first means fix test setup
  (explicit package-default constant), re-run RED, THEN implement.
  Recipe + triage steps in the reference. See also
  references/go-zero-value-traps.md.

## References directory index (2026-09-06 addition, dependency-visibility tree execution)

- leaf-verbatim-contract-messages.md — NEW (2026-09-06, dependency-visibility
  leaf 03/01): when a contract quotes an EXACT failure message, the
  executor's error-wrapper formatting (`skill %q: %s`) silently breaks
  byte-exactness while `strings.Contains` tests stay green. Fix: additive
  unexported `raw` field on the wrapper (empty = legacy formatting) +
  full-string EQUALITY test, never Contains. Same leaf: contract file-lists
  can be wrong about struct location (`type Skill struct` lived in types.go,
  not the named skill_parser.go — grep the SYMBOL before trusting the file
  list), and named func types take plain-nil guards (the AGENTS.md
  typed-nil ritual is for *ConcreteType-in-interface, not func values).

- SKILL.md (2026-09-06) — two new sections from the dependency-visibility
  tree: (1) "Leaf-side consent denials propagate" — a denied command in a
  leaf report is a user decision about that command CLASS; re-attempting it
  orchestrator-side burns a denial and a stall; verify statically + cite
  leaf evidence instead (complements §16 in
  pitfall-sibling-commit-sweep-and-scratch-module.md). (2) "Drift-audit
  dispatch contexts pay for themselves" — 10-minute pre-Wave grep + go doc
  pass found 3 stale leaf claims (kardianos EnvVars, executor.go:215,
  Makefile:254); folded into dispatches = zero re-dispatches all tree.
- pitfall-sibling-commit-sweep-and-scratch-module.md — EXTENDED §15
  refinement: the commit-sweep race is not limited to hook-blocked commits;
  a parallel session can sweep mid-review. Verify content-correctness of
  each swept hunk, record dual-hash provenance in tracking tables, and do
  NOT cherry-pick/revert for cosmetic regrouping when content is verified.

## References directory index (2026-09-06 addition, skill-authoring-and-media-ingest integration review)

- reviewing-parallel-tool-leaves.md — NEW (2026-09-06, orchestrator-side
  review adjudications from a 4-leaf parallel wave into one Go package):
  (1) sibling error-style split (`nil, err` vs `tools.NewErrorResult`) —
  count both styles, trace the ONE consumer funnel (Registry.Execute
  converges them on ToolResult{Success:false}), approve both as established
  patterns; unification demands are scope churn. (2) `_ = ctx` trips the
  ignored-error pre-commit gate — replace with a why-unused comment, not a
  nolint. (3) config-path drift variant: `cfg.Tools.Transcript` invented;
  no Tools struct exists — grep the sibling section ([browser]) and mirror
  its real shape (top-level + DefaultXConfig + frozen DefaultConfig
  defaults). (4) denied rm of leaf scratch dirs: surface + Observations +
  hand the user the cleanup command; the orchestrator is bound by the same
  no-delete denial as the leaf, and untracked scratch packages still
  compile into ./... gates (exclude explicitly from attribution).
  EXTENDED same day (§5, post-tree review + fix wave): the in-session
  review finds seams that green leaf tests miss — grep the delivered
  producer→consumer CHAIN after the tree closes. Real cases: WriteSkill
  didn't Register into the registry, so same-session create→patch failed
  (the leaf-05 wiring test MASKED it by hand-registering the skill — a
  test that hand-feeds its dependency hides exactly that gap); a tool's
  effective output bound is min(tool cap, agent-loop per-result token
  cap) so size-bounded tools need pagination params (offset/max_chars +
  total_chars) from day one; length-derived flags must be computed
  BEFORE suffix mutation. Fix dispatch: parallel subagents batched by
  file ownership; a sibling session may commit your fix subagent's
  working-tree output under its own message (verify content, cite the
  sha, skip re-landing); commit by EXPLICIT PATH when sibling-staged
  foreign files drag already-committed packages into pre-commit analyzer
  scope. EXTENDED AGAIN (§6, user's architecture-limit question): a tool
  cap review stops one layer short — the real bound is min(tool cap,
  3000-tok per-result cap, DECAYING dynamicToolBudget toward 600 tok,
  30k iteration window, 50k turn budget), each clipping independently.
  Decaying-budget failure modes: paginated offsets computed from clipped
  text skip the tail forever; order-dependent non-determinism;
  compressMapResult random key order randomly drops metadata (the model
  loses `path`, keeps `timestamps`); late-turn verification reads most
  degraded. Fixes: ResultSizer declared floors (Categorizer pattern),
  deterministic metadata-preserving compressMapResult, skill slices
  sized to the 600-tok floor. User-preferred shape for bulk content:
  route AROUND the conversation (file-backed output_path + file_read
  paging; local-summarizer digest via the existing SummarizerClient
  chain) — never raise the caps, the caps are correct.

## References directory index (2026-09-06 addition, skill-authoring-and-media-ingest leaf 05)

- leaf-doc-contract-drift.md — UPDATED (2026-09-06): NEW **drift class 5,
  structural-ordering claims**: leaf prose asserting execution order
  ("register at the END of initializeSkills") with line-number anchors can
  be flatly false — initializeSkills, the SkillWriter assignment, and
  registerBuiltinTools all lived inside ONE function (NewComponents), so
  execution order = file order and the leaf's preferred site would have
  injected a NIL writer. Protocol: find each anchor's ENCLOSING function
  (grep ^func, take the last at-or-before the anchor), derive order from
  call structure or a wiring test, and treat the leaf's Notes fallback
  clause ("ONLY with test evidence") as the tiebreaker. Plus two hygiene
  rules: prove handle-liveness FUNCTIONALLY in wiring tests (execute the
  tool end-to-end through the real writer/registry; nil handles fail with
  their own "unavailable" error before doing work), and attribute gofmt -l
  findings against the HEAD blob before reformatting (identical deltas =
  pre-existing debt; a leaf must not reformat sibling/legacy hunks).

## References directory index (2026-09-05 addition, phase-frontier-parallel leaf 03)

- verify-only-contracts-and-slot-parallelization.md — NEW (2026-09-05, meept
  phase-frontier-parallel leaf 03): (1) "VERIFY, don't rebuild" contract
  tasks can genuinely FAIL verification — write the regression test first
  and watch it fail (a stamp-based start needs `state==pending && stamp==""`
  as its not-started guard; a state-only guard re-starts live phases); when
  verification exposes a bug inside the leaf's file scope, fix minimally
  and promote it to the top of the completion report, never weaken the
  test. (2) Single-slot → parallel-safe migration recipe (selectedPhases
  map + idempotent-per-key select + RecordUsage routing key + SUM-semantics
  accessors + explicit-from AdvancePhaseFrom; legacy AdvancePhase delegates
  with serial-only resolution — never resolve the from-key by map iteration
  order under parallel selection, a wrong guess teleports budget between
  live phases). (3) In fan-out dispatch tables, count "once per X" PER-X,
  not per-operation; derive table expectations from the multi-actor
  semantics, and remember table assertions run before the case's later
  steps. (4) Whole-file test rewrites reintroduce transcription bugs
  (`%%`→`%` escape loss caught by vet); patch-append big test files instead.

## References directory index (2026-09-06 additions, classifier-observability tree + run-10 forensics)

- forensic-run-attribution.md — NEW (2026-09-06, meept session-aware-intent-gate
  leaf 03 + classifier-observability tree): the recipe for overturning a wrong
  failure attribution before writing fixes. 13 e2e runs were attributed to a
  "zai 429 quota window"; read-only forensics on ONE kept workdir found ZERO
  429s — the real chain was: local fallback "empty content" → alias rotation →
  SHARED classifier client silently re-pointed → router scored a concrete
  create-file request as intent=platform confidence=1.0 (reply = capabilities
  dump); clarifications were SUCCESSFUL weak-model verdicts (0.6-0.9), not
  errors. Rule: after ~3 consecutive externally-attributed FAILs, dispatch a
  read-only forensics subagent (daemon.log timeline + sqlite state DBs + actual
  reply files) with "document what the artifacts show, don't assume the
  orchestrator's premise." Also: confirm the e2e binary mtime postdates fix
  commits before crediting/blaming a mid-campaign fix. Companion lesson:
  assert-heuristics that fail ANY reply containing '?' will fail correct
  answers that also offer follow-up help — check artifact reference first.

## References directory index (2026-09-05 additions, research-audit-tools xlsx leaf)

- leaf-brief-external-api-drift.md — NEW (2026-09-05, meept
  research-audit-tools 03-spreadsheet xlsx leaf): leaf briefs citing an
  EXTERNAL dependency's API from memory get signatures wrong by omitting
  error returns — and TDD makes the TESTS inherit the drift before the
  brief's own "verify API from source" task runs. Rules: run go doc for
  every external function the test cases touch BEFORE writing the test
  file; treat sentinel-value returns as the dangerous variant (excelize
  GetSheetIndex returns -1 with NIL error for a missing sheet → an
  err-only existence check compiles and spins forever; the symptom
  signature is a test that HANGS, not fails); when a brief's concrete
  row/cell expectation conflicts with the contract's index semantics,
  pin the test to the contract (neighbor-relative assertions) and
  comment the index→row mapping; a parallel sibling's shared file
  becomes read-only to you once the canonical definition lands, even if
  it looks broken mid-edit — poll the package build green instead of
  "fixing" their file.

## References directory index (2026-09-05 additions, session-aware-intent-gate tree)

- session-aware-intent-gate-design.md — NEW (2026-09-05, meept
  session-aware-intent-gate tree): the reference implementation for
  context-conditioned ambiguity gating. Design per the user's
  architecture principle: user-addressed agents (intent analyzer) QUERY
  session state at turn time (SessionContextDigest from
  GetTasksForSession + terminal step Result + last intent); the session
  never absorbs worker-loop transcripts beyond the final summary.
  Analyzer gets a [Recent session activity] block + two
  context-conditioned ambiguity rules; contextless turns are
  byte-identical (wire-proven via httptest capture). Testing pattern
  for concrete *llm.Client fields (not stubdable): factor
  message-building into an unexported helper for hermetic unit tests +
  httptest wire proof, and use the dispatcher's real analyzer seam
  (ClassifierClient) for integration. Deliberate non-goals: no
  threshold change, no keyword lists, no config.

## References directory index (2026-09-04 addition, e2e scratch-daemon leaf consolidated)

- e2e-scratch-daemon-leaf.md — NEW (2026-09-04, consolidated from two
  sessions of live-e2e leaf work; overlaps and supersedes the run-by-run
  detail in live-e2e-leaves-and-gate-attribution.md): budget 3-6 script
  bugs across 4-8 runs on first live exercise; macOS /var→/private/var
  dual-path allow patterns (compute WORK_RESOLVED via pwd -P, allow both
  forms — EvalSymlinks'd deny paths defeat single-form globs); null-list
  JSON endpoints (`data.get("k") or []` or the parser crash misclassifies
  as provider failure); feature gates create rosters (`specs=0` in the
  log = missing config gate in scratch config, not a broken daemon);
  lazy conversation IDs (chat RPCs accept bare conv IDs without creating a
  session row — sqlite the scratch DB before writing discovery logic);
  canned replies = a gate ABOVE the agent (grep the reply template in Go
  source: a hit means no LLM ever saw the history); sqlite forensics
  before blaming code under test; guard escape hatches must not bypass
  unambiguous markers (absolute trigger for `## Available Agents`); STOP-
  clause integrity (verify upstream deps forensically, then commit the
  tightened assertion as documentation of the real gap); reliability
  gates need two consecutive provider-available green runs.

## References directory index (2026-09-04 addition, session-continuity leaf 03)

- fallback-model-masquerade.md — NEW (2026-09-04, meept session-continuity
  leaf 03): how a provider quota window makes a live e2e suite FAIL like a
  product regression — daemon records 429s as assistant replies or re-routes
  to the small local model which ANSWERS, so honest-SKIP never fires and
  assertions fail on canned fallback boilerplate. Includes the
  forensics-before-STOP protocol (--keep workdir → sqlite session_messages
  dump proves deps landed independently of reply quality → daemon.log 429/
  fallback attribution → grep the reply template in Go source: a hit means
  a daemon gate produced the reply and no LLM ever saw the restored
  history), the three-way disposition (deps broken / window degraded /
  pre-existing gate behavior needing a follow-up leaf), and the real case:
  A5's STOP clause tripped on a provider-live run while leaves 01/02 were
  proven good — culprit was dispatcher.go buildClarificationResult firing
  before the chat agent.

## References directory index (2026-09-04 addition, live-e2e leaves + gate attribution)

- live-e2e-leaves-and-gate-attribution.md — NEW (2026-09-04,
  chat-dispatch-ux leaf 10 + integration gate): (1) live-E2E leaves
  iterate 3-5 script bugs on first real runs — the four that recurred:
  `set -u` unbound vars masquerading as provider SKIPs (classify
  crashes as FATAL), minimal scratch configs omitting behavior-gating
  flags (multiagent.enabled gate → "no agent available" looks like a
  provider problem), session-ID discovery vs lazy bare conversation
  IDs (daemon processed oneshot_responses without creating a row —
  check what the path keys on before writing discovery logic), and
  macOS /var→/private/var symlinks defeating single-form allow-path
  globs (allow both `$WORK/**` and `$(cd "$WORK" && pwd -P)/**`).
  Plus the non-negotiables: FATAL on broken build (never stale
  binary), honest SKIP with printed reason never reachable from a
  script bug, and STOP-not-weaken when a should-pass assertion still
  fails. (2) Integration-gate lint findings attributed per-line via
  `git log -L` — sibling/pre-tree debt recorded and skipped, only
  findings on lines your commits introduced are blockers (zero here;
  repo-wide modernize-50/staticcheck-45 was parallel-session debt).
  (3) Companion lesson from the same tree: heuristic guard escape
  hatches (prose-ratio bypass on a catalog guard) get bypassed by
  model output wrapped in legitimate-looking prose — tighten flaky
  leaks to absolute triggers on unambiguous markers + named regression
  test case (meept commit 26f276fd).

## References directory index (2026-09-04 additions, chat-dispatch-ux execution + integration gates)

- integration-gate-lint-attribution.md — NEW (2026-09-04, integration
  gate of chat-dispatch-ux): when `make lint-ci` fails at the gate in a
  repo with sibling sessions, attribute every finding in tree-touched
  files via `git log -L <line>,<line>:<file>` / `-S snippet` to its
  introducing commit before fixing anything. Introducing commit is yours
  → fix now; a sibling's or pre-tree → leave for the owner and document
  in the completion report. Large category totals (modernize 50,
  staticcheck 45) are repo-wide parallel-session debt, not this tree's
  regression — the gate holds the tree only for NEW findings inside hunks
  its own commits added. Also records the gate ORDER learned here:
  generated-docs regen AFTER the last code commit, then suites
  (-count=1, -p 2), then analyzers.

## References directory index (2026-09-04 additions, chat-dispatch-ux tree, wave 2)

- orchestrated-leaf-commit-hygiene.md — NEW (2026-09-04, same tree): the
  ORCHESTRATOR-side commit discipline this parallel wave proved out:
  same-file leaves (04/06 on components.go, 05/07 on loop.go) dispatched
  strictly sequentially with "leaf NN just landed, commit <sha>, relocate
  via grep" timing notes in the dispatch context; committing a leaf whose
  file carries OTHER sessions' uncommitted hunks (sibling bughunt
  self-fixes interleaved in loop.go) = commit together + name the origin
  in the commit message ("flag loudly, never sweep silently"); pre-commit
  hooks that build the whole repo fail on sibling WIP — bypass via
  `git -c core.hooksPath=/dev/null` ONLY after manual package
  verification, with the bypass + reason recorded in the commit body;
  authoring-time line anchors drift across the session's own commits
  (components.go:1422 wiring site → registry constructed at :2251, nil at
  :1422) — tell implementers to relocate via grep and accept
  deviation-note site changes (two implementers found real improvements:
  nil at the pinned site; CWD lives in DetectionContext.CWD, not a
  top-level field); flaky suite FAILs under parallel load → rerun twice
  before treating as real, record the call in the tracking table.

## References directory index (2026-09-04 additions, chat-dispatch-ux tree)

- chat-harness-ux-comparison.md — NEW (2026-09-04, meept-vs-hermes
  naive-user comparison): the recipe that GENERATED a plan tree — roleplay
  a non-technical user through an identical transcript on your product and
  a reference harness, same model both sides, sandboxed cwd, evidence from
  the session DB + daemon log (not just the CLI), re-run turn 1 three times
  (output variation = finding). Includes the assertion contract (no task-ID
  stubs, claims match disk, failures state harness cause, continuity,
  destructive-action hygiene) and the transcript-failure → file:line
  pipeline-defect mapping that became docs/plans/chat-dispatch-ux.

## References directory index (2026-09-02 additions, llm-resilience-forest follow-up wave)

- parallel-sibling-forest-execution.md — UPDATED (2026-09-02): new
  "Follow-up close-out wave" section — the completion report's follow-up
  items became a second dispatch wave: slow-suite de-flake via the
  already-shipped test-only config seam (grep for a seam the tree landed
  BEFORE inventing injected-clock machinery; 308s → 14s), dose-response
  discipline for resource-bound flakes (unbounded → -p 4 → -p 2, ladder
  recorded in the fix comment; full-sweep verification in background with
  notify; expect one transient flake per sweep even at a good bound), and
  reviewing `git status` after a subagent completes (it may leave an
  uncommitted companion test worth committing under your own message).

## References directory index (2026-09-01 additions, llm-resilience-forest)

- parallel-sibling-forest-execution.md — NEW (2026-09-01, meept
  llm-resilience-forest): executing a plan forest alongside PARALLEL
  SIBLING SESSIONS that are executing the same forest. Verify-before-
  reimplement dispatch framing ("if already implemented, verify and
  report, change nothing" — all three such dispatches returned correctly
  with zero changes), dirty-file fences vs sibling WIP, dispatch order
  from the LIVE dependency graph not plan numbering, claiming untouched
  leaves the sibling skipped, honoring sibling-written gates, verifying
  sibling-landed leaves with the same review gates (caught a real
  pre-existing infinite-rotation-retry bug pre-commit), stale sibling
  tracking tables reconciled from git history, pre-commit hook sweeping
  sibling WIP into your commit, and long-test verification patterns
  (background terminal + -run filters when a sibling's WIP may break the
  package build).

## References directory index (2026-09-01 additions, skill-evolver re-review)

- sequential-file-edit-clobber.md — NEW (2026-09-01): two sequential content
  replacements on one file inside a single script; the second rewrite uses a
  stale pre-first-edit read and silently reverts the first fix. One mutation
  per script per file; verify intended bytes on disk before dependent
  changes; prefer anchored patches over whole-file writes for multi-hunk work.
- phase2-tree-execution-2026-09-01.md — NEW (2026-09-01, meept-bench phase-2
  wave-tree): disjoint file-ownership partitioning across 9 leaves (zero
  collisions); per-leaf review outcomes incl. two accepted contract
  deviations (diff TaskDiff needs endpoint wall/cost fields, not bare deltas;
  harness tasks dropped `expect_agent` under classifier outage); known-failure
  task semantics under a diff gate (fail→fail = unchanged, gap fix = FIXED
  signal); environment-coupled routing flakiness (classifier alias chain down
  ⇒ keyword-fallback misroutes — `expect_agent` belongs only where dispatch
  IS the contract); user-denied-probe protocol (stop the probe class,
  substitute log/file evidence, record leftover artifacts and ask once);
  per-leaf `--out` isolation so parallel live-daemon runs don't overwrite
  each other's transcripts.
- store-split-plan-visibility.md — NEW (2026-09-01): a correctly-introduced
  dedicated sink store makes artifacts invisible to user surfaces built on
  the shared store — the original dead end reborn at the CLI/RPC layer.
  Detection checklist, minimal fix shape (optional fallback manager+store on
  the handler, daemon wires it, list-union dedupe), and gotchas: managers
  may lack listing (inject store separately), nullableString stores ''
  as NULL breaking `WHERE col=''` list queries, approve-then-Synthesize
  advancing state past 'approved'.

## Existing index (pre-2026-09-01)

- leaf-sizing-and-timeouts.md
- multi-agent-contention.md
- leaf-verification-fallbacks.md
- leaf-spec-drift-line-refs.md
- leaf-testability-seams.md — NEW (2026-08-25): making legacy handlers testable in leaves — one-method interface narrowing of concrete deps, override-var fallback seam, body-context stubbing, HMAC signature test matrix, normalization-map table tests, JobID/dedupe convention tests.
- multi-session-repo-hazards.md — UPDATED (2026-08-25, oauth tree): NEW H6 pre-commit hook blockers (staticcheck scans whole staged package; interactive feature-docs tty prompt — fix is to write the real docs/workflows/<pkg>.md; parallel-WIP build breakage → park-in-/tmp-commit-restore pattern), H7 mandatory `git diff --cached --name-only` index check before EVERY leaf commit (foreign files get pre-staged by failed attempts or sibling `git add -A`; a graphs-only commit shipped 799 lines of a sibling's modelstore.go), H8 subagent hard-death (429 with zero files) vs timeout-stall (files on disk).
- subagent-rate-limit-mitigation.md — UPDATED (2026-08-31): distinguishes per-minute 429 (stagger+retry) from 5-hour usage-window exhaustion (check disk first, salvage in-session, never re-dispatch into the window); track which mode killed each agent.
- machine-artifacts-in-repo.md — NEW (2026-08-31): a product daemon with CWD inside the repo writes generated files into the tree — ID-format fingerprinting to find the writer, session-search blind spot for non-chat processes, cp+git-rm-cached migration to a user-scoped sink, expect mid-migration regeneration.
- pitfall-sibling-git-restore-revert.md — NEW (2026-09-01, skill-evolver tree): a still-running sibling leaf's mis-scoped `git restore` reverted a COMPLETED leaf's tracked-file work. Survival asymmetry (untracked new files survive; tracked diffs die), detection via mtime clustering + symbol-grep flip, the commit-each-green-leaf rule, explicit git-path prohibitions in every leaf brief, and recovery from the delegation cache instead of re-dispatch. COMPANION: pitfall-leaf-reverts-sibling-work.md (same tree, different actor) — the reverting agent was a FINISHED leaf doing "workspace cleanup" of another leaf's files it misread as broken; it confessed in its report ("restored... to HEAD") and had saved the diff to /tmp. Covers the brief-side prohibition, the detection signature (reports saying "restored... to HEAD" about non-owned files = destruction confession), commit-each-green-leaf discipline, and recovery via `git apply --3way` + re-authoring from the dead leaf's cached report. Also: orchestrator in-session fixes to leaf-owned files are revert targets until committed.
- leaf-spec-gate-polarity.md — NEW (2026-09-01): leaf-authoring bug where a contract's gate predicate pointed opposite to the producer's selection predicate (`effectiveness >= T` gate fed by an `effectiveness < T` selector) — internally consistent, fully tested, and would have killed the pipeline in production. Rule: derive confirm-gate polarity from the selector, cite both predicates with file:line in the leaf doc, grep the producer before dispatching any >= / < contract. UPDATED (2026-09-01 re-review wave): gate fixtures and polarity corrections needed re-verification after a sibling revert destroyed the first fix — polarity checks belong in the RE-REVIEW checklist too, not just authoring.
- adversarial-re-review-of-committed-work.md — NEW (2026-09-01): post-landing re-review pattern from the skill-evolver tree. Scope carve-up across three parallel reviewers (leaf-pair correctness / cross-leaf wiring / integration+CLI-visibility), fix authority in every brief, and the key trick: reviewing COMMITTED state is immune to the sibling-revert class and leaves reviewer fixes as the only dirty files. Attacks library that caught real issues: provenance stripping on approval rewrite, driver-specific SQLite DSN pragmas silently ignored, store-split visibility (dedicated sink store invisible to shared-store CLI surfaces), WriteSkill tier split-brain trace.
