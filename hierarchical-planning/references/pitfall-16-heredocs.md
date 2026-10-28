# Pitfall 16 - Heredocs in execute_code Fail Silently

When to use: batch file operations from execute_code, or any temptation to write files via shell heredoc.
Lesson: heredoc syntax is a shell feature - inside execute_code's Python it is an unterminated string literal. Use write_file and terminal append instead.

If orchestrators or leaf agents use `execute_code` for batch file operations, heredoc syntax (`cat > file << 'EOF'`) causes "unterminated string literal" errors in Python. The error surfaces as a syntax failure of the whole code block, often far from the line that intended the heredoc - which is why it reads as "fails silently."

## Rules

1. Use `write_file` for content creation.
2. Use `terminal("cat temp.md >> target.md")` for appending.
3. Never embed heredocs inside `execute_code` terminal calls.

Related corruption vectors in the same family: Pitfall 29 (f-string escape sequences and regex-based code assembly). The general rule: content creation goes through `write_file`/`patch`, not through string assembly in execute_code.
