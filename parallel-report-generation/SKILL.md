---
name: parallel-report-generation
description: Generate long-form reports from plans/source material by splitting work across parallel subagents, assembling into a single output. Handles rate limit retries, artifact cleanup, and TOC unification.
version: 1.0
category: productivity
---

# Parallel Report Generation with Subagents

Generate long-form reports/documents from plans or source material by splitting work across parallel subagents, then assembling into a single output file.

## When to Use
- plan.md or similar source material is too large for a single LLM pass (>2000 lines)
- Report has clear logical section boundaries
- User asks to "implement a plan" and output a report/document

## Steps

### 1. Read and Assess the Source
- Read the full source material (plan.md, spec, etc.)
- Identify natural section boundaries
- Estimate total size -- if under ~500 lines, a single subagent may suffice

### 2. Split Into Parallel Tasks (max 3)
- Group sections logically (e.g., sections 1-3, 4-6, 7-11)
- Each subagent writes to a separate temp file: `report_part1.md`, `report_part2.md`, `report_part3.md`
- In the task context, specify which sections to cover and the output file path
- Set `max_iterations: 30` to give subagents enough turns

### 3. Handle Rate Limit Failures
- Parallel subagents can trigger HTTP 429 rate limits on the provider
- If some tasks fail with rate limit errors, retry ONLY the failed tasks individually (not as a batch)
- A single subagent running alone rarely hits rate limits
- May need 2-3 retry rounds for all parts to complete

### 4. Assemble the Final Document
- Use `execute_code` to read all parts and concatenate them
- Use `---` separators between parts
- **Critical: read_file output contains line-number prefixes** -- when concatenating raw content from read_file, these become double-numbered artifacts (e.g., `1|1|content`)
- Post-process to strip artifacts:
  ```python
  import re
  m = re.match(r'^\s*\d+\|\s*\d+\|(.*)$', line)
  if m: fixed = m.group(1)
  ```

### 5. Clean Up and Verify
- Remove "Part X" markers that are no longer relevant in the combined document
- Update the Table of Contents to reflect all sections
- Fix any header metadata (e.g., "Sections 1-3 of 11" -> "Sections 1-11 Complete")
- Verify all expected sections are present by checking for `## N.` markers
- Remove temp part files (`rm -f report_part*.md`)
- Do a final read of first ~80 lines and last ~30 lines to confirm clean output

## Prevention: Avoiding Line-Number Corruption (Root Cause)

The #1 cause of corrupted output is **subagents using read_file on source material and then including that read_file output in their write_file call**. `read_file` returns content with `     N|` line-number prefixes. If a subagent reads a file and then passes that output into `write_file`, those line numbers get baked into the output file permanently.

**Prevention (do this in EVERY subagent task):**
1. In the task context, include ALL source data inline as structured text. Do NOT tell the subagent to "read plan.md first."
2. Add explicit formatting instructions: "Write clean markdown only. No line numbers. No code blocks wrapping the content."
3. Instruct the subagent to write directly to the output file using `write_file` with the full content as a single string.
4. Add: "Do NOT read the file back after writing. Just write it once and stop."

If the source material is too large to inline in the context, have ONE subagent read it first and extract the relevant portion, then pass that extracted content as context to the writing subagent.

## Assembly: Safe Concatenation

When assembling parts into the final document:
1. Use `terminal("tail -n +N file")` to extract from each part file (skipping each part's individual header/metadata)
2. Write a unified header+TOC separately with `write_file`
3. Use `terminal("cat header.md part1.md part2.md part3.md > report.md")` to concatenate
4. **Verify with `xxd report.md | head -3`** that raw bytes start with `#` (not spaces+numbers+pipe)
5. **Verify with `grep -cE '^[[:space:]]+[0-9]+\\|' report.md`** that zero lines have number-pipe prefixes

If artifacts are found, fix with: `sed -E -i '' 's/^[[:space:]]+[0-9]+\|//' report.md`

## Header Normalization

Subagents may use inconsistent header casing (e.g., `## SECTION 4: TITLE` vs `## Section 4 — Title`). Normalize after assembly:
```
sed -i '' 's/^## SECTION 4: ALTERNATIVE THEORIES/## Section 4 — Alternative Theories/' report.md
```
Use em-dashes (—) for consistency.

## Cleanup Checklist

After assembly, run these checks:
- [ ] All `## Section N` headers present (grep for `^## `)
- [ ] Zero `(gauge)` or placeholder values remain (if updating from concrete data)
- [ ] No duplicate title/metadata blocks from part boundaries
- [ ] No "End of Report Part X" markers
- [ ] Single clean ending with document metadata
- [ ] Table of Contents covers all sections
- [ ] `xxd` raw byte check confirms no line-number prefixes
- [ ] `wc -l -c` for final size confirmation

## Updating Reports with New Data

When updating an existing report with new concrete data (e.g., replacing "(gauge)" placeholders with confirmed lab values):
1. Re-run the full parallel subagent pipeline rather than trying to patch individual values -- the scope of changes (updated analysis, new sections, shifted probabilities) justifies a full rewrite.
2. Inline ALL new data values in each subagent's context as structured text. Do NOT tell subagents to read the existing report.md (it has line-number artifacts from read_file).
3. Add explicit instructions: "Replace ALL (gauge) placeholders with concrete values" and "Update urgency from hypothetical to confirmed."
4. If adding a new section (e.g., Section 12), include it in the context for the relevant subagent with full content requirements.

## Pitfalls
- **Rate limits**: The biggest risk with 3 parallel subagents. Always plan for retries.
- **Line-number corruption (ROOT CAUSE)**: Subagents that read_file source material and include that output in write_file will bake `     N|` prefixes into the output. Prevent by inlining all source data in the task context instead of asking subagents to read files.
- **Heredocs in execute_code**: Do NOT use heredoc syntax (`cat > file << 'EOF'`) inside `terminal()` calls from `execute_code` -- Python will fail with unterminated string literal. Use `write_file()` for content and `terminal("cat file >> target")` for appending.
- **Inconsistent TOC**: Each subagent generates its own TOC fragment. Write a unified TOC in the header file separately.
- **Stray part markers**: Subagents add "End of Part X" footers. Remove with sed in cleanup.
- **ALL CAPS headers**: Some subagents use ALL CAPS for section headers. Normalize to Title Case after assembly.
- **write_file then terminal append**: When appending an ending to a file, use `write_file` for a temp file then `terminal("cat /tmp/ending.md >> report.md")` -- avoids heredoc issues entirely.
