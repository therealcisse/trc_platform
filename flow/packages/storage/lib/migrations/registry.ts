import { z } from 'zod';
import {
  ExtensionStorageSchemaV0,
  ExtensionStorageSchemaV1,
  LATEST_SCHEMA_VERSION,
} from '../validation/versioned-storage.js';

export type Version = 0 | 1; // extended with v1

// Map versions to their zod-inferred types
export interface VersionMap {
  0: z.infer<typeof ExtensionStorageSchemaV0>;
  1: z.infer<typeof ExtensionStorageSchemaV1>;
}

export type MigrationStep<From extends Version, To extends Version> = {
  from: From;
  to: To;
  schemaFrom: z.ZodType<VersionMap[From]>;
  schemaTo: z.ZodType<VersionMap[To]>;
  up: (input: VersionMap[From]) => VersionMap[To] | Promise<VersionMap[To]>;
};

// Migrations
export const MIGRATIONS: readonly MigrationStep<any, any>[] = [
  {
    from: 0,
    to: 1,
    schemaFrom: ExtensionStorageSchemaV0,
    schemaTo: ExtensionStorageSchemaV1,
    up: v0 => {
      const { inboxInterOpenDelayMs: _remove, ...restConfig } = (v0.config as any) ?? {};
      return {
        ...v0,
        schemaVersion: 1,
        config: restConfig,
      } as any;
    },
  },
] as const;

export function getSchemaForVersion(v: Version) {
  switch (v) {
    case 0:
      return ExtensionStorageSchemaV0;
    case 1:
      return ExtensionStorageSchemaV1;
    default:
      throw new Error(`No schema for version ${v}`);
  }
}

export { LATEST_SCHEMA_VERSION };
