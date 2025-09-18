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
  delay: DelayConfigSchema.optional(),
});

export const ProductConfigSchema = z.object({
  text: z.string(),
  insuredType: z.string(),
  insuredAge: DelayConfigSchema,
  meta: z.record(z.string(), z.unknown()).optional(),
  delay: DelayConfigSchema.optional(),
});

export const StoredProductStrategySchema = z.object({
  id: z.string(),
  name: z.string(),
  patterns: z.array(ProductPatternSchema),
});

// Ensure we're validating against StoredProductStrategy
export const ProductStrategySchema = StoredProductStrategySchema;

export const ExecutionConfigSchema = z.object({
  token: z.string().optional(),
  operationalHours: OperationalHoursSchema.optional(),
  emailMode: z.boolean().optional(),
  emailRefreshMin: z.number().optional(),
  emailRefreshMax: z.number().optional(),
  inboxMode: z.boolean().optional(),
  inboxRefreshMin: z.number().optional(),
  inboxRefreshMax: z.number().optional(),
  products: z.array(ProductConfigSchema).optional(),
  animals: z.boolean().optional(),
  animalTimerMin: z.number().optional(),
  animalTimerMax: z.number().optional(),
  animalProcessingTimeSeconds: z.number().optional(),
  cancer: z.boolean().optional(),
  cancerTimerMin: z.number().optional(),
  cancerTimerMax: z.number().optional(),
  cancerProcessingTimeSeconds: z.number().optional(),
  people: z.boolean().optional(),
  peopleTimerMin: z.number().optional(),
  peopleTimerMax: z.number().optional(),
  peopleProcessingTimeSeconds: z.number().optional(),
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
  href: z.string(),
});

export const ExtensionStorageSchema = z.object({
  enabled: z.boolean(),
  config: ExecutionConfigSchema,
  logs: z.array(LogEntrySchema),
  managedTabs: z.record(z.number(), z.number()),
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
