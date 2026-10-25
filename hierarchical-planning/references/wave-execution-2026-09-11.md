# Wave execution: contract-only deps, cross-language contracts, deny handling (classi-fly, 2026-09-11)

Four orchestrator-level patterns from a 4-leaf + 3-leaf + verification wave
run on a fresh Go+Python repo. All are additions to the Pitfalls sections of
the parent SKILL.md; kept here for size.

## 1. Contract-only sibling dependencies → RED-BUILD-BLOCKED (collapses waves)

When leaf B depends on leaf A only through a frozen signature (different
files/packages, no shared file edits), do NOT serialize them into two waves.
Brief B with:

- the frozen signatures VERBATIM (inline them; B must not read A's files),
- "author to the contract; if A has not landed when you finish, retry the
  build ONCE, then report RED-BUILD-BLOCKED",
- "never touch A's files or package".

Outcome observed: B and C returned complete-but-uncompilable; both compiled
clean the moment A landed, zero rework of B/C logic. A 3-wave plan ran as
1.5 waves.

Residual cost to plan for: authoring to the right SIGNATURES can still drift
on STRUCT FIELD TYPES. Observed: B's packer built the shared Artifact with
int8 slices + pre-scaled floats; A's owner spec'd float64 arrays (WriteFile
owns quantization). The orchestrator reconciles this mechanically in-session
(~6-line diff) — do not re-dispatch either leaf for it.

## 2. Cross-language binary contracts need a cross-language round-trip test

Frozen byte format, written by Go, read by a Python reference implementation
(offline tooling). Sequence that caught a real bug:

1. Land the Python reader FIRST (wave A), as the contract's independent
   interpretation.
2. Require the Go writer leaf (wave B) to parse its OWN output with the
   Python reader and compare results, not just Go-load what Go wrote.

Bug caught: `Load` read `readout_scale` BEFORE the readout matrix it scales —
a payload-order violation both the Go writer and Go reader agreed on, so a
same-language round-trip passed. Python's independent order exposed it.
Moral: two sides of one implementation share one misreading of a contract;
the independent reader does not.

## 3. Shared scalars across producer/consumer leaves: pin in contracts + carry in the header

A scalar both sides must agree on (observed: `decay`, the tanh leak term —
trainer and runtime recurrence) is a contract, not a default. Pin it in the
orchestrator's Interface Contracts AND make it a field in the artifact
header. When an implementer escalates "action needed: the packer must write
decay" instead of silently defaulting, that is correct behavior — reward it:
edit master.md, then patch the consuming brief. Never let a producer/consumer
pair each invent a default; the failure mode is silent state mismatch, not a
crash.

## 4. Orchestrator verification under standing operator denies

The run had standing denies: dataset downloads, `git rm -r --cached`-style
cleanups, throwaway file creation (context: memory notes say "no compound
cmds; /tmp only" — respect them literally). Even an explicit "execute until
completion, do not require input" did NOT lift them. What passed review
without friction:

- single verification commands: `go test ./... -race -count=N`, `go vet`,
  `gofmt -l`, `python3 -m pytest <dir> -q`, targeted greps;
- inline `python3 - <<'EOF'` numeric probes (accepted).

What got denied: `cat > file <<'EOF'` writing probe test files INTO package
dirs, the 35MB dataset download, the pycache untrack. Correct response when
denied mid-wave: STOP, summarize exact state (which commits landed, which
tests green, the identified one-line fix), hand the user the decision.
Never rephrase-and-retry a denied command, and never treat "autonomous" as
consent for a denied action class.

Related: debugging the failing scaffold (see the parent skill's underdose
pitfall) — the `loss >= ln(K)` guard fired on tanh SATURATION from an
over-strong provisional input projection, not an lr problem; fix the
projection scale, not the head.
