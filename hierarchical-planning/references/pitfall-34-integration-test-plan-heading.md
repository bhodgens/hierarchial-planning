# Pitfall 34 - Compliance Scanner Requires Exact Heading "Integration Test Plan"

When to use: writing or reviewing orchestrator documents.
Lesson: the heading must be exactly `## Integration Test Plan` - variants fail the scan.

The `check_template_compliance.py` scanner requires the exact heading `## Integration Test Plan` - it does NOT accept variants like `## Integration Review Plan`, `## Integration Testing`, or `## Integration Tests`. In one session, 3 of 4 plan trees initially failed compliance because they used "Integration Review Plan" instead.

## Prevention

Always use the exact template heading `## Integration Test Plan`. If you prefer "review" terminology in your content, keep the heading as-is and title subsections differently. The scanner checks for the literal string `## integration test plan` (case-insensitive) in the markdown.

Worked example and omitted-section snippets: `references/codebase-review-plan-patterns.md`. Full exact-heading list: `references/compliance-headings.md`. Sister heading rule: Pitfall 36 (`## Completion Tracking Table`).
