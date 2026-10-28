# Porting From a Reference Implementation (Sibling Codebase as the Spec)


When to use: planning a port of behavior that works in another codebase.
Lesson: survey the reference checkout first; freeze reference constants verbatim with citations.
Use when the feature being planned ports behavior that already works in
another codebase — a sibling agent project (Hermes → meept), an upstream
CLI, a previous fork. Observed 2026-08-25 (meept oauth-provider tree:
Hermes device/PKCE flows → meept Go).

## Pattern

1. **Survey the reference checkout BEFORE decomposing.** Locate the
   working implementation with terminal cat/grep on its checkout — never
   read_file (line-number corruption risk), never from memory of "how
   OAuth works".
2. **Freeze reference constants verbatim** in the plan's frozen-contracts
   block, each with a citation:
   `// REF (~/git/<repo>/<file>:<line>): <exact value>`
   Never paraphrase endpoint URLs, scope strings, client IDs, redirect
   URIs, grant types, or header values. They look derivable; they are
   arbitrary. A plan with invented constants compiles clean, passes
   structural review, and can never authenticate.
3. **Read the comment blocks around every constant.** The highest-risk
   contract material lives in reference COMMENTS, not code or prose specs,
   because no design doc mentions it (worked examples below). Grep the
   reference for "rate", "429", "requires", "must", "rejects" near the
   constants you are freezing.
4. **Note flow-shape deviations from the standard.** A "device flow" may
   differ per provider in body encoding (JSON vs form), polling semantics
   (200-only completion vs RFC 8628 error codes), token endpoint
   resolution (fixed vs OIDC discovery), or exchange grant
   (device_code vs authorization_code + returned PKCE verifier). Encode
   the deviation as a FlowKind-style discriminator in the plan rather
   than boolean flags scattered across leaves.
5. **Route the contract-verification digest at the reference checkout,**
   not at a GDD/spec — the sibling source is the binding spec for frozen
   values.

## Worked quirks (OAuth provider class — reusable if touching these flows)

- **Anthropic subscription OAuth (Claude Pro/Max):** the token endpoint
  (`platform.claude.com/v1/oauth/token`, fallback `console.anthropic.com`)
  429-rate-limits any User-Agent starting with `claude-code/`; token
  calls must send an axios-style UA (`axios/1.7.9`). The INFERENCE path
  keeps the `claude-code/` UA + `anthropic-beta: oauth-2025-04-20` — a
  different fingerprint is required there. Client ID
  `9d1c250a-e61b-44d9-88ed-5944d1962f5e`, scopes
  `org:create_api_key user:profile user:inference`.
- **OpenAI Codex device flow:** non-RFC — POST JSON to
  `auth.openai.com/api/accounts/deviceauth/usercode`, poll
  `.../deviceauth/token` where 403/404 mean pending and 200 returns an
  `authorization_code` + `code_verifier` to exchange at
  `auth.openai.com/oauth/token` (authorization_code grant, redirect
  `auth.openai.com/deviceauth/callback`). The usercode endpoint 429s;
  retry honoring Retry-After. Inference at
  `chatgpt.com/backend-api/codex` sits behind Cloudflare that 403s
  non-first-party clients: pin `originator: codex_cli_rs`, a
  codex-shaped User-Agent, and `ChatGPT-Account-ID` from the access-token
  JWT claim `https://api.openai.com/auth`.`chatgpt_account_id`.
- **xAI (SuperGrok):** near-standard RFC 8628 but the device-code request
  must be form-encoded, and the token endpoint is resolved via OIDC
  discovery (`auth.x.ai/.well-known/openid-configuration`). Access tokens
  are short-lived (~6h). Client ID
  `b1a00492-073a-47ea-816f-4c329264a828`, scope
  `openid profile email offline_access grok-cli:access api:access`.

Reference implementation: `~/git/hermes-agent/hermes_cli/auth.py` and
`agent/anthropic_adapter.py`, `agent/auxiliary_client.py` (constants
frozen 2026-08-25; re-verify against the live checkout before executing
a plan that cites them — the reference evolves).
