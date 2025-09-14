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
  productId?: string;
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
  timerMode?: boolean;
  randomDelay?: DelayConfig;
  products?: ProductConfig[];

  // Animal insurance product strategy
  animals?: boolean;
  animalTimerMin?: number;
  animalTimerMax?: number;

  // Cancer scan product strategy
  cancer?: boolean;
  cancerTimerMin?: number;
  cancerTimerMax?: number;

  // People insurance product strategy
  people?: boolean;
  peopleTimerMin?: number;
  peopleTimerMax?: number;
}

export interface OperationalHours {
  [day: number]: {
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

export interface Product {
  valid: boolean;
  text: string;
  name?: string;
  insuredType?: string;
  insuredAge?: number;
  meta?: Record<string, any>;
  isAllowed(config: ExecutionConfig): { allowed: boolean; delay?: number };
  toString(): string;
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
export interface BackgroundCommands {
  'email.openUnreadAndClickLink': EmailCommand;
  'offers.clickProductLink': OffersCommand;
  'buyOffer.execute': BuyOfferCommand;
  'matcher.register': MatcherRegistration;
  'executor.run': ExecutorRequest;
  'tab.manage': TabManagementCommand;
  'state.buying': BuyingStateCommand;
  'extension.log': { text: string };
  'extension.telemetry': { events: TelemetryEvent[] };
  'extension.getConfig': {};
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

export interface OffersCommand {
  productStrategies?: ProductStrategy[];
  selectors?: OffersSelectors;
}

export interface OffersSelectors {
  offerMarkers: string;
  offerPopup: string;
  browseList: string;
  buyButton: string;
  titleLink: string;
}

export interface BuyOfferCommand {
  productId?: string;
  delay?: number;
  selectors?: BuyOfferSelectors;
}

export interface BuyOfferSelectors {
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
  key: string;
  id?: string;
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
export interface ExtensionStorage {
  enabled: boolean;
  config: ExecutionConfig;
  logs: string[];
  managedTabs: Record<number, number>;
  buyingOffers: Record<string, BuyingOffer>;
  productStrategies: ProductStrategy[];
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
