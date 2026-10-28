# Pitfall 9 - Dispatching Leaves One at a Time

When to use: leaves with no dependency between them.
Lesson: batch independent leaves in groups of 3 for concurrent dispatch; sequential dispatch of independent work wastes wall-clock.

Independent leaves should be batched in groups of 3 for concurrent dispatch. Sequential dispatch of independent work wastes time - the whole value of the tree is concurrency.

## Concurrency rules

- Hermes `delegate_task` concurrency is configurable via `delegation.max_concurrent_children` in config.yaml (default 3, can be raised: `hermes config set delegation.max_concurrent_children 6`). Batch independent leaves up to the configured cap.
- Sequential dependencies: wait for the prerequisite to reach COMPLETE before dispatching.
- Maximize parallelism - dispatch all independent leaves immediately.
- Mixed work types (implementation + review + research): use the higher cap - a review subagent is lightweight and does not compete for the same resources as an implementation agent.
- Exception - serialize leaves that edit the same shared file (Pitfall 46) or that are TDD-coupled in the same package (Pitfall 43 class, `references/concurrent-wave-execution.md`).
