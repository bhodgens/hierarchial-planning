# Frontend Dashboard Plan Tree Pattern

When the plan target is a React (or similar) SPA dashboard embedded in a
backend binary (Go `//go:embed`, Rust `include_dir!`, etc.). Applies to any
frontend with a shared-type + hooks foundation consumed by independent view
components.

## When to Use

The plan builds a dashboard/SPA with these characteristics:
- Multiple independent views (timeline, charts, tables, live feeds)
- Shared foundation: TypeScript types, custom hooks (`useWebSocket`,
  `useApi`), utility functions (color mapping, formatters)
- Backend serves static files via embed; views consume REST + WebSocket
- No external state library (hooks-only state management)

## Decomposition Pattern

### Foundation-First Concurrency

Unlike backend plan trees where modules can often be built in any order,
frontend dashboards have a strict foundation dependency:

```
Group A (sequential prerequisite):
  01-app-shell    ← MUST complete first; all views import its exports

Group B (parallel after A):
  02-timeline
  03-app-breakdown
  04-heatmap
  05-chart
  06-live-feed
  07-summary
```

The foundation leaf (01) creates the project scaffold, shared types,
hooks, utilities, layout shell, AND stub components for every view.
The stubs define the exact prop interfaces that view leaves must match.
This is the binding contract — if a view leaf changes props, it must also
update the shell's `App.tsx` wiring.

### Leaf Sizing

- Foundation leaf: ~70K context (larger than typical — scaffolding +
  hooks + utilities + layout + stubs for all views)
- View leaves: ~40-50K each (one view = one leaf, with its sub-components)

## Contract Definition

For frontend plan trees, the contract is TypeScript types + component prop
interfaces, not Go interfaces or API specs. Define these in the orchestrator's
Interface Contracts section and repeat them in the foundation leaf:

### Orchestrator-level contracts (3 layers):

1. **REST API shapes** — what the backend returns (consumed by `useApi`)
2. **WebSocket frame schema** — frame type discriminator + data shapes
3. **TypeScript type definitions** — mirror the backend's Go types
4. **Shell module exports** — exact function signatures the views import:
   ```typescript
   export function useWebSocket(url: string): { connected, lastFrame }
   export function useApi<T>(url): { data, loading, error, refetch }
   export function getAppColor(bundle: string): string
   export function formatDuration(secs: number): string
   ```

### View leaf contracts:

Each view leaf's "What This Leaf Exposes" section states the exact prop
interface (matching the stub) and the exact file path to modify. The
implementer replaces the stub body; the export signature does NOT change.

## Task Spec Pattern: Actual Code, Not Prose

**Key quality standard (user preference):** For frontend plan trees, each
task must contain actual TSX/TS component code as the implementation spec.
The implementing agent needs:
- Exact component names
- Typed prop interfaces (no `any`)
- API call shapes (fetch URLs, response types)
- WebSocket message handling logic

Do NOT write prose-only tasks like "create a timeline component that shows
sessions." Instead write the full component code in the task's Step 3,
including imports, styled JSX, and event handlers. The implementing agent
copies the code, adapts minor details, and writes tests around it.

### Stub-first approach

The foundation leaf creates minimal stubs for every view:
```tsx
export function TimelineView({ sessions, loading }: TimelineViewProps) {
  return <div>Placeholder</div>
}
```

Each view leaf then replaces the stub body with the full implementation.
The `App.tsx` in the shell imports all views and wires them — this file
is created once in the shell leaf and NOT modified by view leaves (unless
prop interfaces change, which requires a contract amendment).

## Chart Library Decision

For dashboards needing charts, pick the library in the orchestrator and
document the rationale:
- **uPlot** (~35KB): canvas-based, high-performance for time-series,
  best for many data points. Only leaf that needs it installs the dep.
- **Recharts** (~100KB): SVG-based, React-native, easier for simple charts.
- **CSS-only** (0KB): for bar charts, heatmaps, progress indicators.
  Use divs with percentage widths — no library needed.

Prefer CSS-only for simple visualizations (bars, heatmaps, stat cards).
Reserve chart libraries for actual plotted data (line charts, scatter).

## Testing in Frontend Leaves

- Use Vitest + React Testing Library
- Test files alongside source (`*.test.tsx`)
- Mock fetch with `vi.spyOn(globalThis, 'fetch')`
- Mock WebSocket with a `MockWebSocket` class that records instances
- Use `renderHook` from `@testing-library/react` for hook tests
- Set `environment: 'jsdom'` in vitest config for DOM-dependent tests

## Pitfalls Specific to Frontend Plan Trees

1. **Stub prop drift.** If a view leaf changes the prop interface without
   updating `App.tsx`, the build breaks. The orchestrator review must
   verify that every view leaf's exported props match the stub from leaf 01.
   Run `npx tsc --noEmit` after each view leaf review — it catches prop
   mismatches immediately.

2. **Hook dependency cycles.** `useWebSocket` and `useApi` live in the
   shell leaf. If a view leaf needs a new hook, it must either (a) be
   added to the shell leaf (re-dispatch shell), or (b) be local to the
   view leaf's own `hooks/` directory. Document which hooks are shared
   vs view-local in the orchestrator.

3. **CSS class consistency.** With Tailwind, dark theme colors must be
   consistent across views. The orchestrator should specify the palette
   (e.g., "zinc-950 background, zinc-100 text, blue-400 accent") in
   Coding Conventions so all view leaves use the same classes.

4. **Chart library bundle size.** Only install chart libraries in the
   leaf that actually uses them. uPlot in the typing-speed leaf, not in
   the shell. This keeps the foundation leaf buildable without heavy deps.

## Worked Example

AgentAudit Phase 1 MVP dashboard branch (2026-08 session):
- 1 orchestrator + 7 leaves (1 foundation + 6 views)
- Foundation leaf: ~70K context, created Vite project, types, 2 hooks,
  2 utility modules, layout (Sidebar/Header/App), 6 view stubs
- View leaves: 40-50K each, all dispatched in parallel after foundation
  reached REVIEWED
- Compliance scan passed on first authoring pass
- Each leaf contained full TSX component code in task specs
- TypeScript strict mode enforced via orchestrator Coding Conventions
