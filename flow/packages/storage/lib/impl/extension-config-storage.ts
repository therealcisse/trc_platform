import { createStorage, StorageEnum, ExtensionStorageType } from '../base/index.js';
import type { ExecutionConfig, ExtensionStorage } from '@extension/types';
import {
  validateStorageData,
  ExtensionStorageSchema,
  BuyingOfferSchema,
  LogEntrySchema,
  ProductStrategySchema,
  StoredProductStrategySchema,
} from '../validation/storage.js';

import type { StoredProductStrategy } from '@extension/types';

export const DEFAULT_CONFIG: ExtensionStorage = {
  enabled: true,
  config: {
    operationalHours: {
      0: { enabled: true, min: 8, max: 17 }, // Sunday
      1: { enabled: true, min: 8, max: 17 }, // Monday
      2: { enabled: true, min: 8, max: 17 }, // Tuesday
      3: { enabled: true, min: 8, max: 17 }, // Wednesday
      4: { enabled: true, min: 8, max: 17 }, // Thursday
      5: { enabled: true, min: 8, max: 17 }, // Friday
      6: { enabled: true, min: 8, max: 17 }, // Saturday
    },
    emailMode: true,
    emailRefreshMin: 30,
    emailRefreshMax: 60,

    // Inbox mode defaults
    inboxMode: true,
    inboxRefreshMin: 30,
    inboxRefreshMax: 60,

    // Product strategies
    animals: true,
    animalTimerMin: 10,
    animalTimerMax: 30,

    cancer: true,
    cancerTimerMin: 15,
    cancerTimerMax: 45,

    people: true,
    peopleTimerMin: 20,
    peopleTimerMax: 60,
  },
  // Initialize empty storage collections
  logs: [],
  managedTabs: {},
  buyingOffers: {},
  productStrategies: [],
};

const storage = createStorage<ExtensionStorage>('extension-config-storage-key', DEFAULT_CONFIG, {
  storageEnum: StorageEnum.Local,
  liveUpdate: true,
});

export const extensionConfigStorage: ExtensionStorageType = {
  ...storage,

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
    async markBuying(key: string, id: string, timeout: number) {
      const offer = validateStorageData(BuyingOfferSchema, { id, timeout });
      await storage.set(currentState =>
        validateStorageData(ExtensionStorageSchema, {
          ...currentState,
          buyingOffers: {
            ...currentState.buyingOffers,
            [key]: offer,
          },
        }),
      );
    },

    async checkBuying(key: string) {
      const current = await storage.get();
      const offer = current.buyingOffers[key];

      if (!offer) return { buying: false };

      const validated = validateStorageData(BuyingOfferSchema, offer);
      if (Date.now() > validated.timeout) {
        await this.clearBuying(key);
        return { buying: false };
      }

      return { buying: true, id: validated.id };
    },

    async clearBuying(key: string) {
      await storage.set(currentState => {
        const { [key]: _, ...remainingOffers } = currentState.buyingOffers;
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

    async getBuyingOffer(key: string) {
      const current = await storage.get();
      const offer = current.buyingOffers[key];
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
