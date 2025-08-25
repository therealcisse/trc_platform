export const PaymentStatus = {
  PENDING: 'pending',
  PAID: 'paid',
  OVERDUE: 'overdue',
  WAIVED: 'waived',
} as const;

export type PaymentStatus = typeof PaymentStatus[keyof typeof PaymentStatus];

export interface BillingPeriod {
  id: string;
  userId: string;
  periodStart: Date;
  periodEnd: Date;
  totalRequests: number;
  totalCostCents: number;
  isCurrent: boolean;
  paymentStatus: PaymentStatus;
  paidAt: Date | null;
  paidAmountCents: number | null;
  paymentReference: string | null;
  paymentNotes: string | null;
  createdAt: Date;
  updatedAt: Date;
  periodLabel?: string; // Computed property
  canBeMarkedPaid?: boolean; // Computed property
}

export interface UsageSummary {
  today: number;
  yesterday: number;
  last7Days: number;
  thisMonth: number;
  lastRequestAt?: string;
}

export const RequestStatus = {
  SUCCESS: 'success',
  ERROR: 'error',
} as const;

export type RequestStatus = typeof RequestStatus[keyof typeof RequestStatus];

export interface RequestLog {
  id: string;
  userId: string;
  tokenId: string | null;
  service: string;
  requestTs: Date;
  durationMs: number;
  requestBytes: number;
  responseBytes: number;
  status: RequestStatus;
  errorCode: string | null;
  requestId: string;
  billingPeriodId: string | null;
  result: string | null;
}

export interface PaginatedResponse<T> {
  results: T[];
  count: number;
  next: string | null;
  previous: string | null;
}
