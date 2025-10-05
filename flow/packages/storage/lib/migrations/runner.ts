import { ExtensionStorageSchemaLatest } from '../validation/versioned-storage.js';
import { LATEST_SCHEMA_VERSION, MIGRATIONS, getSchemaForVersion } from './registry.js';

// Very small deep merge tailored to the ExtensionStorage shape
export function withDefaults<T extends { config: any }>(latestDefaults: T, value: Partial<T>): T {
  return {
    ...latestDefaults,
    ...value,
    config: {
      ...latestDefaults.config,
      ...(value.config ?? {}),
    },
  } as T;
}

export function detectVersion(raw: unknown): number {
  if (raw && typeof raw === 'object' && 'schemaVersion' in raw) {
    const v = (raw as any).schemaVersion;
    if (typeof v === 'number' && Number.isFinite(v) && v >= 0) return v;
  }
  return 0; // assume v0 if absent
}

export async function migrateToLatest<T extends { schemaVersion: number }>(
  raw: unknown,
  latestDefaults: T,
): Promise<T> {
  // New installs, or empty storage
  if (raw == null) {
    const fresh = { ...(latestDefaults as any), schemaVersion: LATEST_SCHEMA_VERSION };
    return ExtensionStorageSchemaLatest.parse(fresh) as unknown as T;
  }

  // Start at detected version, parse against that version's schema
  let currentVersion = detectVersion(raw);
  let current = getSchemaForVersion(currentVersion as any).parse(withDefaults(latestDefaults as any, raw as any));

  // Step through registry, strictly validating each step
  while (currentVersion < LATEST_SCHEMA_VERSION) {
    const step = MIGRATIONS.find(m => m.from === currentVersion && m.to === currentVersion + 1);
    if (!step) throw new Error(`Missing migration step from v${currentVersion} to v${currentVersion + 1}`);

    const validatedInput = step.schemaFrom.parse(current);
    const next = await step.up(validatedInput);
    current = step.schemaTo.parse(next);
    currentVersion = step.to;
  }

  // Final validation against latest, with defaults and explicit schemaVersion
  const latest = ExtensionStorageSchemaLatest.parse(
    withDefaults(latestDefaults as any, { ...current, schemaVersion: LATEST_SCHEMA_VERSION }),
  );
  return latest as unknown as T;
}

export async function ensureMigrated<D extends { schemaVersion: number }>(
  storage: { get: () => Promise<D>; set: (v: D) => Promise<void> },
  latestDefaults: D,
  log?: (msg: string) => Promise<void> | void,
): Promise<void> {
  const before = await storage.get();
  const after = await migrateToLatest(before, latestDefaults);

  const changed = JSON.stringify(before) !== JSON.stringify(after);
  if (changed) {
    await storage.set(after);
    await log?.(`[Migration] Upgraded schema to v${LATEST_SCHEMA_VERSION}`);
  }
}
