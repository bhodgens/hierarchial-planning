# Go Leaf-Implementer Playbook — Multi-Module Repos (strategist-usa payment-shim tree, 2026-08-25)

Durable lessons from executing leaf `01-foundation/01-processor-interface.md`
(TDD package skeleton: Provider enum, neutral types, 14-method Processor
interface). Applies to ANY leaf dispatched into a multi-module Go monorepo.

## 1. Multi-module Go repos: find the module root BEFORE running anything

The repo root often has NO `go.mod` — each Go tree is its own module:

    strategist-usa/
      pkg/            -> github.com/strategist/pkg       (shared services)
      backend-api/    -> own module
      go-global-runner/, go-web-hooks/, go-shard-runner/, auth/, tools/analyzers/

- First move: `search_files` (or `find`) for `go.mod` from repo root. A leaf
  spec saying "run `go test ./pkg/services/payments/`" is written from the
  ORCHESTRATOR's repo-root perspective and silently fails (`no such package`)
  from the module's own directory — and vice versa. Translate paths to the
  owning module: `go test ./services/payments/` with workdir `.../pkg`.
- Prefer the terminal tool's `workdir` parameter over `cd` chains. Exported
  cwd PERSISTS between terminal calls: a `cd pkg` in call N breaks relative
  `cd pkg` in call N+1 (`cd: pkg: No such file or directory`). Same for
  `go build ./...` — always scope it to the module you're editing.

## 2. RED for compile-time assertion tests is a BUILD failure — that's correct TDD

Interface-definition leaves test via `var _ Processor = fullStub{}` and
struct-literal field access. The RED phase is `undefined: Processor` /
`[build failed]`, NOT an assertion failure. It is still a valid RED:
- Write the stub test first; `go test` shows the build error.
- Bonus: the write_file tool's LSP diagnostics surface the same undefined
  symbols instantly — a zero-cost RED confirmation before spending a test run.
Implement → `go test -v` green → `go vet ./...` → `gofmt -l` (repo gate).

## 3. Contract code block beats prose — implement it verbatim, flag drift in the report

Leaf prose said "14-method Processor interface" while Contract 1's code block
defined `Name()` + 13 methods (14 total — the prose was counting
inclusively). Resolution rule: **the contract code block is authoritative**,
because sibling branches compile against it; prose counts/summaries are not.
Never "fix" the discrepancy by adding or renaming methods — implement the
code block exactly and note the count in the deviation section of your
report so the review agent can confirm zero drift.

## 4. Mirror-type leaves: verify shapes from source, never from memory

When the leaf says "field-for-field mirror of StripeX in <file>:<lines>",
grep/sed the real struct first and copy field names, ORDER, types, and json
tags from the actual source (this session: `StripePaymentIntent`,
`StripeRefund`, `StripeDispute`, `StripeInvoice` in
`pkg/services/stripe_client.go`). Doc-comment each interface method with the
concrete client method it mirrors (grep `^func (c *Client)` for the real
surface — it also catches methods the leaf forgot or invented).

## 5. End-of-leaf git hygiene in a repo with concurrent workstreams

Shared repos routinely show OTHER agents' dirty state. Before reporting:
1. `git status --porcelain` at REPO root (not module dir).
2. Attribute every entry: mine vs pre-existing. This session's status showed
   six modified backend-api files + an audits file from parallel sessions —
   none of the leaf's business.
3. State the separation explicitly in the report ("my only change is the new
   untracked `pkg/services/payments/`") so the orchestrator's review+commit
   step doesn't sweep siblings' files into the leaf's commit.
4. Leaf rules that bear repeating: do NOT commit, do NOT `git add`, do NOT
   re-read files after writing them.

## 6. Context for this tree (payment-processor shim)

- Plan tree: `docs/plans/2026-08-25-payment-processor-shim/` (root
  orchestrator + master.md hold Contracts 1–5).
- Contract 1 landed: `pkg/services/payments/{types,processor}.go` —
  Provider (`stripe`/`hyperswitch`), PaymentIntent/Refund/Dispute/Invoice,
  Processor interface. Downstream leaves (resolver/router, Hyperswitch
  adapter, handler wiring) compile against these signatures — any drift
  breaks branches 02–04.
- Settings-read pattern for the resolver leaf: `SELECT value FROM settings
  WHERE key = $1 LIMIT 1` via pgx (reference: go-shard-runner
  email worker). Fail-closed to `stripe`.
