import { DEFAULT_LOCAL_MODEL } from '../constants.js';
import { LocalTime } from '@extension/types';
import { z } from 'zod';

export const LocalTimeSchema = z
  .object({
    hour: z.number().int().min(0).max(23),
    minute: z.number().int().min(0).max(59),
    second: z.number().int().min(0).max(59).default(0).optional(),
  })
  .transform(({ hour, minute, second }) => LocalTime.of(hour, minute, second ?? 0));

export const OperationalHoursSchema = z.record(
  z.enum(['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']),
  z.object({
    enabled: z.boolean(),
    min: LocalTimeSchema,
    max: LocalTimeSchema,
  }),
);

export const ProcessingTimeWindowSchema = z.object({
  id: z.string(),
  min: LocalTimeSchema,
  max: LocalTimeSchema,
  duration: z.number().int().positive(),
  enabled: z.boolean(),
});

// V0 shape included inboxInterOpenDelayMs
export const ExecutionConfigSchemaV0 = z.object({
  // Inbox mode configuration
  inboxMode: z.boolean().default(true),
  inboxReloadSeconds: z.array(z.number()).default([4, 7]),
  inboxPostReloadDelayMs: z.number().default(0),
  inboxMaxLinksPerScan: z.number().default(10),
  inboxInterOpenDelayMs: z.number().default(400),
  inboxBuysImmediately: z.boolean().default(true),

  token: z.string().optional(),

  // Required fields
  operationalHours: OperationalHoursSchema,
  emailMode: z.boolean(),
  emailRefreshMin: z.number(),
  emailRefreshMax: z.number(),

  // Animal insurance product strategy
  animal: z.object({ dogs: z.boolean(), cats: z.boolean() }),
  animalProcessingTimeSeconds: z.number(),
  animalProcessingTimeWindows: z.array(ProcessingTimeWindowSchema),

  // Cancer scan product strategy
  cancer: z.boolean(),
  cancerProcessingTimeSeconds: z.number(),
  cancerProcessingTimeWindows: z.array(ProcessingTimeWindowSchema),

  // Health insurance product strategy
  health: z.boolean(),
  healthProcessingTimeSeconds: z.number(),
  healthProcessingTimeWindows: z.array(ProcessingTimeWindowSchema),

  // Accident insurance product strategy
  accidents: z.boolean(),
  accidentProcessingTimeSeconds: z.number(),
  accidentProcessingTimeWindows: z.array(ProcessingTimeWindowSchema),
});

// V1 shape drops inboxInterOpenDelayMs
export const ExecutionConfigSchemaV1 = z.object({
  // Inbox mode configuration
  inboxMode: z.boolean().default(true),
  inboxReloadSeconds: z.array(z.number()).default([4, 7]),
  inboxPostReloadDelayMs: z.number().default(0),
  inboxMaxLinksPerScan: z.number().default(10),
  inboxBuysImmediately: z.boolean().default(true),
  inboxAutoRefreshMs: z.number().default(300000),

  token: z.string().optional(),
  useLocal: z.boolean().default(true),
  localModel: z.string().default(DEFAULT_LOCAL_MODEL),

  // Required fields
  operationalHours: OperationalHoursSchema,
  emailMode: z.boolean(),
  emailRefreshMin: z.number(),
  emailRefreshMax: z.number(),

  // Animal insurance product strategy
  animal: z.object({ dogs: z.boolean(), cats: z.boolean() }),
  animalProcessingTimeSeconds: z.number(),
  animalProcessingTimeWindows: z.array(ProcessingTimeWindowSchema),

  // Cancer scan product strategy
  cancer: z.boolean(),
  cancerProcessingTimeSeconds: z.number(),
  cancerProcessingTimeWindows: z.array(ProcessingTimeWindowSchema),

  // Health insurance product strategy
  health: z.boolean(),
  healthProcessingTimeSeconds: z.number(),
  healthProcessingTimeWindows: z.array(ProcessingTimeWindowSchema),

  // Accident insurance product strategy
  accidents: z.boolean(),
  accidentProcessingTimeSeconds: z.number(),
  accidentProcessingTimeWindows: z.array(ProcessingTimeWindowSchema),
});

// Latest alias
export const ExecutionConfigSchema = ExecutionConfigSchemaV1;
