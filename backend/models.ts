/**
 * TypeScript definitions for Django models
 * Generated from Django backend models
 * TypeScript version: 5.7.x (latest as of 2025)
 */

// ==================== Core Models ====================

/**
 * Singleton settings model for the application
 */
export interface Settings {
  costPerRequestCents: number;
}

// ==================== Customer Models ====================

/**
 * User model with authentication and permissions
 */
export interface User {
  id: string; // UUID
  email: string;
  isActive: boolean;
  isStaff: boolean;
  emailVerifiedAt: Date | null;
  dateJoined: Date;
  isSuperuser?: boolean;
  lastLogin?: Date | null;
  
  // Computed properties
  isEmailVerified?: boolean;
  
  // Relations
  apiTokens?: ApiToken[];
  inviteCodeUsed?: InviteCode;
  billingPeriods?: BillingPeriod[];
  requestLogs?: RequestLog[];
}

/**
 ye* API token for programmatic access
 */
export interface ApiToken {
  id: string; // UUID
  userId: string; // UUID foreign key
  user?: User;
  name: string;
  tokenPrefix: string;
  tokenHash: string;
  createdAt: Date;
  revokedAt: Date | null;
  lastUsedAt: Date | null;
  
  // Computed properties
  isRevoked?: boolean;
  
  // Relations
  requestLogs?: RequestLog[];
}

// ==================== Usage Models ====================

/**
 * Payment status enum for billing periods
 */
export enum PaymentStatus {
  PENDING = 'pending',
  PAID = 'paid',
  OVERDUE = 'overdue',
  WAIVED = 'waived',
}

/**
 * Represents a monthly billing period
 */
export interface BillingPeriod {
  id: string; // UUID
  userId: string; // UUID foreign key
  user?: User;
  periodStart: Date;
  periodEnd: Date;
  totalRequests: number;
  totalCostCents: number;
  isCurrent: boolean;
  
  // Payment tracking fields
  paymentStatus: PaymentStatus;
  paidAt: Date | null;
  paidAmountCents: number | null;
  paymentReference: string | null;
  paymentNotes: string | null;
  
  createdAt: Date;
  updatedAt: Date;
  
  // Computed properties
  periodLabel?: string;
  canBeMarkedPaid?: boolean;
  
  // Relations
  requests?: RequestLog[];
}

/**
 * Request status enum
 */
export enum RequestStatus {
  SUCCESS = 'success',
  ERROR = 'error',
}

/**
 * Log of API requests for usage tracking
 */
export interface RequestLog {
  id: string; // UUID
  userId: string; // UUID foreign key
  user?: User;
  tokenId: string | null; // UUID foreign key
  token?: ApiToken | null;
  service: string;
  requestTs: Date;
  durationMs: number;
  requestBytes: number;
  responseBytes: number;
  status: RequestStatus;
  errorCode: string | null;
  requestId: string; // UUID
  billingPeriodId: string | null; // UUID foreign key
  billingPeriod?: BillingPeriod | null;
  result: string | null;
  
  // Relations
  savedImage?: RequestImage;
}

/**
 * Stores image data for requests when SAVE_REQUEST_IMAGES is enabled
 */
export interface RequestImage {
  id: string; // UUID
  requestLogId: string; // UUID foreign key (OneToOne)
  requestLog?: RequestLog;
  imageData: ArrayBuffer | Uint8Array; // Binary data
  mimeType: string;
  fileSize: number;
  imageHash: string; // SHA256
  width: number | null;
  height: number | null;
  createdAt: Date;
}

// ==================== Type Guards ====================

/**
 * Type guard to check if a user is verified
 */
export function isVerifiedUser(user: User): boolean {
  return user.emailVerifiedAt !== null;
}

/**
 * Type guard to check if an API token is valid
 */
export function isValidApiToken(token: ApiToken): boolean {
  return token.revokedAt === null;
}



// ==================== Utility Types ====================


/**
 * Create API token input type
 */
export interface CreateApiTokenInput {
  userId: string;
  name: string;
}

/**
 * Settings update input (partial update)
 */
export interface UpdateSettingsInput {
  costPerRequestCents?: number;
  openaiModel?: string;
  openaiTimeoutS?: number;
}

// ==================== Response Types ====================

/**
 * Paginated response wrapper
 */
export interface PaginatedResponse<T> {
  results: T[];
  count: number;
  next: string | null;
  previous: string | null;
}

/**
 * API error response
 */
export interface ApiErrorResponse {
  error: string;
  code?: string;
  details?: Record<string, unknown>;
}

/**
 * Token generation response
 */
export interface TokenGenerationResponse {
  token: string;
  tokenPrefix: string;
  apiToken: ApiToken;
}

// ==================== Query Filter Types ====================

/**
 * User query filters
 */
export interface UserFilters {
  email?: string;
  isActive?: boolean;
  isStaff?: boolean;
  isEmailVerified?: boolean;
  dateJoinedAfter?: Date;
  dateJoinedBefore?: Date;
}

/**
 * Billing period query filters
 */
export interface BillingPeriodFilters {
  userId?: string;
  paymentStatus?: PaymentStatus;
  isCurrent?: boolean;
  periodStartAfter?: Date;
  periodStartBefore?: Date;
}

/**
 * Request log query filters
 */
export interface RequestLogFilters {
  userId?: string;
  tokenId?: string;
  service?: string;
  status?: RequestStatus;
  requestTsAfter?: Date;
  requestTsBefore?: Date;
  billingPeriodId?: string;
}

// ==================== Aggregate Types ====================

/**
 * Usage statistics
 */
export interface UsageStatistics {
  totalRequests: number;
  totalCostCents: number;
  averageRequestDurationMs: number;
  totalRequestBytes: number;
  totalResponseBytes: number;
  successRate: number;
  periodStart: Date;
  periodEnd: Date;
}

/**
 * User summary with usage
 */
export interface UserSummary extends User {
  currentPeriodUsage: UsageStatistics;
  lifetimeUsage: UsageStatistics;
  activeTokensCount: number;
  outstandingBalanceCents: number;
}

// ==================== Constants ====================

/**
 * Default settings values
 */
export const DEFAULT_SETTINGS: Readonly<Settings> = {
  costPerRequestCents: 100,
  openaiModel: 'gpt-vision',
  openaiTimeoutS: 30,
  updatedAt: new Date(),
} as const;

/**
 * Service types enum
 */
export enum ServiceType {
  IMAGE_SOLVE = 'core.image_solve',
  // Add more service types as needed
}

/**
 * Token prefix constant
 */
export const API_TOKEN_PREFIX = 'tok_' as const;

/**
 * Invite code length
 */
export const INVITE_CODE_LENGTH = 8 as const;

// ==================== Helper Functions ====================

/**
 * Format billing period label
 */
export function formatBillingPeriodLabel(period: BillingPeriod): string {
  const date = new Date(period.periodStart);
  const options: Intl.DateTimeFormatOptions = { 
    year: 'numeric', 
    month: 'long' 
  };
  return date.toLocaleDateString('en-US', options);
}

/**
 * Calculate cost in dollars from cents
 */
export function centsToDollars(cents: number): number {
  return cents / 100;
}

/**
 * Format UUID for display (shortened version)
 */
export function formatUuidShort(uuid: string): string {
  return uuid.split('-')[0];
}

/**
 * Check if billing period is overdue
 */
export function isBillingPeriodOverdue(period: BillingPeriod): boolean {
  if (period.isCurrent || period.paymentStatus === PaymentStatus.PAID) {
    return false;
  }
  
  const gracePeriodDays = 30;
  const overdueDate = new Date(period.periodEnd);
  overdueDate.setDate(overdueDate.getDate() + gracePeriodDays);
  
  return new Date() > overdueDate && period.paymentStatus !== PaymentStatus.WAIVED;
}

// ==================== Export all types ====================

export type {
  Settings,
  User,
  InviteCode,
  ApiToken,
  BillingPeriod,
  RequestLog,
  RequestImage,
  CreateUserInput,
  CreateApiTokenInput,
  MarkBillingPeriodAsPaidInput,
  CreateRequestLogInput,
  UpdateSettingsInput,
  PaginatedResponse,
  ApiErrorResponse,
  TokenGenerationResponse,
  UserFilters,
  BillingPeriodFilters,
  RequestLogFilters,
  UsageStatistics,
  UserSummary,
};
