import { z } from 'zod';
import { LocalTime } from '@extension/types';

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

export const DelayConfigSchema = z.object({
  min: z.number(),
  max: z.number(),
});

export const ProductPatternSchema = z.object({
  insuredType: z.string().optional(),
  insuredAge: DelayConfigSchema.optional(),
  meta: z.record(z.string(), z.unknown()).optional(),
});

export const ProductConfigSchema = z.object({
  text: z.string(),
  insuredType: z.string(),
  insuredAge: DelayConfigSchema,
  meta: z.record(z.string(), z.unknown()).optional(),
});

export const StoredProductStrategySchema = z.object({
  id: z.string(),
  name: z.string(),
  patterns: z.array(ProductPatternSchema),
});

// For storage purposes ProductStrategy == StoredProductStrategy
export const ProductStrategySchema = StoredProductStrategySchema;

export const ProcessingTimeWindowSchema = z.object({
  id: z.string(),
  min: LocalTimeSchema,
  max: LocalTimeSchema,
  duration: z.number().int().positive(),
  enabled: z.boolean(),
});

export const ExecutionConfigSchema = z.object({
  // Inbox mode configuration
  inboxMode: z.boolean().default(true),
  inboxReloadSeconds: z.array(z.number()).default([4, 7]),
  inboxPostReloadDelayMs: z.number().default(0),
  inboxMaxLinksPerScan: z.number().default(10),
  inboxInterOpenDelayMs: z.number().default(400),

  token: z.string().optional(),

  // Required fields
  operationalHours: OperationalHoursSchema,
  emailMode: z.boolean(),
  emailRefreshMin: z.number(),
  emailRefreshMax: z.number(),
  products: z.array(ProductConfigSchema),

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

export const BuyingOfferSchema = z.object({
  id: z.string(),
  timeout: z.number(),
});

export const LogEntrySchema = z.object({
  timestamp: z.number(),
  message: z.string(),
});

export const FlowSchema = z.object({
  id: z.string(),
  timestamp: z.number(),
  requestTimestamp: z.number(),
  status: z.enum(['running', 'done', 'failed']),
  source: z.enum(['email', 'inbox']),
  type: z.enum(['pdf', 'offer']),
  doneTimestamp: z.number().optional(),
});

export const ManagedTabInfoSchema = z.object({
  flowId: z.string(),
  createdAt: z.number(),
  lastActive: z.number(),
});
