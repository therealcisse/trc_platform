import { http } from '../lib/http';
import type { BillingPeriod, UsageSummary, RequestLog, PaginatedResponse } from '../types/billing';

export const billingService = {
  async getCurrentPeriod(): Promise<BillingPeriod> {
    const { data } = await http.get('/customers/billing/current');
    return data;
  },

  async getBillingPeriods(status?: string): Promise<BillingPeriod[]> {
    const params = status ? { status } : {};
    const { data } = await http.get('/customers/billing/periods', { params });
    return data.results || [];
  },

  async getBillingPeriodDetails(periodId: string, page = 1): Promise<PaginatedResponse<RequestLog>> {
    const { data } = await http.get(`/customers/billing/periods/${periodId}`, {
      params: { page },
    });
    // The API returns { period, requests }, we need to extract the requests part
    return data.requests || { results: [], count: 0, next: null, previous: null };
  },

  async getBillingPeriodWithRequests(periodId: string, page = 1): Promise<{ period: BillingPeriod; requests: PaginatedResponse<RequestLog> }> {
    const { data } = await http.get(`/customers/billing/periods/${periodId}`, {
      params: { page },
    });
    return data;
  },

  async getUsageSummary(): Promise<UsageSummary> {
    const { data } = await http.get('/customers/usage/summary');
    return data;
  },

  async getUsageRequests(params: {
    from?: string;
    to?: string;
    page?: number;
    pageSize?: number;
  }): Promise<PaginatedResponse<RequestLog>> {
    const { data } = await http.get('/customers/usage/requests', { 
      params: {
        ...params,
        page_size: params.pageSize // Map to backend parameter name
      } 
    });
    return data;
  },
};
