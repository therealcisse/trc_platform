import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { billingService } from '../services/billing.service';
import { format } from 'date-fns';
import { Link } from 'react-router-dom';
import {
  CreditCardIcon,
  CheckCircleIcon,
  ClockIcon,
  ExclamationCircleIcon,
  ArrowRightIcon,
} from '@heroicons/react/24/outline';
import clsx from 'clsx';
import { PaymentStatus } from '../types/billing';
import { formatCurrency, formatNumber } from '../utils/currency';

export const BillingPage = () => {
  const [statusFilter, setStatusFilter] = useState<string>('');

  const { data: periods, isLoading } = useQuery({
    queryKey: ['billing', 'periods', statusFilter],
    queryFn: () => billingService.getBillingPeriods(statusFilter || undefined),
  });

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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Billing</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Manage your billing periods and payment history
        </p>
      </div>

      {/* Filter */}
      <div className="mb-6 flex items-center space-x-4">
        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
          Filter by status:
        </label>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-800 dark:text-white"
        >
          <option value="">All</option>
          <option value="paid">Paid</option>
          <option value="pending">Pending</option>
          <option value="overdue">Overdue</option>
        </select>
      </div>

      {/* Billing Periods List */}
      <div className="space-y-4">
        {periods?.length === 0 ? (
          <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-8 text-center">
            <CreditCardIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600 dark:text-gray-400">No billing periods found</p>
          </div>
        ) : (
          periods?.map((period) => (
            <Link
              key={period.id}
              to={`/billing-history/${period.id}`}
              className="block bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6 hover:shadow-lg hover:border-primary-500 dark:hover:border-primary-400 transition-all group"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center mb-2">
                    <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
                      {period.periodLabel || format(new Date(period.periodStart), 'MMMM yyyy')}
                    </h3>
                    <span
                      className={clsx(
                        'ml-3 px-3 py-1 rounded-full text-sm font-medium inline-flex items-center',
                        getStatusColor(period.paymentStatus)
                      )}
                    >
                      {getStatusIcon(period.paymentStatus)}
                      <span className="ml-1">
                        {period.paymentStatus.charAt(0).toUpperCase() +
                          period.paymentStatus.slice(1)}
                      </span>
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-500">Period</p>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        {format(new Date(period.periodStart), 'MMM d')} -{' '}
                        {format(new Date(period.periodEnd), 'MMM d, yyyy')}
                      </p>
                    </div>

                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-500">Total Requests</p>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        {formatNumber(period.totalRequests)}
                      </p>
                    </div>

                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-500">Total Cost</p>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        {formatCurrency(period.totalCostCents)}
                      </p>
                    </div>

                    {period.paidAt && (
                      <div>
                        <p className="text-sm text-gray-500 dark:text-gray-500">Payment Date</p>
                        <p className="text-sm font-medium text-gray-900 dark:text-white">
                          {format(new Date(period.paidAt), 'PPP')}
                        </p>
                      </div>
                    )}
                  </div>

                  {period.paymentReference && (
                    <div className="mt-4">
                      <p className="text-sm text-gray-500 dark:text-gray-500">
                        Payment Reference:{' '}
                        <span className="font-mono text-gray-700 dark:text-gray-300">
                          {period.paymentReference}
                        </span>
                      </p>
                    </div>
                  )}
                </div>

                <div className="flex items-center justify-end mt-4">
                  <span className="text-sm font-medium text-primary-600 dark:text-primary-400 group-hover:text-primary-700 dark:group-hover:text-primary-300 inline-flex items-center">
                    View Details
                    <ArrowRightIcon className="ml-1 h-4 w-4" />
                  </span>
                </div>
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  );
};
