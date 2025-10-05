# Extension Storage Migrations Spec

Status: active
Schema version: 0

Purpose
- Preserve user data across schema changes in the browser extension
- Provide a typed, autonomous pipeline that upgrades persisted state to the latest schema at startup and on extension update

Design goals
- Typed at every boundary, using zod schemas per version
- Idempotent, safe to run any time
- Backfill defaults for new required fields
- No user interaction required, no reinstall required
- Observable in logs

Key components
1) Versioned schemas
- Source: packages/storage/lib/validation/versioned-storage.ts
- Current latest: ExtensionStorageSchemaV0 with schemaVersion: 0
- Future versions: add ExtensionStorageSchemaV1, V2, ... and update LATEST_SCHEMA_VERSION and ExtensionStorageSchemaLatest

2) Migration registry
- Source: packages/storage/lib/migrations/registry.ts
- Holds an ordered list of MigrationStep objects from N -> N+1
- For v0 launch, MIGRATIONS is intentionally empty
- Add commented reference for a v1 step to serve as a template

3) Migration runner
- Source: packages/storage/lib/migrations/runner.ts
- Ensures data is validated against detected version, deep-fills defaults, and validates against latest schema
- Writes only when the output differs
- Exported ensureMigrated(storage, latestDefaults, log?) to run from background initialization

4) Wiring
- Background init calls ensureMigrated(extensionConfigStorage, DEFAULT_CONFIG, log)
- Also safe to run in chrome.runtime.onInstalled for details.reason === 'update'

5) Defaults backfilling
- All writes should deep-merge DEFAULT_CONFIG before validation. This reduces the chance of parse failures during transitions.

Versioning policy
- schemaVersion is a numeric literal at the type level for ExtensionStorage
  - Today: schemaVersion: 0
  - Later: evolve to 0 | 1 | 2, ... as needed
- Every new version requires:
  - New zod schema with z.literal(nextVersion)
  - A migration step in MIGRATIONS from prev -> next
  - DEFAULT_CONFIG updated to the new shape and version

Operational flow
1) Startup
- ensureMigrated loads current storage, computes target, persists only if changed
- Logs a succinct upgrade message if a write occurred

2) Runtime writes
- Per-method handlers in extensionConfigStorage continue to validate using the latest schema
- Use deep-merge with DEFAULT_CONFIG before validateStorageData

3) Observability
- The runner accepts a log function. Background passes storage-backed logs.addLog so events are captured in the extension logs.

Adding the first migration (reference)
- Use the commented code blocks in versioned-storage.ts and migrations/registry.ts as a starting point
- Typical changes include renaming fields, splitting a single field into multiple, or normalizing structures

Example migration steps (commented in code)
- Define ExtensionStorageSchemaV1 with schemaVersion: 1 and any shape changes
- Add MIGRATIONS entry from 0 -> 1 with an up function that transforms v0 data to v1

Testing
- Unit tests should exercise:
  - Empty storage -> DEFAULT_CONFIG at latest version
  - Already-latest storage -> idempotent, no write
  - Legacy payloads -> migrated and validated at latest version

Caveats
- The runner intentionally limits logic to migration orchestration and final validation. Per-step transformations belong in MIGRATIONS to keep responsibilities clear.
- Avoid logging before the first persisted write completes, to prevent validation against a pre-migration shape.

Checklist for future changes
- If you modify any of the following, consider bumping schemaVersion and adding a migration step:
  - packages/types/lib/app/types.ts: interface ExtensionStorage or ExecutionConfig
  - packages/storage/lib/validation/storage.ts: ExecutionConfigSchema or components used by storage
  - packages/storage/lib/impl/extension-config-storage.ts: DEFAULT_CONFIG shape or key renames
- When bumping:
  - Add V{n+1} schema, set it as latest
  - Add MIGRATIONS step n -> n+1
  - Update DEFAULT_CONFIG.schemaVersion
  - Add or adjust deep-merge defaults in write paths if needed
