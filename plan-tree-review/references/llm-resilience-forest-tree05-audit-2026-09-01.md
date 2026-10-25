# LLM Resilience Forest — Tree 05 (05-catalog) Pre-Dispatch Audit (2026-09-01)

Read-only design review of `docs/plans/llm-resilience-forest/05-catalog/`
(all 4 files: master + 3 leaves) against the meept repo. No repo edits.
Third same-day pass on this forest (tree-04 leaves → root docs → tree 05);
each pass still found fresh majors — sibling-tree/parent-doc cleanliness
never transfers to the next tree.

## Verdict

Structurally sound tree; mostly accurate line-level anchors; **5 MAJOR
factual errors + 4 MINOR** that must be fixed before dispatch. Leaf count
(3 = disk), deps (02 ← {01,03}), tracking tables, status vocabulary, and
the check_template_compliance.py gate all correct.

## MAJOR findings (plan → repo evidence)

### M1. Nonexistent config key `context_window` — actual key is `context_limit`
- Plan: master.md:98 (Contract 3 line 1), 01-context-discovery.md:36
  (precedence rule), :52 (cites "models.go:220 — ModelConfig.ContextWindow
  consumer"), 02-docs-and-config.md:61.
- Repo: `internal/llm/providers.go:51` — `ContextLimit int
  json:"context_limit"` on ModelDef (the models.json5 entry struct).
  ModelConfig (models.go:220) has `ContextLimit`, no ContextWindow field.
  `ContextWindow` exists only on ModelCatalogEntry (models_catalog.go:8,
  static catalog).
- Pattern: HOMONYM TRAP. `context_window` DOES exist in the codebase
  (internal/config/schema.go:981, AmbientExtractionConfig — epistemic
  memory, unrelated subsystem). A naive grep for the plan's name validates
  a false claim. The plan conflated a three-name chain: json5 key
  `context_limit` → catalog field `ContextWindow` → runtime field
  `ContextLimit`.

### M2. Contract names a nonexistent enum value AND contradicts its own sibling rule
- Plan: master.md:83 "AuthType: AuthNone (local)"; 03-lmstudio-provider.md:29
  "no auth (local)"; leaf checklist :152 "field-for-field matches Ollama's
  shape (tested)".
- Repo: `internal/llm/provider_registry.go:54-59` — AuthType consts are
  api_key / oauth_device_code / oauth_external / env only. The Ollama entry
  (:109-117) uses AuthEnvVar with no APIKeyEnvVar.
- Pattern: contract value + copy-this-entry instruction cannot both hold →
  guaranteed implementer improvisation. Fix: AuthEnvVar + unset
  APIKeyEnvVar, or explicitly plan a new AuthNone const and drop
  "field-for-field".

### M3. D12 misstates the Ollama precedent — Ollama has NO discovery in meept
- Plan: DECISIONS.md D12 + master.md:39 "same treatment as Ollama: registry
  entry, discovery, catalog".
- Repo: grep /api/show, /api/tags, any Ollama model-listing across internal/
  → ZERO hits. Ollama today = registry entry (provider_registry.go:109-117)
  + static catalog (models_catalog.go:87-108). The real discovery precedent
  in the repo is PricingSyncer (pricing_sync.go) — which the master's
  Architecture section already cites, so decision text and architecture
  section disagree with each other.
- Pattern: "treat Y like X (which does Z)" is a factual claim about X —
  grep X for Z before leaves inherit the fiction.

### M4. Cited id-validation precedent does not exist
- Plan: 03-lmstudio-provider.md:60-61 "register_local_model.go — id
  sanitization/validation precedent"; master.md:178-181 "sanitize ids into
  the same charset the rest of the catalog uses (grep existing id validation
  in models.go/register_local_model.go)".
- Repo: register_local_model.go has only `localModelKey` (:86-89) — a
  rename transform (TrimSuffix .gguf + Replace "/"→"--"). NO validation
  (no charset check, no `../` rejection). models.go has none either.
- Pattern: "reuse/extend the X precedent" — read X; a same-purpose-but-
  weaker function (transform) masquerades as the cited capability
  (validation). The leaf's hostile-id tests demand real validation; the
  cited precedent to reuse is invented.

### M5. Wrong LM Studio API field name; /v1/models carries no context length
- Plan: 03-lmstudio-provider.md:37-39 "/api/v0/models … richer metadata
  incl. context_length, state"; master.md:29 "/v1/models entries carry
  context length where the loaded model exposes it" (mirrored in D13).
- External evidence (lmstudio.ai/docs REST v0 + SDK list docs):
  /api/v0/models entries carry `max_context_length`; `context_length`
  appears only nested in loaded_instances[].config.context_length. The
  OpenAI-compat /v1/models omits context metadata entirely.
- Pattern: external-provider API claims are verifiable claims. A wrong json
  tag parses silently as zeros — no compile error, and hand-built test
  fixtures encode the same wrong name so tests stay green. Port 1234 and
  the probe-both + tolerate-absence design are otherwise sound.

## MINOR findings

- **m1. llama.cpp fetcher keying + mapping ambiguity.** 01:33,84 keys the
  fetcher "llama-cpp local-models" — the registry id is `local-models`
  (LocalModelsProviderID, register_local_model.go:14); "llama-cpp" is not
  a provider id, so "provider/model" map keys would match nothing. /props
  returns ONE default n_ctx per server while multiple GGUFs merge into one
  endpoint — which model ids receive the value is unspecified; the base
  URL must come from RuntimeManager endpoint resolution, not provider
  config. master.md:27 "per-model via /v1/models metadata where enabled"
  is speculative — llama.cpp's OpenAI list carries none.
- **m2. Doc paths don't exist.** 02:50 `docs/workflows/llm.md` (no such
  file); 02:97 / 03:139 "docs/configuration/ providers page" and master
  Contract 3 "docs/configuration/models page" — provider docs incl. the
  "### Ollama (Local)" section live inside docs/configuration/llm.md
  (~L280). "Modify:" on a nonexistent path is an unforced dispatch
  failure; name the real file or say Create:.
- **m3. Concurrency claim vs leaf reality.** master.md:114-116 says group A
  is parallel because "disjoint files" — but leaf 01 Task 3 creates the
  daemon wiring and leaf 03 Task 3 modifies "the daemon wiring where
  ContextDiscovery constructs" (same file, possibly nonexistent when 03
  runs). Sequence the wiring edit or name the shared file.
- **m4. Unrecorded decision deviation.** Leaf 03 chooses discovery-only
  (no static catalog) vs D12's "…catalog" — defensible (loaded models
  vary) and master endorses it, but nothing tells the orchestrator to
  record the D12 deviation per DECISIONS.md's footer rule. One line in
  master Notes fixes it.

## Clean verifications (checked, no findings)

- Pricing-sync citations exact: openrouterResponse :62, FetchOpenRouter
  :74; OpenRouter URL real (daemon/components.go:660); Sync's
  log-and-continue error tolerance real (:175-199).
- model_picker.go:37 ContextWindow read — exact.
- reasoning_translate.go:65 case list quoted exactly (ProviderIDOllama,
  "qwen", "local", "gala-mlx", "gala-llama").
- /props shape default_generation_settings.n_ctx — real llama.cpp endpoint.
- OpenAI/Anthropic "no context-length API, keep catalog defaults" —
  factually accurate and correctly scoped (D13).
- No second-catalog violation: leaf 03 adds a registry entry to the
  existing mechanism; AGENTS.md:167-169 invariant respected.
- No orphan config fields: leaf 01's llm.context_discovery keys get docs
  in leaf 02 Task 1; leaf 03 adds none. LLMConfig at schema.go:674
  supports the insertion.
- Leaf 03's registry/catalog line cites accurate (:100-120, :17,
  catalog :87-101).
- models.json5 (config/) exists; 355 lines; aliases + slots as documented.
