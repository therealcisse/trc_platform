import type {
  BackgroundCommands,
  CommandResponse,
  TabManagementCommand,
  BuyingStateCommand,
  ExtensionStorage
} from '@extension/types';

// Background service state
export interface BackgroundState {
  managedTabs: Map<number, number>;
  buyingOffers: Map<string, { id: string; timeout: number }>;
  watchedTimers: Map<string, boolean>;
}

// Message handler type
export type MessageHandler<T extends keyof BackgroundCommands> = (
  payload: BackgroundCommands[T],
  sender: chrome.runtime.MessageSender
) => Promise<CommandResponse>;

// Message handler registry
export interface MessageHandlerRegistry {
  handlers: Map<keyof BackgroundCommands, MessageHandler<any>>;
  register<T extends keyof BackgroundCommands>(
    command: T,
    handler: MessageHandler<T>
  ): void;
  handle(
    message: { type: keyof BackgroundCommands; payload: any },
    sender: chrome.runtime.MessageSender
  ): Promise<CommandResponse>;
}

// Tab management service interface
export interface TabManagementService {
  openTab(url: string, managedTab?: boolean): Promise<chrome.tabs.Tab>;
  closeTab(tabId: number): Promise<void>;
  reloadTab(tabId: number): Promise<void>;
  isManaged(tabId: number): boolean;
  markManaged(tabId: number): void;
  unmarkManaged(tabId: number): void;
}

// Storage service interface
export interface StorageService {
  get<K extends keyof ExtensionStorage>(key: K): Promise<ExtensionStorage[K] | undefined>;
  set<K extends keyof ExtensionStorage>(key: K, value: ExtensionStorage[K]): Promise<void>;
  remove<K extends keyof ExtensionStorage>(key: K): Promise<void>;
  addLog(message: string): Promise<void>;
}

// Buying state service interface
export interface BuyingStateService {
  markBuying(key: string, id: string, timeout: number): void;
  isBuying(key: string): { buying: boolean; id?: string };
  clearExpired(): void;
}

// Content script injection service
export interface ContentScriptService {
  injectScript(tabId: number, scriptPath: string): Promise<void>;
  injectFunction(tabId: number, func: Function, args?: any[]): Promise<any>;
  sendMessage(tabId: number, message: any): Promise<any>;
}
