import { createStorage, StorageEnum } from '../base/index.js';
import type { ExecutionConfig } from '@extension/shared/app/types';

export interface ConfigState {
  config: ExecutionConfig;
  enabled: boolean;
}

export interface ConfigStorage {
  get: () => Promise<ConfigState>;
  set: (value: ConfigState | ((prev: ConfigState) => ConfigState)) => Promise<void>;
  getSnapshot: () => ConfigState | null;
  subscribe: (listener: () => void) => () => void;
  toggleEnabled: () => Promise<void>;
  updateConfig: (updates: Partial<ExecutionConfig>) => Promise<void>;
}

const DEFAULT_CONFIG: ConfigState = {
  enabled: true,
  config: {
    operationalHours: {
      0: { enabled: false, min: 0, max: 0 }, // Sunday
      1: { enabled: true, min: 8, max: 17 }, // Monday
      2: { enabled: true, min: 8, max: 17 }, // Tuesday
      3: { enabled: true, min: 8, max: 17 }, // Wednesday
      4: { enabled: true, min: 8, max: 17 }, // Thursday
      5: { enabled: true, min: 8, max: 17 }, // Friday
      6: { enabled: false, min: 0, max: 0 }, // Saturday
    },
    emailMode: true,
    emailRefreshMin: 30,
    emailRefreshMax: 60,
    timerMode: false,
    randomDelay: {
      min: 5,
      max: 30,
    },
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

const storage = createStorage<ConfigState>('extension-config-storage-key', DEFAULT_CONFIG, {
  storageEnum: StorageEnum.Sync,
  liveUpdate: true,
});

export const extensionConfigStorage: ConfigStorage = {
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
