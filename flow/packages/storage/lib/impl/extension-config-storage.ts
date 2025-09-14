import { createStorage, StorageEnum, ExtensionStorageType, ExtensionStateType } from '../base/index.js';
import type { ExecutionConfig } from '@extension/types';

export const DEFAULT_CONFIG: ExtensionStateType = {
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
};

const storage = createStorage<ExtensionStateType>('extension-config-storage-key', DEFAULT_CONFIG, {
  storageEnum: StorageEnum.Local,
  liveUpdate: true,
});

export const extensionConfigStorage: ExtensionStorageType = {
  ...storage,
  toggleEnabled: async () => {
    await storage.set(currentState => ({
      ...currentState,
      enabled: !currentState.enabled,
    }));
  },
  updateConfig: async (updates: Partial<ExecutionConfig>) => {
    await storage.set(currentState => ({
      ...currentState,
      config: {
        ...currentState.config,
        ...updates,
      },
    }));
  },
};
