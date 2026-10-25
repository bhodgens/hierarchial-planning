# Fresh-Smoke Probe Patterns (runtime/interpreter trees)

Probe families that found real bugs in a Python-runtime tree while every
agent self-suite was green. Adapt the families to any language-runtime or
layered-system tree; the principle is 'derive from spec reasoning the
agent did not use'.

## 1. Feature-resumption families
- Generators: next() past first yield, list(gen), comprehension over gen,
  nested gen, gen inside gen, yield from chains, next() after exhaustion
  (StopIteration), gen closed early.
- Iterators: zip() re-entry, iter() of the same object twice, enumerate
  with start, map/filter chains, manual next() interleaved with for.
- Found here: generator resume dead, iter/gen ID collision capping loops
  at 2 iterations, enumerate start leaking the raw inner iterator.

## 2. Name-resolution families
- Self-recursion (def calling itself), mutual recursion (a->b->a,
  definition order both ways), rebinding a module fn then calling through
  another fn, global VALUE read from nested fn, closure factory returning
  TWO closures sharing a cell, nonlocal counter factory, curried calls
  mk(10)(5) (closure escaping its maker), walrus then read, comprehension
  variable leakage.
- Found here: module fn bound into the wrong scope store (self-recursion
  NameError), cell-classified params never seated into their cells,
  frees not propagated through intermediate scopes.

## 3. Cross-feature interaction families
- Generators inside f-strings (genexpr fields), comprehensions over
  generators, match with or-patterns + guards + capture, unpacking with
  starred targets, try/finally with break, with-statement + exception
  suppression, decorators on generators, class body executed during
  import of the module defining it.
- Found here: break escaping a nested with body, kwargs not flowing into
  builtin-value method calls, dict-comp nested clauses evaluated in the
  wrong frame.

## 4. Alias and lifetime families
- ys = xs; ys.append(...) (shared mutation), self-referential list repr,
  two closures over one cell (shared state), del then read, rebinding a
  global mid-module then calling a fn defined earlier, weakref liveness
  after gc.collect().
- Found here: escaping closures reading empty cells, live classes swept
  by a cycle collector (root-scoping gap), RefCell reentrancy when GC
  triggers mid-mutation.

## 5. Byte-exactness spot checks
- repr of every builtin type incl. edge floats (1e308*10 -> inf, -0.0,
  subnormals 5e-324), str quote selection with both quote types, escapes,
  dict order after delete+reinsert, key collapse (1 / 1.0 / True),
  format specs (nested {x:{w}}, = debug forms, !r/!s/!a), sort stability,
  big-int to decimal string (2**200 * 2**200), floor-div/mod sign matrix.
- Found here: rsplit returning reversed results, missing str %-formatting,
  float repr divergences on subnormals.

## Procedure
1. Write each probe as a standalone program; run against the shipped
   binary AND the reference implementation (python3.14 for this tree).
2. Compare stdout bytes, stderr bytes, exit code separately — a matching
   stdout with wrong exit code is still a failure.
3. Rank DIFFs by how load-bearing the feature is for the target projects
   (generators and method routing before float-format edge cases).
4. Each DIFF: either a fix-pass dispatch with the probe as acceptance
   test, or a documented divergence in the ledger with the blocking leaf.
5. Promote stable probes into the corpus with pinned expected triples
   (stdout/stderr/exit), generated from the reference implementation.
