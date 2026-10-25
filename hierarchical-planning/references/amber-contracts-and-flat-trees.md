# Amber Contracts + Flat-Tree Scanner Behavior

## Amber contracts (external-protocol plans)

When a plan freezes values from an EXTERNAL spec not read at authoring time (wire-protocol versions, framing style, exact method names published on a spec site), mark them AMBER in the plan:

- Provisional value stated explicitly (e.g. `ProtocolVersion = "1.0" // amber: verify`).
- The FIRST dependent leaf owns verification against the authoritative source (spec site, repo README, published schema files) via web tools — before it implements.
- Verified values get recorded in SHARED-CONVENTIONS.md and the master's contract section is amended; downstream leaves dispatch with the corrected text.
- Never let leaves implement invented constants without that verification step.

This complements contract-verification digests (SKILL.md Review Protocol): digests catch spec-drift POST-authoring; amber contracts prevent it PRE-dispatch.

Worked example (2026-08-28, meept ACP tree `plans/acp-agent-runtime/`): master pinned provisional `ACP_PROTOCOL_VERSION = "1.0"` + newline-delimited framing for the Agent Client Protocol; leaf `02-protocol-types.md` carries an "AMBER CONTRACT — verify before implementing" section requiring verification of version string, framing (newline vs Content-Length), and core method names from agentclientprotocol.com, with SHARED-CONVENTIONS.md §2 as the recording location and downstream leaves consuming method-name constants rather than raw strings.

## Flat trees pass the compliance scanner

A tree authored as master.md + leaf files directly in the tree root (no subdirectories) is valid: the scanner reports a cosmetic `WARNING: no subdirectories found under plans/<tree>` and still returns `ALL TREES COMPLIANT: True`. Do not mint subdirectories just to silence the warning. (Same session, same tree.)

## SKILL.md size note

This SKILL.md is near the 100K patch limit — additional patterns land as reference files in this directory; link them from dispatch contexts rather than growing SKILL.md.
