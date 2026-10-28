# Pitfall 28 - Subagent Code Referencing Undefined Placeholder Functions

When to use: reviewing any subagent-produced code.
Lesson: compile-check IMMEDIATELY, before logic review - the compiler finds undefined references for free.

Subagents sometimes write code that calls helper functions they never define - placeholder names like `mathSqrt()` instead of `math.Sqrt()`, `pkgRand` instead of a package-level `var pkgRand = rand.New(...)`, or invented helpers (`weightedChoice()`, `weightedPickIdx()`) that are referenced but never implemented. This compounds with Pitfall 25 (timeout means the definitions were never written) but is a DISTINCT failure mode even when the subagent does not time out: the subagent may produce syntactically plausible code that simply references symbols it forgot to define.

## Pattern

(a) `find <package> -type f -name "*.go"` to see what landed.
(b) `go build ./<package>/...` to get a list of ALL compile errors at once.
(c) Fix undefined references - often just renaming to stdlib calls or removing dead code.
(d) THEN read for logic/style review.

Do NOT read every file looking for problems the compiler will list for free. The compiler is faster and more reliable than human/agent inspection at finding undefined references.
