import { LocalTimeUtils } from './LocalTimeUtils.js';

// Core matcher and executor types
export interface Matcher {
  id: string;
  name: string;
  urlPatterns: string[];
  domPreconditions?: DomPrecondition[];
  enabled: boolean;
  priority?: number;
  run(): Promise<void>;
}

export interface DomPrecondition {
  selector: string;
  shouldExist: boolean;
  timeout?: number;
}

// Execution context and results
export interface ExecutionContext {
  url: string;
  matcherId: string;
  config: ExecutionConfig;
  timeout?: number;
  dryRun?: boolean;
}

export interface ExecutionConfig {
  // Inbox mode configuration
  inboxMode: boolean;
  inboxReloadSeconds: number[]; // [0, 5] means reload at 0 and 5 seconds of each minute
  inboxPostReloadDelayMs: number; // Delay after reload before scanning
  inboxMaxLinksPerScan: number; // Max links to open per scan
  inboxInterOpenDelayMs: number; // Delay between opening links
  inboxBuysImmediately: boolean; // When true, non-lead inbox items open Buy Offer directly

  // API Authentication
  token?: string;

  operationalHours: OperationalHours;
  emailMode: boolean;
  emailRefreshMin: number;
  emailRefreshMax: number;

  // Animal insurance product strategy
  animal: {
    dogs: boolean;
    cats: boolean;
  };
  animalProcessingTimeSeconds: number;
  animalProcessingTimeWindows: ProcessingTimeWindow[];

  // Cancer scan product strategy
  cancer: boolean;
  cancerProcessingTimeSeconds: number;
  cancerProcessingTimeWindows: ProcessingTimeWindow[];

  // Health insurance product strategy
  health: boolean;
  healthProcessingTimeSeconds: number;
  healthProcessingTimeWindows: ProcessingTimeWindow[];

  // Accident insurance product strategy
  accidents: boolean;
  accidentProcessingTimeSeconds: number;
  accidentProcessingTimeWindows: ProcessingTimeWindow[];
}

export interface OperationalHours {
  [day: string]: {
    enabled: boolean;
    min: LocalTime;
    max: LocalTime;
  };
}

export interface ProcessingTimeWindow {
  id: string;
  min: LocalTime;
  max: LocalTime;
  duration: number;
  enabled: boolean;
}

export interface InboxSelectors {
  titleLinks: string; // Selector for title column links
  rows: string; // Selector for message rows
  requestTimestampElement: string; // Selector for request timestamp (Erhalten column)
}

export interface ExecutionResult {
  success: boolean;
  matcherId: string;
  executorName: string;
  data?: any;
  error?: string;
  telemetry?: TelemetryData;
}

// Product strategy abstraction

// Message types for background communication

export interface CommandResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  requestId: string;
}

// Background command definitions
export interface EmailFlowPayload {
  type: 'email';
  id: string;
}

export interface ManualFlowPayload {
  type: 'manual';
  id: string;
}

export interface InboxFlowPayload {
  type: 'inbox';
  id: string;
  requestTimestamp: number;
}

export type FlowPayload = EmailFlowPayload | ManualFlowPayload | InboxFlowPayload;

export interface BackgroundCommands {
  'item.printProductConfirmation': PDFCommand;
  'tab.manage': TabManagementCommand;
  'state.buying': BuyingStateCommand;
  'extension.log': {
    matcherId: string;
    flowId?: string;
    messages: Array<{ message: string; timestamp: number; level: 'info' | 'warn' | 'error' | 'debug' }>;
    metadata?: Record<string, any>;
    timestamp: number;
  };
  'extension.error': ErrorReport;
  'extension.telemetry': { events: TelemetryEvent[] };
  'extension.getConfig': {};
  'extension.toggleEnabled': {};
  'image.solve': { imageData: string; flowId: string };
  'flows.scheduleCloseAfterNavigation': { flowId: string; timeoutMs: number };
  'extension.startFlow': FlowPayload;
  'extension.getFlow': { id: string };
  'extension.getAllFlows': {};
  'logs.query': {
    action: 'getAllLogs' | 'getFlowLogs' | 'getMatcherLogs' | 'exportFlowTimeline' | 'clearOldLogs' | 'clearAllLogs';
    flowId?: string;
    matcherId?: string;
    olderThanMs?: number;
  };
  'logs.stats': {};
}

export interface EmailSelectors {
  unreadEmail: string;
  emailBody: string;
  markAsReadButton: string;
}

export interface PDFCommand {
  selectors: PdfSelectors;
}

export interface ItemSelectors {
  buyButton: string;
}

export interface PdfSelectors {
  productTitle: string;
}

export interface MyOfferSelectors {
  titleLink: string;
  itemLink: string;
  pdfLink: string;
}

export interface BuyOfferSelectors {
  input: string;
  img: string;
  productTitle: string;
  buyFormButton: string;
}

export interface TabManagementCommand {
  action:
    | 'open'
    | 'close'
    | 'reload'
    | 'manage'
    | 'unmanage'
    | 'isManaged'
    | 'addManagedTab'
    | 'updateActivity'
    | 'getTabCount'
    | 'closeAllTabs'
    | 'cleanupStale';
  tabId?: number;
  url?: string;
  flowId?: string;
}

export interface BuyingStateCommand {
  action: 'mark' | 'check' | 'clear';
  flowId: string;
  timeout?: number;
}

// Telemetry and logging
export interface TelemetryEvent {
  eventName: string;
  matcherId?: string;
  executorName?: string;
  metadata?: Record<string, any>;
  timestamp: number;
}

// Error reporting from content scripts to background
export interface ErrorReport {
  matcherId: string;
  flowId?: string;
  source: 'window.error' | 'unhandledrejection' | 'manual' | string;
  message: string;
  name?: string;
  stack?: string;
  filename?: string;
  lineno?: number;
  colno?: number;
  reason?: unknown;
  url?: string;
  userAgent?: string;
  timestamp: number;
  metadata?: Record<string, unknown>;
}

export interface TelemetryData {
  startTime: number;
  endTime: number;
  errors: Error[];
}

export interface LogEntry {
  type: string;
  messages: string[];
  timestamp: string;
}

// DOM utilities
export interface WaitOptions {
  timeout?: number;
  interval?: number;
  visible?: boolean;
}

export interface ClickOptions {
  verify?: boolean;
  scroll?: boolean;
}

// Storage types
export interface Flow {
  id: string;
  timestamp: number;
  requestTimestamp: number;
  status: 'running' | 'done' | 'failed';
  source: 'email' | 'inbox' | 'manual';
  doneTimestamp?: number;
}

export type FlowState = Record<string, Flow>;

export interface ManagedTabInfo {
  flowId: string;
  createdAt: number;
  lastActive: number;
}

export interface ExtensionStorage {
  schemaVersion: 0; // later 0 | 1 | ...
  enabled: boolean;
  debugMode: boolean;
  config: ExecutionConfig;
}

export interface ExtensionRuntime {
  logs: {
    timestamp: number;
    message: string;
  }[];
  managedTabs: Record<string, ManagedTabInfo>;
  buyingOffers: Record<string, BuyingOffer>;
  flows: FlowState;
}

export interface BuyingOffer {
  id: string;
  timeout: number;
}

// Utility types
export type LocalDate = {
  toString(): string;
  getHours(): number;
  getMinutes(): number;
  getDay(): number;
};

// Message handler type
export type MessageHandler<T extends keyof BackgroundCommands> = (
  payload: BackgroundCommands[T],
  sender: chrome.runtime.MessageSender,
) => Promise<CommandResponse>;

// Message handler registry
export interface MessageHandlerRegistry {
  handlers: Map<keyof BackgroundCommands, MessageHandler<any>>;
  register<T extends keyof BackgroundCommands>(command: T, handler: MessageHandler<T>): void;
  handle(
    message: { type: keyof BackgroundCommands; payload: any },
    sender: chrome.runtime.MessageSender,
  ): Promise<CommandResponse>;
}

// Tab management service interface
export interface TabManagementService {
  openTab(url: string, managedTab?: boolean): Promise<chrome.tabs.Tab>;
  closeTab(tabId: number): Promise<void>;
  reloadTab(tabId: number): Promise<void>;
  isManaged(tabId: number): Promise<boolean>;
  markManaged(tabId: number, flowId: string): void;
  unmarkManaged(tabId: number): void;
}

// Buying state service interface
export interface BuyingStateService {
  markBuying(flowId: string, timeout: number): Promise<void>;
  isBuying(flowId: string): Promise<{ buying: boolean }>;
  clearBuying(flowId: string): Promise<void>;
  clearExpired(): Promise<void>;
  getBuyingOffer(flowId: string): Promise<BuyingOffer | undefined>;
}

// Product type discriminator
export type ProductType = 'HEALTH' | 'ANIMAL' | 'CANCER' | 'ACCIDENT' | 'INVALID';

// Base interface for valid products
interface BaseValidProduct {
  name: string;
  allowed: boolean;
}

// Health product interface
export interface HealthProduct extends BaseValidProduct {
  type: 'HEALTH';
  insuredAge: number;
  aboveIncomeLimit?: boolean;
}

// Animal product interface
export interface AnimalProduct extends BaseValidProduct {
  type: 'ANIMAL';
  insuredType: string;
  insuredAge: number;
}

// Cancer product interface
export interface CancerProduct extends BaseValidProduct {
  type: 'CANCER';
}

// Accident product interface
export interface AccidentProduct extends BaseValidProduct {
  type: 'ACCIDENT';
}

// Invalid product interface
export interface InvalidProduct {
  type: 'INVALID';
  name: string;
  allowed: false;
  error: string;
}

// Union type of all possible products
export type Product = HealthProduct | AnimalProduct | CancerProduct | AccidentProduct | InvalidProduct;

// Helper type for title parsing results
export interface ParsedTitle {
  name: string;
  insuredType?: string;
  insuredAge?: number;
  meta: {
    aboveIncomeLimit?: boolean;
    [key: string]: any;
  };
}

// Type guards
export function isHealthProduct(product: Product): product is HealthProduct {
  return product.type === 'HEALTH';
}

export function isAnimalProduct(product: Product): product is AnimalProduct {
  return product.type === 'ANIMAL';
}

export function isCancerProduct(product: Product): product is CancerProduct {
  return product.type === 'CANCER';
}

export function isAccidentProduct(product: Product): product is AccidentProduct {
  return product.type === 'ACCIDENT';
}

export function isInvalidProduct(product: Product): product is InvalidProduct {
  return product.type === 'INVALID';
}

// Local time value object for minute-precision operational hours
export class LocalTime {
  readonly hour: number;
  readonly minute: number;
  readonly second: number;

  private constructor(hour: number, minute: number, second: number = 0) {
    if (!Number.isInteger(hour) || hour < 0 || hour > 23) {
      throw new RangeError('Hour must be 0–23');
    }
    if (!Number.isInteger(minute) || minute < 0 || minute > 59) {
      throw new RangeError('Minute must be 0–59');
    }
    if (!Number.isInteger(second) || second < 0 || second > 59) {
      throw new RangeError('Second must be 0–59');
    }
    this.hour = hour;
    this.minute = minute;
    this.second = second ?? 0;
  }

  static of(hour: number, minute: number, second: number = 0): LocalTime {
    return new LocalTime(hour, minute, second);
  }

  static now(): LocalTime {
    const d = new Date();
    return new LocalTime(d.getHours(), d.getMinutes(), d.getSeconds());
  }

  static parse(str: string): LocalTime {
    const match = /^(\d{2}):(\d{2})(?::(\d{2}))?$/.exec(str);
    if (!match) throw new Error('Invalid time string: ' + str);
    const [, h, m, s] = match;
    return new LocalTime(+h, +m, s ? +s : 0);
  }

  toString(): string {
    const pad = (n: number) => String(n).padStart(2, '0');
    return `${pad(this.hour)}:${pad(this.minute)}:${pad(this.second)}`;
  }

  toMinutesOfDay(): number {
    return LocalTimeUtils.toMinutesOfDay(this);
  }

  toSecondsOfDay(): number {
    return LocalTimeUtils.toSecondsOfDay(this);
  }

  compareTo(other: LocalTime): number {
    return this.toSecondsOfDay() - other.toSecondsOfDay();
  }

  plusMinutes(mins: number): LocalTime {
    const totalSeconds = (this.toSecondsOfDay() + mins * 60 + 24 * 60 * 60) % (24 * 60 * 60);
    const hour = Math.floor(totalSeconds / 3600);
    const minute = Math.floor((totalSeconds % 3600) / 60);
    const second = totalSeconds % 60;
    return new LocalTime(hour, minute, second);
  }
}
