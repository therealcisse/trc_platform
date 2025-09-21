import { z } from 'zod';
import type { ProductStrategy, DelayConfig } from '@extension/types';

export const OperationalHoursSchema = z.record(
  z.enum(['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']),
  z.object({
    enabled: z.boolean(),
    min: z.number(),
    max: z.number(),
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

// Ensure we're validating against StoredProductStrategy
export const ProductStrategySchema = StoredProductStrategySchema;

export const ExecutionConfigSchema = z.object({
  // Inbox mode configuration
  inboxMode: z.boolean().optional(),
  inboxReloadSeconds: z.array(z.number()).optional().default([0, 5]),
  inboxPostReloadDelayMs: z.number().optional().default(2000),
  inboxMaxLinksPerScan: z.number().optional().default(10),
  inboxInterOpenDelayMs: z.number().optional().default(400),
  token: z.string().optional(),

  // Required fields (removed .optional())
  operationalHours: OperationalHoursSchema,
  emailMode: z.boolean(),
  emailRefreshMin: z.number(),
  emailRefreshMax: z.number(),
  products: z.array(ProductConfigSchema),

  // Animal insurance product strategy
  animals: z.boolean(),
  animalTimerMin: z.number(),
  animalTimerMax: z.number(),
  animalProcessingTimeSeconds: z.number(),

  // Cancer scan product strategy
  cancer: z.boolean(),
  cancerTimerMin: z.number(),
  cancerTimerMax: z.number(),
  cancerProcessingTimeSeconds: z.number(),

  // People insurance product strategy
  people: z.boolean(),
  peopleTimerMin: z.number(),
  peopleTimerMax: z.number(),
  peopleProcessingTimeSeconds: z.number(),
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
  status: z.enum(['running', 'done']),
  source: z.enum(['email', 'inbox']),
  title: z.string(),
});

export const ExtensionStorageSchema = z.object({
  enabled: z.boolean(),
  config: ExecutionConfigSchema,
  logs: z.array(LogEntrySchema),
  managedTabs: z.record(z.string(), z.number()),
  buyingOffers: z.record(z.string(), BuyingOfferSchema),
  productStrategies: z.array(StoredProductStrategySchema),
  flows: z.record(z.string(), FlowSchema),
});

export function validateStorageData<T>(schema: z.ZodSchema<T>, data: unknown): T {
  return schema.parse(data);
}

// Type inference helpers
export type ValidatedExecutionConfig = z.infer<typeof ExecutionConfigSchema>;
export type ValidatedBuyingOffer = z.infer<typeof BuyingOfferSchema>;
export type ValidatedLogEntry = z.infer<typeof LogEntrySchema>;
export type ValidatedProductStrategy = z.infer<typeof ProductStrategySchema>;
export type ValidatedFlow = z.infer<typeof FlowSchema>;
export type ValidatedExtensionStorage = z.infer<typeof ExtensionStorageSchema>;
export type ValidatedProductConfig = z.infer<typeof ProductConfigSchema>;
export type ValidatedDelayConfig = z.infer<typeof DelayConfigSchema>;
