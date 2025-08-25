export interface BillingPeriod {
  id: string;
  label: string;
  startDate: string;
  endDate: string;
  totalRequests: number;
  totalCost: number;
  status: 'pending' | 'paid' | 'overdue' | 'waived';
  paymentDate?: string;
  paymentReference?: string;
}

export interface UsageSummary {
  today: number;
  yesterday: number;
  last7Days: number;
  thisMonth: number;
  lastRequestAt?: string;
}

export interface ApiRequest {
  id: string;
  timestamp: string;
  service: string;
  status: number;
  duration: number;
  requestSize: number;
  responseSize: number;
  tokenPrefix?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  page: number;
  totalPages: number;
  totalItems: number;
  hasNext: boolean;
  hasPrevious: boolean;
}
