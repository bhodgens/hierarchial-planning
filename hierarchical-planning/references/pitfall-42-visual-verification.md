# Pitfall 42 - Visual Fixes Require Visual Verification

When to use: fixing visual or spatial issues (model positioning, capsule offsets, animation placement).
Lesson: read actual runtime transforms and verify with screenshots; never guess numbers through guess-test round-trips with the user.

When fixing visual issues, iterative code-guess-test cycles are extremely inefficient. Each round-trip (guess a number - user tests - reports "still wrong") costs 5+ minutes.

## Instead

(a) Use Godot MCP servers to read actual runtime transforms (BodyMesh position, capsule offset, model AABB).
(b) Use computer_use screenshots to verify the visual result.
(c) Calculate the exact offset from real data.

If MCP servers aren't installed, install the Godot AI plugin (`hi-godot/godot-ai` on GitHub - copy `addons/godot_ai` into the project, enable in Project Settings - Plugins). This gives programmatic access to node properties, transforms, and screenshots.

The user's own framing settled this pattern: "would this be something that's done easier visually in godot than having reiterative attempts to 'guess' visual equivalence on your part?" - the answer is yes, always prefer visual verification for spatial/visual fixes.

More Godot-specific execution detail: `references/godot-execution-notes.md`, `references/godot-port-planning.md`.
