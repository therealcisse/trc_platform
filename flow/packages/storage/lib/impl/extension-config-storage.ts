import { createStorage, StorageEnum } from '../base/index.js';
import {
  validateStorageData,
  ExtensionStorageSchema,
  BuyingOfferSchema,
  LogEntrySchema,
  ProductStrategySchema,
  StoredProductStrategySchema,
} from '../validation/storage.js';
import type { ExtensionStorageType } from '../base/index.js';
import type { ExecutionConfig, ExtensionStorage, Flow, StoredProductStrategy } from '@extension/types';

export const DEFAULT_OPERATIONAL_HOURS_CONFIG = {
  enabled: false,
  min: 8,
  max: 17,
} as const;

export const DEFAULT_CONFIG: ExtensionStorage = {
  enabled: true,
  config: {
    operationalHours: {
      Sunday: { ...DEFAULT_OPERATIONAL_HOURS_CONFIG, enabled: true },
      Monday: { ...DEFAULT_OPERATIONAL_HOURS_CONFIG, enabled: true },
      Tuesday: { ...DEFAULT_OPERATIONAL_HOURS_CONFIG, enabled: true },
      Wednesday: { ...DEFAULT_OPERATIONAL_HOURS_CONFIG, enabled: true },
      Thursday: { ...DEFAULT_OPERATIONAL_HOURS_CONFIG, enabled: true },
      Friday: { ...DEFAULT_OPERATIONAL_HOURS_CONFIG, enabled: true },
      Saturday: { ...DEFAULT_OPERATIONAL_HOURS_CONFIG, enabled: true },
    },
    emailMode: true,
    emailRefreshMin: 30,
    emailRefreshMax: 60,

    // Inbox mode defaults
    inboxMode: true,

    // Product strategies
    animals: true,
    animalProcessingTimeSeconds: 0,

    cancer: true,
    cancerProcessingTimeSeconds: 0,

    people: true,
    peopleProcessingTimeSeconds: 0,
  },
  // Initialize empty storage collections
  logs: [],
  managedTabs: {},
  buyingOffers: {},
  productStrategies: [],
  flows: {},
};

const storage = createStorage<ExtensionStorage>('extension-config-storage-key', DEFAULT_CONFIG, {
  storageEnum: StorageEnum.Local,
  liveUpdate: true,
});

export const extensionConfigStorage: ExtensionStorageType = {
  ...storage,

  // Flow management namespace
  flows: {
    async cleanupOldFlows(): Promise<void> {
      const dayAgo = Date.now() - 24 * 60 * 60 * 1000;
      const removed: string[] = [];

      await storage.set(currentState => {
        const newFlows = { ...currentState.flows };
        for (const [id, flow] of Object.entries(newFlows)) {
          if (flow.timestamp < dayAgo) {
            removed.push(id);
            delete newFlows[id];
          }
        }
        return validateStorageData(ExtensionStorageSchema, {
          ...currentState,
          flows: newFlows,
        });
      });

      if (removed.length > 0) {
        await extensionConfigStorage.logs.addLog(
          `[Flow] Cleaned up ${removed.length} old flows: ${removed.join(', ')}`,
        );
      }
    },

    async startFlow(flow: Flow): Promise<boolean> {
      // Trigger cleanup
      void this.cleanupOldFlows();

      const current = await storage.get();
      if (current.flows[flow.id]) {
        return true;
      }

      await storage.set(currentState =>
        validateStorageData(ExtensionStorageSchema, {
          ...currentState,
          flows: {
            ...currentState.flows,
            [flow.id]: flow,
          },
        }),
      );
      return false;
    },

    async doneFlow(id: string): Promise<void> {
      await storage.set(currentState => {
        const flow = currentState.flows[id];
        if (flow) {
          return validateStorageData(ExtensionStorageSchema, {
            ...currentState,
            flows: {
              ...currentState.flows,
              [id]: { ...flow, status: 'done' },
            },
          });
        }
        return currentState;
      });
    },

    async getFlow(id: string): Promise<Flow | undefined> {
      const current = await storage.get();
      return current.flows[id];
    },
  },

  // Core methods
  toggleEnabled: async () => {
    await storage.set(currentState =>
      validateStorageData(ExtensionStorageSchema, {
        ...currentState,
        enabled: !currentState.enabled,
      }),
    );
  },

  updateConfig: async (updates: Partial<ExecutionConfig>) => {
    await storage.set(currentState =>
      validateStorageData(ExtensionStorageSchema, {
        ...currentState,
        config: {
          ...currentState.config,
          ...updates,
        },
      }),
    );
  },

  // Buying state namespace
  buyingState: {
    async markBuying(flowId: string, timeout: number) {
      const offer = validateStorageData(BuyingOfferSchema, { id: flowId, timeout });
      await storage.set(currentState =>
        validateStorageData(ExtensionStorageSchema, {
          ...currentState,
          buyingOffers: {
            ...currentState.buyingOffers,
            [flowId]: offer,
          },
        }),
      );
    },

    async checkBuying(flowId: string) {
      const current = await storage.get();
      const offer = current.buyingOffers[flowId];

      if (!offer) return { buying: false };

      const validated = validateStorageData(BuyingOfferSchema, offer);
      if (Date.now() > validated.timeout) {
        await this.clearBuying(flowId);
        return { buying: false };
      }

      return { buying: true };
    },

    async clearBuying(flowId: string) {
      await storage.set(currentState => {
        const { [flowId]: _, ...remainingOffers } = currentState.buyingOffers;
        return validateStorageData(ExtensionStorageSchema, {
          ...currentState,
          buyingOffers: remainingOffers,
        });
      });
    },

    async clearExpired() {
      const current = await storage.get();
      const now = Date.now();

      await storage.set(currentState => {
        const validOffers = Object.entries(currentState.buyingOffers)
          .filter(([_, offer]) => offer.timeout > now)
          .reduce((acc, [key, offer]) => ({ ...acc, [key]: offer }), {});

        return validateStorageData(ExtensionStorageSchema, {
          ...currentState,
          buyingOffers: validOffers,
        });
      });
    },

    async getBuyingOffer(flowId: string) {
      const current = await storage.get();
      const offer = current.buyingOffers[flowId];
      return offer ? validateStorageData(BuyingOfferSchema, offer) : undefined;
    },
  },

  // Tab management namespace
  tabManagement: {
    async markManaged(tabId: number) {
      await storage.set(currentState =>
        validateStorageData(ExtensionStorageSchema, {
          ...currentState,
          managedTabs: {
            ...currentState.managedTabs,
            [tabId]: Date.now(),
          },
        }),
      );
    },

    async unmarkManaged(tabId: number) {
      await storage.set(currentState => {
        const { [tabId]: _, ...remainingTabs } = currentState.managedTabs;
        return validateStorageData(ExtensionStorageSchema, {
          ...currentState,
          managedTabs: remainingTabs,
        });
      });
    },

    async isManaged(tabId: number) {
      const current = await storage.get();
      return tabId in current.managedTabs;
    },

    async getAllManagedTabs() {
      const current = await storage.get();
      return Object.keys(current.managedTabs).map(Number);
    },
  },

  // Logs namespace
  logs: {
    async addLog(message: string) {
      const logEntry = validateStorageData(LogEntrySchema, {
        timestamp: Date.now(),
        message,
      });

      await storage.set(currentState =>
        validateStorageData(ExtensionStorageSchema, {
          ...currentState,
          logs: [...currentState.logs, logEntry],
        }),
      );
    },

    async getLogs() {
      const current = await storage.get();
      return current.logs.map(log => validateStorageData(LogEntrySchema, log));
    },

    async clearLogs() {
      await storage.set(currentState =>
        validateStorageData(ExtensionStorageSchema, {
          ...currentState,
          logs: [],
        }),
      );
    },
  },

  // Product strategies namespace
  productStrategies: {
    async get() {
      const current = await storage.get();
      return current.productStrategies.map(strategy => validateStorageData(ProductStrategySchema, strategy));
    },

    async set(strategies) {
      // Convert ProductStrategy to StoredProductStrategy
      const storedStrategies: StoredProductStrategy[] = strategies.map(strategy => ({
        id: strategy.id,
        name: strategy.name,
        patterns: strategy.patterns,
      }));

      const validatedStrategies = storedStrategies.map(strategy =>
        validateStorageData(StoredProductStrategySchema, strategy),
      );

      await storage.set(currentState =>
        validateStorageData(ExtensionStorageSchema, {
          ...currentState,
          productStrategies: validatedStrategies,
        }),
      );
    },

    async clear() {
      await storage.set(currentState =>
        validateStorageData(ExtensionStorageSchema, {
          ...currentState,
          productStrategies: [],
        }),
      );
    },
  },
};
