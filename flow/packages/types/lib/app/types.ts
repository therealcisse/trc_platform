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
  flowId: string;
  config?: ExecutionConfig;
  timeout?: number;
  retryOptions?: RetryOptions;
  dryRun?: boolean;
}

export interface ExecutionConfig {
  // API Authentication
  token?: string;

  operationalHours?: OperationalHours;
  emailMode?: boolean;
  emailRefreshMin?: number;
  emailRefreshMax?: number;

  // Inbox mode configuration
  inboxMode?: boolean;
  inboxRefreshMin?: number;
  inboxRefreshMax?: number;
  products?: ProductConfig[];

  // Animal insurance product strategy
  animals?: boolean;
  animalTimerMin?: number;
  animalTimerMax?: number;
  animalProcessingTimeSeconds?: number;

  // Cancer scan product strategy
  cancer?: boolean;
  cancerTimerMin?: number;
  cancerTimerMax?: number;
  cancerProcessingTimeSeconds?: number;

  // People insurance product strategy
  people?: boolean;
  peopleTimerMin?: number;
  peopleTimerMax?: number;
  peopleProcessingTimeSeconds?: number;
}

export interface OperationalHours {
  [day: string]: {
    enabled: boolean;
    min: number;
    max: number;
  };
}

export interface DelayConfig {
  min: number;
  max: number;
}

export interface RetryOptions {
  maxAttempts: number;
  delayMs: number;
  backoffMultiplier?: number;
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
  delay?: DelayConfig;
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
  delay?: DelayConfig;
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

// Background command definitions
export interface EmailFlowPayload {
  type: 'email';
  id: string;
  title: string;
  href: string;
}

export interface InboxFlowPayload {
  type: 'inbox';
  id: string;
  requestTimestamp: number;
  title: string;
  href: string;
}

export type FlowPayload = EmailFlowPayload | InboxFlowPayload;

export interface BackgroundCommands {
  'email.openUnreadAndClickLink': EmailCommand;
  'buyOffer.execute': BuyOfferCommand;
  'matcher.register': MatcherRegistration;
  'executor.run': ExecutorRequest;
  'tab.manage': TabManagementCommand;
  'state.buying': BuyingStateCommand;
  'extension.log': { text: string };
  'extension.telemetry': { events: TelemetryEvent[] };
  'extension.getConfig': {};
  'item.clickProductLink': ItemCommand;
  'myOffer.clickProductLink': MyOfferCommand;
  'image.solve': { imageData: string };
  'extension.startFlow': FlowPayload;
  'extension.getFlow': { id: string };
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

export interface ItemCommand {
  productStrategies?: ProductStrategy[];
  id: string;
  selectors?: ItemSelectors;
}

export interface ItemSelectors {
  buyButton: string;
  titleLink: string;
}

export interface MyOfferCommand {
  productStrategies?: ProductStrategy[];
  id: string;
  selectors?: MyOfferSelectors;
}

export interface MyOfferSelectors {
  titleLink: string;
  itemLink: string;
  requestTimestampElement: string;
}

export interface BuyOfferCommand {
  id: string;
  delay?: number;
  selectors?: BuyOfferSelectors;
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
  action: 'open' | 'close' | 'reload' | 'manage' | 'unmanage' | 'isManaged';
  tabId?: number;
  url?: string;
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
  domOperations: number;
  networkRequests: number;
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
  delay?: number;
  verify?: boolean;
  scroll?: boolean;
}

// Storage types
export interface Flow {
  id: string;
  timestamp: number;
  requestTimestamp: number;
  status: 'running' | 'done';
  source: 'email' | 'inbox';
  title: string;
  href: string;
}

export type FlowState = Record<string, Flow>;

export interface ExtensionStorage {
  enabled: boolean;
  config: ExecutionConfig;
  logs: {
    timestamp: number;
    message: string;
  }[];
  managedTabs: Record<number, number>;
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
  markManaged(tabId: number): void;
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
export type ProductType = 'PEOPLE' | 'ANIMAL' | 'CANCER' | 'INVALID';

// Base interface for valid products
interface BaseValidProduct {
  name: string;
  allowed: boolean;
  delay: number;
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

// Invalid product interface
export interface InvalidProduct {
  type: 'INVALID';
  name: string;
  allowed: false;
  error: string;
  delay?: never;
}

// Union type of all possible products
export type Product = PeopleProduct | AnimalProduct | CancerProduct | InvalidProduct;

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

export function isInvalidProduct(product: Product): product is InvalidProduct {
  return product.type === 'INVALID';
}
