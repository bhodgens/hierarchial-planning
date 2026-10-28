# Ggo embed llm prompts
When to use: embedding LLM prompts in Go binaries.
Lesson: go:embed patterns for prompt assets.

# Go `embed` for LLM Prompts

When including long LLM system prompts in Go source, raw string literals
(backtick-delimited) can produce cryptic compiler errors from Unicode
characters (em dashes, multiplication signs, accented letters), escaped
quotes, or template syntax that the Go parser misinterprets.

## Pattern

Put the prompt in a `.txt` file in the same package, then embed it:

```go
package mypackage

import _ "embed"

//go:embed prompt.txt
var systemPrompt string
```

The `.txt` file is plain text with no Go escaping required. The compiler
embeds it as a string at build time — no runtime file I/O, no path
resolution.

## When to use

- Prompts > 500 characters with special characters, JSON examples, or
  formatted text
- Prompts that need to be edited by non-Go-developers (designers,
  prompt engineers)
- Prompts with backticks, quotes, or template delimiters
- Any case where you get a `syntax error: unexpected ) after top level
  declaration` from a raw string literal

## When NOT to use

- Short prompts (< 200 chars) with no special characters — inline is fine
- Prompts that need runtime interpolation — `embed` is compile-time only;
  use `fmt.Sprintf` on the embedded string for templating

## Worked Example

rebellion-the-game adversarial harness (2026-07-20): the adversary system
prompt (~5KB, with Unicode em dashes, multiplication signs, JSON examples)
repeatedly produced `syntax error: unexpected ) after top level declaration`
at compile time, even after byte-level inspection showed no issues. Moving
the prompt to `adversary_prompt.txt` with `//go:embed` resolved it instantly.
