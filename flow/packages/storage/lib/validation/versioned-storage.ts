import { ExecutionConfigSchemaV0, ExecutionConfigSchemaV1 } from './primitives.js';
import { z } from 'zod';

/**
 * Versioned schemas for ExtensionStorage
 *
 * Start with V0 as the current shape. Future versions should be added here
 * using new zod objects with schemaVersion literals and migrated via the
 * migrations registry.
 */

// v0 schema equals current shape, with schemaVersion fixed to 0
export const ExtensionStorageSchemaV0 = z.object({
  schemaVersion: z.literal(0),
  enabled: z.boolean(),
  debugMode: z.boolean().default(false),
  config: ExecutionConfigSchemaV0,
});

export const ExtensionStorageSchemaV1 = z.object({
  schemaVersion: z.literal(1),
  enabled: z.boolean(),
  debugMode: z.boolean().default(false),
  config: ExecutionConfigSchemaV1,
});

// Latest aliases
export const LATEST_SCHEMA_VERSION = 1 as const;
export const ExtensionStorageSchemaLatest = ExtensionStorageSchemaV1;

// Types for consumers
export type ExtensionStorageV0 = z.infer<typeof ExtensionStorageSchemaV0>;
export type ExtensionStorageLatest = z.infer<typeof ExtensionStorageSchemaLatest>;

/**
 * Reference for a future v1 schema, commented out until needed.
 *
 * To introduce v1:
 * 1) Define ExtensionStorageSchemaV1 below and set LATEST_SCHEMA_VERSION to 1
 * 2) Update ExtensionStorageSchemaLatest alias to V1
 * 3) Add a migration step in migrations/registry.ts from 0 -> 1
 */
/*
export const ExtensionStorageSchemaV1 = ExtensionStorageSchemaV0
  // Example: remove or rename fields here if needed
  // .omit({ /* oldProp: true *-/ })
  .extend({
    schemaVersion: z.literal(1),
    // Example changes for v1
    // newRequiredField: z.string(),
    // config: ExecutionConfigSchemaV1, // if you version ExecutionConfig separately
  });

export const LATEST_SCHEMA_VERSION = 1 as const;
export const ExtensionStorageSchemaLatest = ExtensionStorageSchemaV1;

export type ExtensionStorageV1 = z.infer<typeof ExtensionStorageSchemaV1>;
export type ExtensionStorageLatest = ExtensionStorageV1;
*/
