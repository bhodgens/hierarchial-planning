# Pitfall 29 - String-Based Code Assembly Causes Cascading Corruption

When to use: removing or rewriting multi-line code (regex, sed, f-strings), or assembling source via execute_code.
Lesson: use patch with verbatim text and verify after each edit; string-based assembly injects escape-sequence and orphaned-body corruption.

## Failure mode 1: regex/sed removal of function bodies

When removing unused functions from subagent-produced Go code to satisfy U1000 hooks (Pitfall 27), using `execute_code` with Python regex or `sed` to remove function bodies is extremely fragile. Go functions span multiple lines with nested braces; regex removal leaves orphaned bodies (function removed but body remains), dangling closing braces, or removed signatures with the implementation left behind. In one procgen tree, 5 rounds of regex-based removal progressively corrupted `pipeline.go` - each attempt fixed one undefined symbol but introduced a syntax error elsewhere.

## Failure mode 2: escape sequences in f-strings

Using `execute_code` to ASSEMBLE source code via Python string concatenation introduces a second corruption vector: literal escape sequences like `\\t` in Python f-strings render as the literal characters backslash-t, not as tab characters. A `.gd` file assembled this way contained 100+ parse errors from invisible invalid escapes.

## Prevention

(a) Use `patch` (mode=replace) with the FULL old_string (complete function from comment through closing brace) and new_string (empty or replacement) - NOT regex or string concatenation.
(b) If the exact multi-line text is uncertain, re-read the exact range with `terminal("sed -n 'N,Mp' file")`, then `patch` with the verbatim text.
(c) Verify with `go build` (or the language's equivalent) after EACH removal, not after all removals.
(d) If the file is too corrupted for incremental patches, use `write_file` to rewrite the entire file - trivial cost compared to cascading regex failures.
(e) When assembling code via execute_code, use REAL tab characters in the Python source (`\t` only inside regular strings, NEVER inside f-strings) - or better, write the file directly with `write_file`.
