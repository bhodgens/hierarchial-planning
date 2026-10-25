# openbot-parity wave-final F.1 — living docs split + lockfile regen (2026-09-10)

Leaf F.1 (plans/openbot-parity/wave-final.md) on humanplusone: docs/ split +
architecture doc + README slim + lockfile regen + doc sweep. No commit. All
gates green at close: control-plane 649 / worker 170 / provisioning 42
passed, `make docs` idempotent, path grep clean, ruff check + format clean,
`pip install --require-hashes --dry-run -r worker/requirements.lock` exit 0.

## What was produced

- `docs/architecture.md` — single current architecture doc (supersedes
  ARCHITECTURE_v2/v3, both deleted): components table (CT 100 control plane /
  CT 200 management / per-client workers / CT 9000 template / host), bridges
  + iptables tables folded from v3, NATS subject table + scoped-token auth,
  provisioning flow (CTID allocated by control plane, passed via --ctid),
  management stack (11 service groups), audit / policy / control-handoff /
  secrets / identity / SPIFFE sections sourced from waves 3–9 code + plan
  docs, mermaid `graph TB` component diagram + `sequenceDiagram` task flow,
  related-docs table.
- `docs/deployment.md` — 9-step bootstrap (host prep → network/firewall/ZFS →
  API token → tofu → management stack → control plane → template → Kuma →
  first client), env prerequisites per step, hardware minimums + UPS/SPOF
  mitigations folded from v3 §5/§7.
- `docs/provisioning.md` — template build, provision flow (9 steps incl.
  nats.conf ERR-trap rollback), dry-run testing, CTID/IP rules (pool 200–353,
  ip = ctid−99, injective because ctids 101–199 alias the same octets; legacy
  101–353 scheme noted as pre-wave-5), plan tiers.
- `docs/worker.md` — runtime + lifecycle, per-role skills table, full tool
  surface (comms/browser/KB/llm/composio/memory/ledger/request_human_help/
  MCP naming + SSRF guard + read-write classification + n8n tag isolation),
  policy gate (per-task fetch, fail-closed), control gate order (policy
  first, 5s memo, fail-open control check), handoff protocol, SVID, value
  ledger.
- README 738 → ~68 lines: intro, quick start, quality-gates table, docs
  table, license note.
- `worker/requirements.lock` +450/−4: 27 new pins (mcp, mcp-types, httpx2,
  httpcore2, spiffe, grpcio, protobuf, cryptography, opentelemetry-api,
  pyjwt, jsonschema set, starlette, uvicorn, sse-starlette,
  python-multipart, truststore, pem, pyasn1(+modules), pycparser, cffi,
  click); control-plane lock byte-unchanged.
- `scripts/gen-lock.sh` — fixed latent path bug (relative pip-compile path
  resolved before per-project `cd`).
- `control-plane/tests/test_docs_freshness.py` — ALLOWLIST_EXACT += MCP_ALLOW_PRIVATE
  (os.environ-read in worker mcp.py), SPIFFE_ENABLED (provisioning operator
  switch → SPIFFE_SOCKET).

## Gate interactions (folded into SKILL.md items 27–28; maintainer detail in
## repo-quality-gates-setup references/docs-freshness-gate.md)

- Route floor: slim README with zero /api/ mentions failed
  test_readme_api_routes_exist_in_app ("matcher regressed?"); ROUTE_RE
  lookbehind rejects `:8001/api/health` (digit before /api/). Fix: live
  route mention in a docs-table cell.
- Env-key test named MCP_ALLOW_PRIVATE + SPIFFE_ENABLED; classified (b) and
  (c) respectively and allowlisted with justification comments.
- Path grep (ad-hoc script, should become gate test #4): caught 5 bare
  module paths (control/audit.py etc. missing src/) and 1 relative
  config/employee-roles.json; all fixed to repo-relative. Note: path test
  passes on `ARCHITECTURE_v3.md §5`-style refs whose target file is deleted.

## Facts folded from v2/v3 before deletion (grep sweep: IP plan, ports,
## NATS subjects)

vmbr0=192.168.1.0/24 on eno1 gw .1 VLAN-aware Caddy-TLS + PVE UI :8006;
5 iptables rules + ip_forward; ZFS datasets (8K clients / 64K mgmt, lz4,
atime=off); hardware minimums 10/25/50 + UPS 1500VA + mitigation table
(UPS+NUT, ZFS mirror, multi-WAN 5G, PBS RTO 1–2h); n8n SUL + Plane AGPL
positions; mgmt CT 8c/16GB; linked clones <5s; model pricing $0.14/$0.28
Flash / $2/$6 Qwen; 3-bridge layout. Deliberately NOT folded: v2 cloud/Orgo/
Activepieces decisions, v3 cost/TCO tables (superseded strategy; business
plan doc remains the pointer).

## Session decisions worth keeping

- Wave-1/leaf-1.2 pattern honored: allowed-scope `rm` executed exactly
  (both ARCHITECTURE files deleted by rm, nothing else).
- 4 pre-existing ruff-format drift files (billing/provisioner/usage/
  test_audit) formatted after `git stash` baseline proved the drift
  pre-dated the session — make ci's format-check would have flagged them
  at the integration gate regardless of ownership.
- Non-Goals honored: no code behavior changes (the 4 format-only diffs +
  test allowlist + gen-lock path fix are the only non-doc edits, each with
  an explicit reason).
- pip-tools installed into root venv (setup-state fix, not captured as a
  constraint).

## Open items for the integration gate / next pass

- `make ci` full run + `make audit-deps` are orchestrator-run (leaf's gate
  section), not run here.
- Path-existence check is ad-hoc; candidate for gate test #4 (skeleton in
  docs-freshness-gate.md).
- `docs/configuration.md` regen included the wave-9 SPIFFE_SOCKET row
  (expected churn; second `make docs` run byte-identical).
