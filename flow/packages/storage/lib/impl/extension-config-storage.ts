import { createStorage, StorageEnum } from '../base/index.js';
import {
  validateStorageData,
  ExtensionStorageSchema,
  BuyingOfferSchema,
  LogEntrySchema,
  ProductStrategySchema,
  StoredProductStrategySchema,
  ManagedTabInfoSchema,
} from '../validation/storage.js';
import type { ExtensionStorageType } from '../base/index.js';
import type { ExecutionConfig, ExtensionStorage, Flow, StoredProductStrategy } from '@extension/types';
import { LocalTime } from '@extension/types';

export const DEFAULT_OPERATIONAL_HOURS_CONFIG = {
  enabled: false,
  min: LocalTime.of(8, 0),
  max: LocalTime.of(20, 0),
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
    emailMode: false,
    emailRefreshMin: 30,
    emailRefreshMax: 60,

    products: [],

    // Inbox mode defaults
    inboxMode: true,
    inboxReloadSeconds: [4, 7],
    inboxPostReloadDelayMs: 0,
    inboxMaxLinksPerScan: 10,
    inboxInterOpenDelayMs: 400,

    // Product strategies
    animal: { dogs: true, cats: true },
    animalProcessingTimeSeconds: 14,
    animalProcessingTimeWindows: [
      {
        id: 'animals-8am',
        min: LocalTime.of(8, 0),
        max: LocalTime.of(8, 1),
        duration: 3,
        enabled: true,
      },
    ],

    cancer: true,
    cancerProcessingTimeSeconds: 15,
    cancerProcessingTimeWindows: [],

    health: true,
    healthProcessingTimeSeconds: 12,
    healthProcessingTimeWindows: [
      {
        id: 'health-8am',
        min: LocalTime.of(8, 0),
        max: LocalTime.of(8, 1),
        duration: 3,
        enabled: true,
      },
    ],

    // Accident defaults
    accidents: true,
    accidentProcessingTimeSeconds: 15,
    accidentProcessingTimeWindows: [],
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
      // void this.cleanupOldFlows();

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
              [id]: { ...flow, status: 'done', doneTimestamp: Date.now() },
            },
          });
        }
        return currentState;
      });
    },

    async failedFlow(id: string): Promise<void> {
      await storage.set(currentState => {
        const flow = currentState.flows[id];
        if (flow) {
          return validateStorageData(ExtensionStorageSchema, {
            ...currentState,
            flows: {
              ...currentState.flows,
              [id]: { ...flow, status: 'failed', doneTimestamp: Date.now() },
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

    async getAllFlowIds(): Promise<string[]> {
      const current = await storage.get();
      return Object.keys(current.flows);
    },

    async getAllFlows(): Promise<Flow[]> {
      const current = await storage.get();
      return Object.values(current.flows);
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

    async purgeBuying(flowId: string) {
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
    async markManaged(tabId: number, flowId: string) {
      const now = Date.now();
      const tabInfo = validateStorageData(ManagedTabInfoSchema, {
        flowId,
        createdAt: now,
        lastActive: now,
      });

      await storage.set(currentState =>
        validateStorageData(ExtensionStorageSchema, {
          ...currentState,
          managedTabs: {
            ...currentState.managedTabs,
            [tabId]: tabInfo,
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

    async updateActivity(tabId: number) {
      await storage.set(currentState => {
        const tabInfo = currentState.managedTabs[tabId];
        if (tabInfo) {
          const updatedTabInfo = validateStorageData(ManagedTabInfoSchema, {
            ...tabInfo,
            lastActive: Date.now(),
          });
          return validateStorageData(ExtensionStorageSchema, {
            ...currentState,
            managedTabs: {
              ...currentState.managedTabs,
              [tabId]: updatedTabInfo,
            },
          });
        }
        return currentState;
      });
    },

    async isManaged(tabId: number) {
      const current = await storage.get();
      return String(tabId) in current.managedTabs;
    },

    async getAllManagedTabs() {
      const current = await storage.get();
      return Object.keys(current.managedTabs).map(Number);
    },

    async getTabCount() {
      const current = await storage.get();
      return Object.keys(current.managedTabs).length;
    },

    async getTabsByFlow(flowId: string) {
      const current = await storage.get();
      return Object.entries(current.managedTabs)
        .filter(([_, tabInfo]) => tabInfo.flowId === flowId)
        .map(([tabId]) => Number(tabId));
    },

    async closeAllTabsForFlow(flowId: string) {
      const current = await storage.get();
      const tabsToClose = Object.entries(current.managedTabs)
        .filter(([_, tabInfo]) => tabInfo.flowId === flowId)
        .map(([tabId]) => Number(tabId));

      // Close actual tabs
      for (const tabId of tabsToClose) {
        try {
          await chrome.tabs.remove(tabId);
        } catch (error) {
          // Tab might already be closed, continue
        }
      }

      // Remove from storage
      await storage.set(currentState => {
        const newManagedTabs = { ...currentState.managedTabs };
        tabsToClose.forEach(tabId => {
          delete newManagedTabs[String(tabId)];
        });

        return validateStorageData(ExtensionStorageSchema, {
          ...currentState,
          managedTabs: newManagedTabs,
        });
      });
    },

    async cleanupStaleTabs(staleTimeout: number = 5 * 60 * 1000) {
      const current = await storage.get();
      const now = Date.now();
      const staleTabIds: number[] = [];

      // Find stale tabs
      Object.entries(current.managedTabs).forEach(([tabId, tabInfo]) => {
        if (now - tabInfo.lastActive > staleTimeout) {
          staleTabIds.push(Number(tabId));
        }
      });

      // Close stale tabs
      for (const tabId of staleTabIds) {
        try {
          await chrome.tabs.remove(tabId);
        } catch {
          // Tab might already be closed
        }
      }

      // Remove from storage if any were found
      if (staleTabIds.length > 0) {
        await storage.set(currentState => {
          const newManagedTabs = { ...currentState.managedTabs };
          staleTabIds.forEach(tabId => {
            delete newManagedTabs[String(tabId)];
          });

          return validateStorageData(ExtensionStorageSchema, {
            ...currentState,
            managedTabs: newManagedTabs,
          });
        });
      }

      return staleTabIds.length;
    },

    async validateExistingTabs() {
      const current = await storage.get();
      const tabIds = Object.keys(current.managedTabs).map(Number);
      const invalidTabIds: number[] = [];

      // Check which tabs still exist
      for (const tabId of tabIds) {
        try {
          await chrome.tabs.get(tabId);
        } catch {
          // Tab no longer exists
          invalidTabIds.push(tabId);
        }
      }

      // Remove invalid tabs from storage
      if (invalidTabIds.length > 0) {
        await storage.set(currentState => {
          const newManagedTabs = { ...currentState.managedTabs };
          invalidTabIds.forEach(tabId => {
            delete newManagedTabs[String(tabId)];
          });

          return validateStorageData(ExtensionStorageSchema, {
            ...currentState,
            managedTabs: newManagedTabs,
          });
        });
      }

      return invalidTabIds.length;
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

  // Actions methods
  async restoreDefaults() {
    await storage.set(() => validateStorageData(ExtensionStorageSchema, DEFAULT_CONFIG));
  },

  async clearFlowDatabase() {
    const flows = (await storage.get()).flows;

    for (const [id, _] of Object.entries(flows)) {
      await chrome.runtime.sendMessage({
        type: 'state.buying',
        payload: {
          action: 'purge',
          flowId: id,
        },
      });
    }

    await storage.set(currentState =>
      validateStorageData(ExtensionStorageSchema, {
        ...currentState,
        flows: {},
        logs: [],
      }),
    );
  },
};
