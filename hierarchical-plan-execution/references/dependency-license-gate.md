# Dependency License Gate for New Go/Node Dependencies

User rule (binding): GPL/AGPL is acceptable ONLY as a subprocess dep —
never vendored or linked into shipped binaries. Every plan that adds a
dependency must enforce this at leaf level, and the orchestrator must
INDEPENDENTLY verify the license rather than trust the implementing
subagent's word.

## The gate pattern (proven in the 20260905-research-audit-tools tree)

1. **Put the gate in the leaf doc itself**, as a STOP clause on the
   dependency task:

   > READ the LICENSE file in the module cache (go env GOMODCACHE).
   > Expected <license>. If it is GPL/AGPL, STOP immediately and
   > report — do not implement.

2. **Require the license verdict in the leaf's report format** ("LICENSE
   verdict: <spdx>"), so a silent skip is visible at review.

3. **Orchestrator verifies independently at review time** — do not take
   the subagent's word:

   ```
   head -3 $(go env GOMODCACHE)/github.com/<owner>/<repo>@<ver>/LICENSE
   ```

   One command, seconds of cost. Session proof: the excelize BSD-3
   verdict was re-confirmed from the module cache in one line after the
   subagent reported it.

4. **Also verify claimed API drift with `go doc`** the same way. Session
   proof: a subagent reported the brief's library signatures were wrong
   (pdf.NewReader takes io.ReaderAt, Page() returns no error); go doc
   confirmed all three claims in ~30 seconds before the review accepted
   them. Subagent corrections of orchestrator briefs are usually RIGHT —
   but the confirmation is cheap and the failure mode (accepting a wrong
   drift claim that contradicts the frozen contract) is expensive.

## License notes for common Go deps (verified)

- excelize/v2: BSD-3-Clause (link-safe)
- ledongthuc/pdf: MIT (pseudo-version tags are normal for this repo —
  no semver tags exist; @latest resolving to v0.0.0-<date>-<sha> is not
  an error)
- encoding/csv, stdlib: no gate needed

## Where this lives in plan authoring

When authoring with hierarchical-planning: the dependency task in the
leaf gets the STOP clause; the branch orchestrator's Review Checklist
gets "license independently verified from module cache"; the master's
interface contract records the license expectation (e.g. "MIT; if
actually GPL, record actual and STOP").
