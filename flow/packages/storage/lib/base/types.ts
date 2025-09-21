import type { StorageEnum } from './index.js';
import type { ValidatedBuyingOffer, ValidatedLogEntry, ValidatedProductStrategy } from '../validation/storage.js';
import type { ExecutionConfig, ExtensionStorage, Flow } from '@extension/types';

export type ValueOrUpdateType<D> = D | ((prev: D) => Promise<D> | D);

export type BaseStorageType<D> = {
  get: () => Promise<D>;
  set: (value: ValueOrUpdateType<D>) => Promise<void>;
  getSnapshot: () => D | null;
  subscribe: (listener: () => void) => () => void;
};

export type StorageConfigType<D = string> = {
  /**
   * Assign the {@link StorageEnum} to use.
   * @default Local
   */
  storageEnum?: StorageEnum;
  /**
   * Only for {@link StorageEnum.Session}: Grant Content scripts access to storage area?
   * @default false
   */
  sessionAccessForContentScripts?: boolean;
  /**
   * Keeps state live in sync between all instances of the extension. Like between popup, side panel and content scripts.
   * To allow chrome background scripts to stay in sync as well, use {@link StorageEnum.Session} storage area with
   * {@link StorageConfigType.sessionAccessForContentScripts} potentially also set to true.
   * @see https://stackoverflow.com/a/75637138/2763239
   * @default false
   */
  liveUpdate?: boolean;
  /**
   * An optional props for converting values from storage and into it.
   * @default undefined
   */
  serialization?: {
    /**
     * convert non-native values to string to be saved in storage
     */
    serialize: (value: D) => string;
    /**
     * convert string value from storage to non-native values
     */
    deserialize: (text: string) => D;
  };
};

export interface ThemeStateType {
  theme: 'light' | 'dark';
  isLight: boolean;
}

export type ThemeStorageType = BaseStorageType<ThemeStateType> & {
  toggle: () => Promise<void>;
};

export interface ExtensionStateType {
  config: ExecutionConfig;
  enabled: boolean;
}

export type ExtensionStorageType = BaseStorageType<ExtensionStorage> & {
  // Core methods
  toggleEnabled(): Promise<void>;
  updateConfig(updates: Partial<ExecutionConfig>): Promise<void>;

  // Buying state namespace
  buyingState: {
    markBuying(flowId: string, timeout: number): Promise<void>;
    checkBuying(flowId: string): Promise<{ buying: boolean }>;
    clearBuying(flowId: string): Promise<void>;
    clearExpired(): Promise<void>;
    getBuyingOffer(flowId: string): Promise<ValidatedBuyingOffer | undefined>;
  };

  // Tab management namespace
  tabManagement: {
    markManaged(tabId: number): Promise<void>;
    unmarkManaged(tabId: number): Promise<void>;
    isManaged(tabId: number): Promise<boolean>;
    getAllManagedTabs(): Promise<number[]>;
  };

  // Logs namespace
  logs: {
    addLog(message: string): Promise<void>;
    getLogs(): Promise<ValidatedLogEntry[]>;
    clearLogs(): Promise<void>;
  };

  // Product strategies namespace
  productStrategies: {
    get(): Promise<ValidatedProductStrategy[]>;
    set(strategies: ValidatedProductStrategy[]): Promise<void>;
    clear(): Promise<void>;
  };

  flows: {
    cleanupOldFlows(): Promise<void>;
    startFlow(flow: Flow): Promise<boolean>;
    doneFlow(id: string): Promise<void>;
    getFlow(id: string): Promise<Flow | undefined>;
  };

  // Actions methods
  restoreDefaults(): Promise<void>;
  clearFlowDatabase(): Promise<void>;
};
