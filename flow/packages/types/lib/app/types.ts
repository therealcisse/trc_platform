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
  tabId: number;
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

  // API Authentication
  token?: string;

  operationalHours: OperationalHours;
  emailMode: boolean;
  emailRefreshMin: number;
  emailRefreshMax: number;

  products: ProductConfig[];

  // Animal insurance product strategy
  animals: boolean;
  animalTimerMin: number;
  animalTimerMax: number;
  animalProcessingTimeSeconds: number;
  animalProcessingTimeWindows: ProcessingTimeWindow[];

  // Cancer scan product strategy
  cancer: boolean;
  cancerTimerMin: number;
  cancerTimerMax: number;
  cancerProcessingTimeSeconds: number;
  cancerProcessingTimeWindows: ProcessingTimeWindow[];

  // People insurance product strategy
  people: boolean;
  peopleTimerMin: number;
  peopleTimerMax: number;
  peopleProcessingTimeSeconds: number;
  peopleProcessingTimeWindows: ProcessingTimeWindow[];

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

export interface DelayConfig {
  min: number;
  max: number;
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
export interface ProductStrategy {
  id: string;
  name: string;
  patterns: ProductPattern[];
  isMatch(doc: Document): boolean;
  selectActionTargets(doc: Document): Element[];
  extractMetadata(doc: Document): ProductMetadata;
}

export interface ProductPattern {
  insuredType?: string;
  insuredAge?: { min: number; max: number };
  meta?: Record<string, any>;
}

export interface StoredProductStrategy {
  id: string;
  name: string;
  patterns: ProductPattern[];
}

export interface ProductConfig {
  text: string;
  insuredType: string;
  insuredAge: { min: number; max: number };
  meta?: Record<string, any>;
}

export interface ProductMetadata {
  name: string;
  insuredType: string;
  insuredAge: number;
  price?: number;
  validity?: string;
  rawText?: string;
}

// Message types for background communication
export interface BackgroundMessage<T = any> {
  type: string;
  payload: T;
  timestamp: number;
  requestId: string;
}

export interface CommandResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  requestId: string;
}

export type FlowAction = 'pdf' | 'offer';

// Background command definitions
export interface EmailFlowPayload {
  type: 'email';
  action: FlowAction;
  id: string;
}

export interface InboxFlowPayload {
  type: 'inbox';
  id: string;
  action: FlowAction;
  requestTimestamp: number;
}

export type FlowPayload = EmailFlowPayload | InboxFlowPayload;

export interface BackgroundCommands {
  'item.printProductConfirmation': PDFCommand;
  'inbox.openMyOfferLink': InboxCommand;
  'email.openUnreadAndClickLink': EmailCommand;
  'buyOffer.execute': BuyOfferCommand;
  'matcher.register': MatcherRegistration;
  'executor.run': ExecutorRequest;
  'tab.manage': TabManagementCommand;
  'state.buying': BuyingStateCommand;
  'extension.log': {
    matcherId: string;
    flowId?: string;
    messages: Array<{ message: string; timestamp: number; level: 'info' | 'warn' | 'error' | 'debug' }>;
    metadata?: Record<string, any>;
    timestamp: number;
  };
  'extension.telemetry': { events: TelemetryEvent[] };
  'extension.getConfig': {};
  'extension.toggleEnabled': {};
  'item.clickProductLink': ItemCommand;
  'myOffer.clickProductLink': MyOfferCommand;
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

export interface EmailCommand {
  visitedUrls?: Record<string, boolean>;
  selectors?: EmailSelectors;
}

export interface EmailSelectors {
  unreadEmail: string;
  emailBody: string;
  markAsReadButton: string;
}

export interface InboxCommand {
  selectors: InboxSelectors;
}

export interface ItemCommand {
  id: string;
  selectors: ItemSelectors;
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

export interface MyOfferCommand {
  selectors: MyOfferSelectors;
}

export interface MyOfferSelectors {
  titleLink: string;
  itemLink: string;
  pdfLink: string;
}

export interface BuyOfferCommand {
  id: string;
  selectors: BuyOfferSelectors;
}

export interface BuyOfferSelectors {
  input: string;
  img: string;
  productTitle: string;
  buyFormButton: string;
}

export interface MatcherRegistration {
  matcher: Matcher;
}

export interface ExecutorRequest {
  executorName: string;
  context: ExecutionContext;
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
  source: 'email' | 'inbox';
  type: FlowAction;
  doneTimestamp?: number;
}

export type FlowState = Record<string, Flow>;

export interface ManagedTabInfo {
  flowId: string;
  createdAt: number;
  lastActive: number;
}

export interface ExtensionStorage {
  enabled: boolean;
  config: ExecutionConfig;
  logs: {
    timestamp: number;
    message: string;
  }[];
  managedTabs: Record<string, ManagedTabInfo>;
  buyingOffers: Record<string, BuyingOffer>;
  productStrategies: StoredProductStrategy[];
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
export type ProductType = 'PEOPLE' | 'ANIMAL' | 'CANCER' | 'ACCIDENT' | 'INVALID';

// Base interface for valid products
interface BaseValidProduct {
  name: string;
  allowed: boolean;
}

// People product interface
export interface PeopleProduct extends BaseValidProduct {
  type: 'PEOPLE';
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
export type Product = PeopleProduct | AnimalProduct | CancerProduct | AccidentProduct | InvalidProduct;

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
export function isPeopleProduct(product: Product): product is PeopleProduct {
  return product.type === 'PEOPLE';
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

  private constructor(hour: number, minute: number) {
    if (!Number.isInteger(hour) || hour < 0 || hour > 23) {
      throw new RangeError('Hour must be 0–23');
    }
    if (!Number.isInteger(minute) || minute < 0 || minute > 59) {
      throw new RangeError('Minute must be 0–59');
    }
    this.hour = hour;
    this.minute = minute;
  }

  static of(hour: number, minute: number): LocalTime {
    return new LocalTime(hour, minute);
  }

  static now(): LocalTime {
    const d = new Date();
    return new LocalTime(d.getHours(), d.getMinutes());
  }

  static parse(str: string): LocalTime {
    const match = /^(\d{2}):(\d{2})$/.exec(str);
    if (!match) throw new Error('Invalid time string: ' + str);
    const [, h, m] = match;
    return new LocalTime(+h, +m);
  }

  toString(): string {
    const pad = (n: number) => String(n).padStart(2, '0');
    return `${pad(this.hour)}:${pad(this.minute)}`;
  }

  toMinutesOfDay(): number {
    return LocalTimeUtils.toMinutesOfDay(this);
  }

  compareTo(other: LocalTime): number {
    return this.toMinutesOfDay() - other.toMinutesOfDay();
  }

  plusMinutes(mins: number): LocalTime {
    const total = (this.toMinutesOfDay() + mins + 24 * 60) % (24 * 60);
    const hour = Math.floor(total / 60);
    const minute = total % 60;
    return new LocalTime(hour, minute);
  }
}
