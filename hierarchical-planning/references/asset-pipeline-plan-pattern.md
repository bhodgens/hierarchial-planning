# Ops & Asset Pipeline Plan Trees

## When This Pattern Applies

When the plan tree dispatches agents that execute **shell commands, API calls,
web searches, and file downloads** rather than writing code or editing
documents. Examples:

- Asset retrieval (download from public-domain repos, CC0 marketplaces)
- AI asset generation (ComfyUI REST API, trellis2cpp CLI via SSH)
- Data collection / web scraping
- Server provisioning / infra setup
- Model download / dependency installation

The key distinction from code trees: there is no TDD cycle, no `go build`,
no compilation step, and no linting. Verification is "file exists with expected
size and format," not "tests pass."

## Plan Tree Shape

Use the **inline leaf** pattern (forest-scale, §Step 6.6). Each leaf is a
sequence of shell commands and API calls rather than code tasks. Leaves are
still bounded by context (~50-60K for ops, lower than code since there's no
source-file reading overhead).

The dispatcher is an LLM agent with `terminal`, `web_search`, `web_extract`
tools — not `delegate_task` to a coding subagent. The orchestrator (main model)
can dispatch ops leaves directly or via delegate_task with `enabled_toolsets`
narrowed to the tools the leaf actually uses.

## Verification (Replaces TDD)

Instead of "red-green-refactor":

| Code Tree Check | Ops Tree Equivalent |
|----------------|---------------------|
| `go test ./...` | `find <dir> -name "*.ext" \| wc -l` |
| `go vet` | `file <output>` or `identify <image>` (ImageMagick) |
| `golangci-lint run` | `jq '.entries \| keys \| length' manifest.json` |
| Code review | Download, open, or vision_analyze the generated file |
| Commit after review | Commit after human-verification gate (manifest `verified: false`) |

## Manifest Pattern

Ops trees that produce lots of files (assets, images, meshes) should produce a
`manifest.json` at each output directory level tracking:

```json
{
  "directory": "weapons/",
  "collected": "2026-07-21",
  "entries": {
    "ASSET-ID": {
      "filename": "ASSET-ID_descriptive_slug.ext",
      "source": "Smithsonian NMAH",
      "url": "https://...",
      "license": "CC0 / Public Domain",
      "description": "...",
      "verified": false,
      "verified_date": null
    }
  }
}
```

This enables: (a) coverage reporting (N found / N total), (b) human verification
pass later, (c) re-download from URL if file is lost, (d) diffing between runs.

## Tooling Conventions

- **Search:** `web_search` for discovery, `web_extract` for page content
- **Download:** `terminal("curl -L -o ...")` or `terminal("wget -q -O ...")`
- **Remote hosts:** `terminal("ssh host 'command'")` for socrates/remote nodes
- **REST APIs:** `terminal("curl -s http://host:port/endpoint")` (ComfyUI, etc.)
- **API workflows:** Use the relevant skill's run scripts (e.g. comfyui skill's
  `run_workflow.py`) rather than raw curl where a script wraps auth/retry/monitoring

## Worked Example

The `plans-glm/15-assets-retrieval/` and `plans-glm/16-assets-generation/` trees
in the Rebellion project use this pattern:

- Tree #15: 3 leaves, each downloading SEARCHED assets from web + marketplaces
  into `assets/` with per-directory `manifest.json`
- Tree #16: 4 leaves, generating images via ComfyUI REST API on socrates:8188,
  then meshes via ComfyUI Trellis nodes (or trellis2cpp CLI fallback),
  output to `assets/generated/`

Both use inline leaf definitions (~50-60K context per leaf), no TDD cycles,
file-existence verification, and manifest.json tracking.

## Pitfalls Specific to Ops Trees

1. **Rate limits on batch API calls.** ComfyUI processes one job at a time.
   Budget per-generation time in the plan (30s-2min for image-to-3D). Account
   for queue serialization — 26 NPCs × 2 min = ~52 min minimum for meshes alone.

2. **Large binary downloads fail silently.** curl/wget timeout defaults are short.
   Always use `--connect-timeout 30 --max-time 600` for large files. Check
   `Content-Length` header before download, compare to `stat` after.

3. **SSH connection state.** `ssh host 'command'` starts a fresh connection each
   call. For long-running ComfyUI/model operations, use `nohup ... &` on the
   remote and poll with subsequent calls.

4. **Path differences between workstation and remote.** The ComfyUI path on
   socrates (`/home/caimlas/comfyui/ComfyUI/`) differs from the workstation.
   Never assume `~/comfy/ComfyUI/` — probe with `ps aux | grep main.py` first.

5. **Gitignore large generated assets.** Binary files (models, meshes, images)
   should be gitignored and tracked via manifest.json URLs. The repo stays
   small; the files live on disk (pulled on demand).
