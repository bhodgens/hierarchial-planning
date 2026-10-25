# Dispatch + Scratch-Rig + MLX Pitfalls (2026-09 meept classifier/quickplan campaign)

Hard-won operational lessons from a multi-tree campaign (quickplan-mode 4 leaves,
allotment 2 leaves, classifier 20 iterations). These apply to any future
hierarchical-plan execution in the meept repo or similar shared-repo Go projects.

## 1. Delegation dispatch pitfalls

- **Line-number corruption**: never feed read_file output into write_file
  (line-number prefixes get baked into the written file). Explore with
  search_files or `terminal cat`; after writing a file do NOT read it back to
  verify — write once and stop.
- **Dispatch context must be SELF-CONTAINED**: subagents have zero session
  memory. Inline into the dispatch context:
  - leaf doc path + current-state deltas (prior leaves' commit SHAs)
  - pinned source regions as GREP ANCHORS, not line numbers (prior leaves
    shift line numbers — "grep func suggestMode" survives, "~line 1251" rots)
  - exact constraints: no commit/no git add, ASCII only, gofmt clean,
    ≤10-line return format
  - for parallel waves: explicit per-leaf FILE OWNERSHIP to prevent two
    writers on one file
- **Async returns re-enter as [ASYNC DELEGATION BATCH COMPLETE] messages**.
  On receipt: re-verify in the parent session — run the tests yourself, check
  `git status` for the claimed files — subagent self-reports are claims, not
  verified facts. Then commit with EXPLICIT paths (shared-repo protocol:
  sibling sessions hold unrelated WIP in the same tree; never `git add .`).
- **Late and duplicate notices are normal.** A leaf whose work you already
  reviewed and committed hours ago can emit its completion notice mid-way
  through a LATER wave. On each notice: check `git log --oneline -- <leaf
  files>` and `git diff HEAD -- <files>` — empty diff = already landed, do
  NOT re-commit or re-dispatch. Three duplicate notices arrived in one
  session, each for work already in a reviewed commit. A straggler's
  summary may also claim "uncommitted residual diffs" that are actually
  someone else's newer WIP — diff against HEAD, not against the
  subagent's memory of its own changes.
- **Subagent "deviations" resolving leaf-prose arithmetic errors are
  usually right** — but verify before folding in. Example: a leaf said
  "window 8192 → batches 3/3/1" for 512-token steps, but 3072 tokens
  fits six; the implementing agent pinned the intended shape with window
  6144 and documented the correction. Fold these into the commit message
  so the leaf doc's bad example is on record as corrected.
- **One subagent's completion notice may arrive AFTER you committed its
  sibling's wave AND after the tree was declared complete** — the notice
  is still just a duplicate if the diff is empty. Confirm with `git log
  --all -- <files>` (the commit may sit on the same branch under a
  different message than the subagent quoted).
- **Per-leaf commit shape**: feat commit for code + separate docs(plan)
  tracking-table commit. Keeps end-of-campaign squash history clean.
- Trailing stale `[IMPORTANT: Background process exited]` notices from old
  failed launches keep arriving after the rig is fixed. Check the CURRENT
  process (pgrep + health endpoint) before treating one as new information.
- ** NEVER write a new master.md into an existing plan directory without
  checking what lives there**: `git log --oneline -1 -- <dir>/master.md`
  plus a read of the file header. A COMPLETE tree from an earlier campaign
  occupied the natural directory name; the write-tool's sibling-modification
  warning is the last-line defense — revert (`git checkout -- <file>`) and
  pick a fresh directory.

## 2. Meept scratch-daemon e2e smoke rig

Config (JSON5 via hujson):
- Quoted keys REQUIRED. Simplest reliable path: write plain JSON via python
  json.dumps — valid JSON is valid JSON5. Watch for double commas after
  programmatic string edits.
- Real transport schema (internal/config/schema.go TransportConfig):
  `transport.http` keys are `enabled / addr / require_auth / api_keys / rest
  / websocket / ws_path / mcp / mcp_path / rate_limit_*` — NOT
  `listen_addr`, NOT `auth: {}`, and there is no top-level `http_transport`.
- **`rest: true` must be set explicitly.** daemon.go copies the config value
  over NewServer's default, and the zero value is false — so omitting `rest`
  disables REST even though DefaultServerConfig() comments say "enabled by
  default". Symptom: /health works but every /api/v1/* route 404s.
- HTTP is ALWAYS TLS: `curl -sk https://...`. Chat endpoint: POST
  `/api/v1/chat` with `{"message", "session_id", "conversation_id"}`.
- Auth: `Authorization: Bearer $(cat ~/.meept/dev_key)`. DevAPIKey() uses
  os.UserHomeDir() and IGNORES MEEPT_HOME — the key comes from the real home
  even in a scratch rig. The legacy literal default key is banned → 418.
- Isolation: `MEEPT_HOME=/tmp/... meept-daemon -f -c /tmp/.../meept.json5`.
  Before picking ports: `lsof -nP -iTCP:<port> -sTCP:LISTEN`. "daemon already
  running (PID x)" means a leftover process holds the socket/rig.
- The daemon ADOPTS an already-listening external model runtime as
  "observed, not owned" — pointing a provider baseURL at the user's live
  runtime (same model) is fine for smokes; drop the `lifecycle` spawn block
  if the port is busy.
- **Rebuild the binary after feature commits.** A stale daemon binary
  silently serves old routes/defaults and masquerades as a config bug.
- Scratch-agent definitions: agents discovery tiers use os.UserHomeDir()
  (real ~/.meept/agents), not MEEPT_HOME — a modified coder AGENT.md placed
  under MEEPT_HOME will NOT be picked up. config/agents resolves via
  resolveBundledPath: CWD first, then exe dir.

## 3. MLX / PyTorch fine-tuning pitfalls (from the classifier campaign)

- **Head-lr underdose**: a fresh linear classification head needs lr ~1e-3;
  reusing the backbone's 2e-5 for the head leaves it at uniform output —
  loss pinned at ln(num_classes), max-softmax ≈ 1/N, "added 0 routes".
  Looks like "training divergent" but is a ~50x underdose. Fix: split head
  vs backbone learning rates (head 1e-3, backbone 2e-5).
- **Train on CPU, not MPS**: PyTorch MPS has documented BERT-family training
  corruption (pytorch#82707 — infinite loss/NaN, degraded metrics vs CPU).
- **Softmax ceiling on tiny data**: 12-class max-prob tops out ~0.21 even
  when correct, so absolute-tau gates (0.7) never fire. Use train-side
  quantile calibration, or relative/agreement gating — a second cheap
  classifier's top-1 agreement veto measurably beat every absolute-threshold
  policy (87.35% vs 84.56% on the gold replay) AND beat the LLM-chain floor.
- ModernBERT small-task fine-tunes from the base checkpoint underperform
  (answerdotai/ModernBERT#225: published numbers train from the MNLI
  mid-checkpoint). Raw ModernBERT embeddings also underperform simple
  centroid-on-domain-embedder gates for short-message intent classification.
- Evaluation discipline that paid off: fixed fold-assignment cache (seed 42),
  silver labels kept SEPARATE from gold until human-adjudicated, and a
  human adjudication sheet (message / model opinion / blank "your label:"
  line) resolved ~35 label disputes and produced normative boundary rules.
- **Small-sample acceptance claims need decomposition scrutiny.** A
  cascade policy scoring 87.35% "above the 86.8% floor" decomposed to
  2 routed cases out of 48 plus 46 × 0.868 chain credit — a 2-case
  effective sample that cannot distinguish a perfect router from a
  coin-flip. When a system score is `(right + n_chain × constant) / tot`,
  always report the ROUTE COUNT and per-route precision alongside the
  headline; one flipped route moved the verdict from "beats the floor"
  to "loses to it" (a sibling reviewer caught this and wrote
  alt-methods-correction.md — the correction-of-record pattern: leave
  the original commit untouched, add a dated correction file).
- **Never claim a measured win without committing the results artifact**
  in the same commit as the claim. Numbers printed to stdout are not
  reproducible from git; an audit wave flagged their absence and forced
  a correction of record.

## 4. User-interaction patterns that worked (meept owner preferences observed)

- "explain like I'm stupid" → plain-language analogy (shower-temperature for
  learning rates) landed well. Numbers in tables, one idea per row.
- Decisions get stated as options with a recommendation, but the user wants
  the DECISION RULES surfaced (e.g. "after the look, what happens?" boundary
  tables), not just verdicts.
- Investigate-first for architecture questions: the user suspects a component
  is over-engineered → trace what exists (grep the real regions), measure the
  alternative on real data, and report which part is actually the gap
  (it was the tactical scheduler's count-based caps, not the classifier).
- When the user corrects a design assumption ("shouldn't the orchestrator
  own planning?" / "quickplan should clarify first"), the correction
  reshapes the spec BEFORE dispatch — restate the corrected design back,
  get the boundary rules settled (a decision table with worked examples
  for each intent boundary), then author the tree. Two rounds of this
  turned a vague "3 stages not 2" into QuickPlan + the outcome loop.
- Status requests after a long autonomous run want a TABLE (process /
  state), a committed-work list with SHAs, and an explicit "nothing needs
  a decision from you right now" — not prose recaps.
- "Are we using X yet?" questions deserve a status answer AND the
  measured overhead of adopting X (train time, model size, per-message
  latency) — the user decides from numbers, and "not yet, but here's
  what adoption costs" is the answer shape that led to a green light.
