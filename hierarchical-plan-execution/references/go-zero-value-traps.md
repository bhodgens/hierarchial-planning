# Go Zero-Value Traps in Injected Structs

When injecting data into Go structs that were designed to be constructed via a
factory function (e.g. `CreateFact`), watch for fields that default to zero and
silently disable behavior:

## The `ExpiresAt` Trap

`gossip.Fact.ExpiresAt` is `world.GameTime{}` by default — year=0, month=0, day=0.
If a `Fact` is constructed manually (not via `CreateFact`) and `ExpiresAt` is not
set, the `Expired(now)` check compares `now.Year (e.g. 1764) > ExpiresAt.Year (0)`
and returns `true` — the fact is immediately expired.

**Symptom:** Facts register successfully, no errors, but propagation never happens.
The shareable filter silently skips expired facts (rule 2: `fact.Expired(now)`).

**Fix:** Always set `ExpiresAt` to a far-future value when constructing facts manually:
```go
fact := &gossip.Fact{
    ExpiresAt: world.GameTime{Year: 1780, Month: 1, Day: 1},
    // ...
}
```

## The `MaxHops` Trap

`gossip.Fact.MaxHops` defaults to 0. The shareable filter checks
`fact.PropagationDepth >= fact.MaxHops` — with MaxHops=0, even the originating NPC
(PropagationDepth=0) triggers `0 >= 0 → true` and the fact is skipped.

**Symptom:** Same as ExpiresAt — facts exist but never propagate.

**Fix:** Set `MaxHops` to a generous value (e.g. 20 for testing):
```go
fact := &gossip.Fact{
    MaxHops: 20,
    // ...
}
```

## Detection Pattern

When facts register but never appear in shareable lists despite seemingly valid
conditions (compatibility above threshold, NPC knows the fact), suspect a zero-value
field in the shareable filter. The shareable filter has 8 rules — check which one
is silently rejecting the fact by adding a debug print inside `getShareableFacts`.

Real-world discovery: adversarial harness, rebellion-the-game session 2026-07-20.
Facts injected via `InjectFacts` (which called `g.Register` directly, not
`CreateFact`) didn't propagate for hours of debugging. Both `ExpiresAt` and
`MaxHops` were zero.
