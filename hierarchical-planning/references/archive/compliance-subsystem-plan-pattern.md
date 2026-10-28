# Compliance Subsystem Plan Tree Pattern


When to use: plan target is a GDPR/SOC2/data-governance compliance layer.
Lesson: export/erasure/retention/audit-log decomposition pattern for compliance modules.
When the plan target is a GDPR/SOC2/data-governance compliance layer in a Go
backend. Applies to any compliance module with: data subject export (multi-table
query + archive), right to erasure (multi-table cascading delete), retention
policies (periodic purge), audit logging (hash-chained, tamper-evident), and
REST endpoints exposing these operations.

## When to Use

The plan builds a compliance subsystem with these characteristics:
- **Multi-table operations:** export or delete data across 10+ tables by `user_id`
- **Hash-chained audit log:** append-only table where each entry's hash includes
  the previous entry's hash, creating a tamper-evident chain
- **Retention enforcement:** configurable per-data-type retention with background
  purge goroutine
- **REST API surface:** thin HTTP handlers delegating to a central manager type
- **Permission-gated endpoints:** auth middleware checks roles/permissions per endpoint

## Decomposition Pattern

### Foundation-First with Audit Log as Prerequisite

Unlike generic backend plans, compliance trees have a critical dependency:
nearly every operation logs to the audit trail. The audit log must be defined
as an interface contract before other leaves can be fully tested. However,
leaves can be dispatched against the *interface* before the *implementation*
is complete.

```
Group A (independent foundation):
  03-retention-policy    ← no dependencies
  04-audit-log           ← no dependencies, defines AuditLogger interface

Group C (depend on audit log interface):
  01-data-subject-export ← uses AuditLogger interface
  02-right-to-erasure    ← uses AuditLogger interface

Group D (aggregates all):
  05-compliance-api      ← thin handlers calling all manager methods
```

### Leaf Sizing

- Audit log leaf: ~15K (hash chain logic, Log/Query/VerifyChain, migration)
- Export/erasure leaves: ~15K each (multi-table queries, transaction management)
- Retention leaf: ~12K (config struct, purge logic, goroutine lifecycle)
- API leaf: ~18K (5-6 handlers, request/response types, SOC2 report assembly)

## Key Pattern: Hash-Chained Audit Log

This is the compliance subsystem's foundation. The design must be stable before
other leaves can integrate.

### Canonical Representation

The hash is computed over a deterministic, pipe-delimited string that excludes
the `id` and `entry_hash` fields (those are computed AFTER canonicalization):

```
canonical = "timestamp_RFC3339|actor_id|action|resource_type|resource_id|details|prev_hash"
entry_hash = SHA256(canonical)
```

The first entry chains from a genesis hash (64 zeros).

### Go Implementation Stub

```go
func canonicalRepresentation(entry AuditEntry) string {
    return fmt.Sprintf("%s|%s|%s|%s|%s|%s|%s",
        entry.Timestamp.UTC().Format(time.RFC3339),
        entry.ActorID, entry.Action, entry.ResourceType,
        entry.ResourceID, entry.Details, entry.PrevHash,
    )
}

func computeEntryHash(entry AuditEntry) string {
    sum := sha256.Sum256([]byte(canonicalRepresentation(entry)))
    return hex.EncodeToString(sum[:])
}
```

### Chain Verification

`VerifyChain(from time.Time)` walks entries in order, checking:
1. First entry's `prev_hash` equals genesis hash
2. Each subsequent entry's `prev_hash` equals the prior entry's `entry_hash`
3. Each entry's stored `entry_hash` matches a fresh recomputation

If any check fails, return `BrokenAt: <entry_id>`.

### Concurrency Consideration

The `Log()` method reads the last entry's hash, then inserts. In SQLite WAL
mode, the single-writer lock serializes this sufficiently. If using PostgreSQL
with concurrent writers, wrap the read+compute+insert in a transaction with
`SELECT ... FOR UPDATE` or use `INSERT ... SELECT` to atomically compute the
hash in SQL.

## Key Pattern: Multi-Table Cascading Operations

### Export (GDPR Article 15)

Query every table that holds user data. The export leaf defines a query helper
per table group:

| Query Helper | Tables | Join Strategy |
|-------------|--------|---------------|
| queryEventsForUser | events | direct user_id filter |
| querySessionsForUser | sessions | direct user_id filter |
| queryKeystrokeLogForUser | keystroke_log | JOIN events ON event_id |
| querySkillsForUser | skills | JOIN skill_candidates → patterns |
| queryPatternsForUser | patterns | direct user_id filter |
| countScreenshotsForUser | screenshots | JOIN events via timestamp |
| queryLatestConstitution | constitution_versions | direct user_id, LIMIT 1 |

The export assembles a `UserDataExport` struct with per-type counts in
`ExportStats`, then packages as JSON → ZIP via `archive/zip`.

### Erasure (GDPR Article 17)

Delete in dependency order — child tables before parent tables. Run inside a
single transaction for atomicity. The critical table list (from AgentAudit
Phase 1+2):

```
1. keystroke_log (FK → events)
2. skill_executions (FK → skills)
3. skills (FK → skill_candidates)
4. skill_candidates (FK → patterns)
5. vlm_analyses, rhythm_profiles, proficiency_scores, recommendations
6. constitution_versions
7. patterns
8. transitions
9. shortcut_stats
10. entity_edges (src/dst LIKE 'user:<id>%')
11. sessions
12. events
```

**Post-delete verification:** query every table for residual `user_id` rows.
Return error listing orphaned tables if any found. This catches missed tables
during development and verifies completeness in production.

### The Append-Only vs Erasure Tension

The audit log is append-only (INSERT only, never DELETE). But GDPR Article 17
requires removing personal identity. Resolution:

- **Anonymize, don't delete:** `UPDATE audit_log SET actor_id = '[anonymized]'
  WHERE actor_id = ?`
- **Do NOT modify hash chain fields** (`prev_hash`, `entry_hash`). The chain
  remains structurally intact for tamper detection of action records.
- **Document the tradeoff:** anonymized entries will fail strict recomputation
  because `actor_id` changed. The SOC2 evidence report should note this. An
  alternative: exclude `actor_id` from the canonical representation, accepting
  that the audit log cannot verify *who* acted, only *that* an action occurred.

## Key Pattern: Compliance REST API Leaf

The API leaf aggregates all prior leaves. Thin handlers delegate to
`ComplianceManager` methods — no business logic in handlers.

### Route Registration

Use Go 1.22+ method-pattern routing (`mux.HandleFunc("POST /path", h)`) to
eliminate third-party routers. Each endpoint gets auth middleware applied:

```go
func RegisterRoutes(mux *http.ServeMux, cm *ComplianceManager,
    authMW func(http.HandlerFunc, string) http.HandlerFunc) {
    mux.HandleFunc("POST /api/v1/compliance/export-user",
        authMW(cm.handleExportUser, "export_compliance"))
    // ...
}
```

### Handler Patterns by Response Type

| Endpoint | Response | Key Detail |
|----------|----------|------------|
| POST export-user | Binary ZIP | Set Content-Type=application/zip, Content-Disposition=attachment |
| DELETE user/{id} | 204 No Content | No body |
| GET audit-log | JSON array | Include chain_valid flag in response |
| PUT retention-policy | JSON config | Validate before saving |
| GET soc2-evidence | JSON report | Aggregates audit counts, chain verification, retention config |

### SOC2 Evidence Report

The evidence endpoint bundles compliance artifacts into a self-contained JSON
report an auditor can review without system access:

```go
type SOC2EvidenceReport struct {
    GeneratedAt       time.Time
    Period            TimePeriod
    AccessControls    AccessControlEvidence  // roles, permissions, SSO status
    RetentionPolicy   *RetentionConfig
    AuditLogEntries   int                     // count for period
    ChainVerification *ChainVerification      // hash chain intact?
    UserCount         int
    ExportCount       int
    DeletionCount     int
}
```

## Interface Contract Patterns

### ComplianceManager as Central Type

All operations hang off `ComplianceManager`. The constructor takes `store.Store`
and `AuditLogger`:

```go
type ComplianceManager struct {
    store    store.Store
    auditLog AuditLogger
}
func NewComplianceManager(s store.Store, al AuditLogger) *ComplianceManager
```

Every compliance operation (export, delete, retention run, config change) logs
to the audit trail as a side effect. The audit log call should be non-fatal —
if logging fails, the operation still succeeds. The error is swallowed but
the user gets their data.

### AuditLogger Interface

Defined as an interface (not a concrete type) so other leaves can mock it in
tests:

```go
type AuditLogger interface {
    Log(ctx context.Context, entry AuditEntry) error
    Query(ctx context.Context, from, to time.Time, filters ...AuditFilter) ([]AuditEntry, error)
    VerifyChain(ctx context.Context, from time.Time) (*ChainVerification, error)
}
```

The concrete `dbAuditLogger` is created by the audit log leaf. Other leaves
dispatch against the interface and use a mock in tests.

## Migration Numbering

Compliance migrations are high-numbered (Phase 4 = 020+). Check existing
migration numbers before assigning. The compliance branch typically owns:
- `020_audit_log.sql` — append-only, hash-chained
- `021_retention_policy.sql` — single-row config table (CHECK(id = 1))

## Testing Patterns

### Test DB Setup

Every leaf needs `setupTestDB(t)` that creates an in-memory SQLite DB, applies
relevant migrations, and seeds test data. Share this across the package via a
`testhelpers_test.go` file.

### Mock Audit Logger

```go
type mockAuditLogger struct {
    entries []AuditEntry
}
func (m *mockAuditLogger) Log(ctx context.Context, e AuditEntry) error {
    m.entries = append(m.entries, e); return nil
}
```

### Hash Chain Tests

Test the chain in both directions:
1. **Valid chain:** insert N entries, verify chain passes
2. **Tampered chain:** insert N entries, UPDATE one directly via SQL, verify
   `VerifyChain` detects the break and reports `BrokenAt`

## Pitfalls Specific to Compliance Plan Trees

1. **Missing tables in cascading operations.** The erasure leaf must enumerate
   EVERY table with user data. Use a `userDataTableList` slice (table name +
   count query) so the verification step systematically checks all tables.
   Cross-reference against all Phase migrations to ensure completeness.

2. **Screenshots table lacks user_id.** The screenshots table may not have a
   direct `user_id` column. It joins through `events` via timestamp or
   `event_id`. The join may be imprecise. Document this as a known imprecision
   in the export — the count is approximate.

3. **Retention goroutine must handle missing table.** If a Phase 2 table
   doesn't exist (e.g., early deployment), the purge DELETE will error.
   Either check table existence first or swallow "no such table" errors.

4. **Auth middleware import cycle.** The compliance API leaf needs auth
   middleware but must not import the auth package directly (cycle). Use a
   function type parameter: `func(http.HandlerFunc, string) http.HandlerFunc`.
   The server wires the real middleware at route registration time.

5. **Audit log Log() concurrency.** The read-last-hash-then-insert sequence
   has a race window. SQLite WAL's single-writer lock mitigates this. For
   PostgreSQL, use `SELECT ... FOR UPDATE` or `INSERT ... SELECT`.

6. **Phase 2 tables may not exist.** In a deployment that only ran Phase 1
   migrations, DELETE statements against `vlm_analyses` or `constitution_versions`
   will fail. Either guard with table-existence checks or document that
   compliance requires all migrations applied.

## Worked Example

AgentAudit Phase 4 branch 16 (2026-08 session):
- 1 orchestrator + 5 leaves (2 foundation + 2 dependent + 1 API aggregator)
- 4 interface contracts: ComplianceManager, AuditLogger, Data Export Types,
  Retention Config
- 3 concurrency groups: A (retention + audit log) → C (export + erasure) → D (API)
- 2 migrations: 020_audit_log.sql, 021_retention_policy.sql
- Hash chain: canonical pipe-delimited representation, SHA-256, genesis = 64 zeros
- 16 tables covered in cascading delete with post-delete verification
- 5 REST endpoints with permission-gated middleware
- Each leaf had 5-6 TDD tasks with full Go code stubs
