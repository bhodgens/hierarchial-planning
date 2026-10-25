# Scratch-daemon e2e smoke harness (quickplan/prefilter)

Run three e2e smokes against an isolated scratch meept daemon:

1. **quickplan** — cue-bearing review-and-fix request must reach the
   coder and produce a report with no clarification gate.
2. **ambiguity** — underspecified request ("fix it") must trigger a
   clarification request.
3. **fallback** — gibberish longer than the short-simple guard must fall
   through to the chain (chat-style response is correct for content-free
   input).

Prerequisites (checked by the script):
- scratch meept-daemon binary (build: `go build -o /tmp/qp-meept-daemon ./cmd/meept-daemon`)
- scratch config (meept.json5, ports remapped off the live daemon: HTTP 18096, RPC socket in the scratch home, no lifecycle block)
- embedding prefilter server on :8090 (scripts/embed_server.py, our instance)
- live or scratch LLM runtime on :8082 (LFM2.5-8B)
- dev key: real ~/.meept/dev_key (os.UserHomeDir, NOT MEEPT_HOME — the
  daemon's auth middleware falls back to it when api_keys is empty)

Gotchas baked in:
- hujson needs ALL object keys quoted (inline `{ enabled: true }` too)
- `transport.http.rest` is a BOOL; omit it and every /api/v1 route 404s
  while /health still returns 200 (DefaultServerConfig true is
  overwritten by the config value in daemon.go)
- auth middleware returns 418 for the banned legacy key
  `meept_dev_default_key_CHANGE_ME`
- scratch daemon writes state into MEEPT_HOME but the dev key into the
  REAL ~/.meept — that asymmetry is intentional upstream (both sides of
  the client/server pair read the same file)
- a prior crashed scratch instance holds the RPC socket: kill by PID
  (lsof the socket path), then `kill -9` if graceful kill fails
