import { http } from '../lib/http';
import type { BillingPeriod, UsageSummary, ApiRequest, PaginatedResponse } from '../types/billing';

export const billingService = {
  async getCurrentPeriod(): Promise<BillingPeriod> {
    const { data } = await http.get('/customers/billing/current');
    return data;
  },

  async getBillingPeriods(status?: string): Promise<BillingPeriod[]> {
    const params = status ? { status } : {};
    const { data } = await http.get('/customers/billing/periods', { params });
    return data;
  },

  async getBillingPeriodDetails(periodId: string, page = 1): Promise<PaginatedResponse<ApiRequest>> {
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
  }): Promise<PaginatedResponse<ApiRequest>> {
    const { data } = await http.get('/customers/usage/requests', { 
      params: {
        ...params,
        page_size: params.pageSize // Map to backend parameter name
      } 
    });
    return data;
  },
};
