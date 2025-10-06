import { createStorage, StorageEnum } from '../base/index.js';
import { validateStorageData, ExtensionStorageSchema } from '../validation/storage.js';
import type { ExtensionStorageType } from '../base/index.js';
import type { ExecutionConfig, ExtensionStorage } from '@extension/types';
import { LocalTime } from '@extension/types';

export const DEFAULT_OPERATIONAL_HOURS_CONFIG = {
  enabled: false,
  min: LocalTime.of(8, 0, 0),
  max: LocalTime.of(20, 0, 0),
} as const;

export const DEFAULT_CONFIG: ExtensionStorage = {
  schemaVersion: 0,
  enabled: true,
  debugMode: false,
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
        min: LocalTime.of(8, 0, 0),
        max: LocalTime.of(8, 1, 0),
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
        min: LocalTime.of(8, 0, 0),
        max: LocalTime.of(8, 1, 0),
        duration: 3,
        enabled: true,
      },
    ],

    // Accident defaults
    accidents: true,
    accidentProcessingTimeSeconds: 15,
    accidentProcessingTimeWindows: [],
  },
};

const storage = createStorage<ExtensionStorage>('extension-config-storage-key', DEFAULT_CONFIG, {
  storageEnum: StorageEnum.Sync,
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

  toggleDebugMode: async () => {
    await storage.set(currentState =>
      validateStorageData(ExtensionStorageSchema, {
        ...currentState,
        debugMode: !currentState.debugMode,
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

  // Actions methods
  async restoreDefaults() {
    await storage.set(() => validateStorageData(ExtensionStorageSchema, DEFAULT_CONFIG));
  },
};
