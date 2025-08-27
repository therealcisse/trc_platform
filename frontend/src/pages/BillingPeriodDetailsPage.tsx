import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { billingService } from '../services/billing.service';
import { format } from 'date-fns';
import {
  ArrowLeftIcon,
  CreditCardIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  CheckCircleIcon,
  ClockIcon,
  ExclamationCircleIcon,
} from '@heroicons/react/24/outline';
import clsx from 'clsx';
import { PaymentStatus, RequestStatus } from '../types/billing';
import type { RequestLog } from '../types/billing';
import { formatCurrency, formatNumber, formatBytes } from '../utils/currency';

export const BillingPeriodDetailsPage = () => {
  const { periodId } = useParams<{ periodId: string }>();
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ['billing', 'period', periodId, 'requests', page],
    queryFn: () => billingService.getBillingPeriodWithRequests(periodId!, page),
    enabled: !!periodId,
  });

  const period = data?.period;
  const requests = data?.requests;

  const getStatusIcon = (status: PaymentStatus) => {
    switch (status) {
      case PaymentStatus.PAID:
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case PaymentStatus.PENDING:
        return <ClockIcon className="h-5 w-5 text-yellow-500" />;
      case PaymentStatus.OVERDUE:
        return <ExclamationCircleIcon className="h-5 w-5 text-red-500" />;
      case PaymentStatus.WAIVED:
        return <CheckCircleIcon className="h-5 w-5 text-gray-500" />;
      default:
        return null;
    }
  };

  const getStatusColor = (status: PaymentStatus) => {
    switch (status) {
      case PaymentStatus.PAID:
        return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400';
      case PaymentStatus.PENDING:
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400';
      case PaymentStatus.OVERDUE:
        return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400';
      case PaymentStatus.WAIVED:
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400';
    }
  };

  const getRequestStatusColor = (status: RequestStatus): string => {
    if (status === RequestStatus.SUCCESS) return 'text-green-600 dark:text-green-400';
    if (status === RequestStatus.ERROR) return 'text-red-600 dark:text-red-400';
    return 'text-gray-600 dark:text-gray-400';
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!period) {
    return (
      <div className="p-8">
        <div className="text-center">
          <CreditCardIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            Billing Period Not Found
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            The billing period you're looking for doesn't exist.
          </p>
          <Link
            to="/billing-history"
            className="inline-flex items-center text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-medium"
          >
            <ArrowLeftIcon className="h-4 w-4 mr-2" />
            Back to Billing History
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      {/* Back Link */}
      <Link
        to="/billing-history"
        className="inline-flex items-center text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white mb-6"
      >
        <ArrowLeftIcon className="h-4 w-4 mr-2" />
        Back to Billing History
      </Link>

      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              Billing Period:{' '}
              {period.periodLabel || format(new Date(period.periodStart), 'MMMM yyyy')}
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-2">
              {format(new Date(period.periodStart), 'MMMM d')} -{' '}
              {format(new Date(period.periodEnd), 'MMMM d, yyyy')}
            </p>
          </div>
          <span
            className={clsx(
              'px-4 py-2 rounded-full text-sm font-medium inline-flex items-center',
              getStatusColor(period.paymentStatus)
            )}
          >
            {getStatusIcon(period.paymentStatus)}
            <span className="ml-2">
              {period.paymentStatus.charAt(0).toUpperCase() + period.paymentStatus.slice(1)}
            </span>
          </span>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6">
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
            Total Requests
          </p>
          <p className="text-3xl font-bold text-gray-900 dark:text-white">
            {formatNumber(period.totalRequests)}
          </p>
        </div>

        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6">
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Total Cost</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-white">
            {formatCurrency(period.totalCostCents)}
          </p>
        </div>

        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6">
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
            Average Cost per Request
          </p>
          <p className="text-3xl font-bold text-gray-900 dark:text-white">
            {period.totalRequests > 0
              ? formatCurrency(period.totalCostCents / period.totalRequests)
              : '€0.00'}
          </p>
        </div>
      </div>

      {/* Payment Information */}
      {period.paidAt && (
        <div className="bg-green-50 dark:bg-green-900/10 border border-green-200 dark:border-green-800 rounded-xl p-6 mb-8">
          <div className="flex items-start">
            <CheckCircleIcon className="h-6 w-6 text-green-500 flex-shrink-0 mt-0.5" />
            <div className="ml-3">
              <h3 className="text-lg font-semibold text-green-900 dark:text-green-200">
                Payment Received
              </h3>
              <p className="text-sm text-green-700 dark:text-green-300 mt-1">
                Payment was received on {format(new Date(period.paidAt), 'PPPP')}
              </p>
              {period.paymentReference && (
                <p className="text-sm text-green-700 dark:text-green-300 mt-2">
                  Reference: <span className="font-mono">{period.paymentReference}</span>
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Request History */}
      <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-800">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Request History</h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Showing {requests?.results.length || 0} of {requests?.count || 0} requests
          </p>
        </div>

        {!requests?.results || requests.results.length === 0 ? (
          <div className="p-8 text-center">
            <p className="text-gray-600 dark:text-gray-400">
              No requests found for this billing period
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Timestamp
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Service
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Duration
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Size
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Request ID
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {requests?.results.map((request: RequestLog) => (
                  <tr
                    key={request.requestId}
                    className="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      {format(new Date(request.requestTs), 'MMM d, yyyy HH:mm:ss')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      {request.service}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={clsx(
                          'text-sm font-medium',
                          getRequestStatusColor(request.status)
                        )}
                      >
                        {request.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                      {request.durationMs}ms
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                      <div className="flex flex-col">
                        <span>↑ {formatBytes(request.requestBytes)}</span>
                        <span>↓ {formatBytes(request.responseBytes)}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-500 font-mono text-xs">
                      {request.requestId}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
      {requests && (requests.next || requests.previous) && (
        <div className="flex items-center justify-between mt-6">
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={!requests.previous}
              className={clsx(
                'p-2 rounded-lg border transition-colors',
                requests.previous
                  ? 'border-gray-300 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300'
                  : 'border-gray-200 dark:border-gray-800 text-gray-400 dark:text-gray-600 cursor-not-allowed'
              )}
            >
              <ChevronLeftIcon className="h-5 w-5" />
            </button>

            <span className="px-3 py-1 text-sm text-gray-700 dark:text-gray-300">Page {page}</span>

            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={!requests.next}
              className={clsx(
                'p-2 rounded-lg border transition-colors',
                requests.next
                  ? 'border-gray-300 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300'
                  : 'border-gray-200 dark:border-gray-800 text-gray-400 dark:text-gray-600 cursor-not-allowed'
              )}
            >
              <ChevronRightIcon className="h-5 w-5" />
            </button>
          </div>

          <p className="text-sm text-gray-600 dark:text-gray-400">
            Total: {requests.count} requests
          </p>
        </div>
      )}
    </div>
  );
};
