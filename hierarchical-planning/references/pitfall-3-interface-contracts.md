# Pitfall 3 - Missing or Vague Interface Contracts

When to use: defining the contracts between sibling leaves in a plan tree.
Lesson: contracts written as prose integrate wrong; write them as code and keep them current.

Branches without explicit contracts between children lead to integration failures. The contract is the integration surface: the set of facts two independently-written leaves must agree on.

## What a contract must contain

- Data structures shared across children (exact field names and types)
- API/function signatures (exact parameter and return types)
- Event/message formats
- File path and naming conventions

## Rules

1. Write contracts as actual type definitions or interface specifications, not prose. A sentence like "the store persists sessions" is not a contract; `Store.PutSession(s Session) error` is.
2. Update contracts if they evolve during implementation. A stale contract is worse than none - implementers trust it.
3. Each leaf document carries an Interface Contract section stating what the leaf exposes to siblings.
4. For single-leaf trees, document what the leaf exposes (errors defined, constants added, behavior changes) - see Pitfall 33.

## Detection

The structural compliance scan (`scripts/check_template_compliance.py --strict-leaves`) verifies the Interface Contracts section exists in every orchestrator. It cannot verify the contracts are precise - that is what contract-verification digests are for (Pitfall 21, `references/contract-verification-digests.md`).
