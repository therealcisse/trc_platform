import { useQuery } from '@tanstack/react-query';
import { billingService } from '../services/billing.service';
import { format } from 'date-fns';
import {
  ChartBarIcon,
  ClockIcon,
  CurrencyDollarIcon,
  ServerIcon,
} from '@heroicons/react/24/outline';
import clsx from 'clsx';

const REFRESH_INTERVAL = 5 * 60 * 1000; // 5 minutes as specified in UI.md

export const DashboardPage = () => {
  const { data: currentPeriod, isLoading: periodLoading } = useQuery({
    queryKey: ['billing', 'current'],
    queryFn: billingService.getCurrentPeriod,
    refetchInterval: REFRESH_INTERVAL, // Automatic refetch every 5 minutes
    refetchOnWindowFocus: true, // Refetch when window regains focus
  });

  const { data: usageSummary, isLoading: usageLoading } = useQuery({
    queryKey: ['usage', 'summary'],
    queryFn: billingService.getUsageSummary,
    refetchInterval: REFRESH_INTERVAL, // Automatic refetch every 5 minutes
    refetchOnWindowFocus: true, // Refetch when window regains focus
  });

  const isLoading = periodLoading || usageLoading;

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('en-US').format(num);
  };

  const stats = [
    {
      name: 'Total Requests',
      value: currentPeriod?.totalRequests || 0,
      icon: ServerIcon,
      change: '+12%',
      changeType: 'positive',
    },
    {
      name: 'Current Cost',
      value: currentPeriod?.totalCostCents ? currentPeriod.totalCostCents / 100 : 0,
      icon: CurrencyDollarIcon,
      change: '+5%',
      changeType: 'positive',
      isCurrency: true,
    },
    {
      name: 'Today\'s Usage',
      value: usageSummary?.today || 0,
      icon: ChartBarIcon,
      change: '-2%',
      changeType: 'negative',
    },
    {
      name: 'Last Request',
      value: usageSummary?.lastRequestAt || 'Never',
      icon: ClockIcon,
      isTime: true,
    },
  ];

  const usageStats = [
    { label: 'Today', value: usageSummary?.today || 0 },
    { label: 'Yesterday', value: usageSummary?.yesterday || 0 },
    { label: 'Last 7 days', value: usageSummary?.last7Days || 0 },
    { label: 'This month', value: usageSummary?.thisMonth || 0 },
  ];

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
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Welcome back! Here's an overview of your API usage.
        </p>
      </div>

      {/* Current Billing Period Card */}
      {currentPeriod && (
        <div className="bg-gradient-to-r from-primary-500 to-primary-600 rounded-2xl p-6 mb-8 text-white">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-primary-100 text-sm font-medium">Current Billing Period</p>
              <h2 className="text-2xl font-bold mt-1">{currentPeriod.periodLabel || format(new Date(currentPeriod.periodStart), 'MMMM yyyy')}</h2>
              <p className="text-primary-100 text-sm mt-2">
                {format(new Date(currentPeriod.periodStart), 'MMM d')} -{' '}
                {format(new Date(currentPeriod.periodEnd), 'MMM d, yyyy')}
              </p>
            </div>
            <div className="text-right">
              <p className="text-primary-100 text-sm font-medium">Status</p>
              <span
                className={clsx(
                  'inline-flex items-center px-3 py-1 rounded-full text-sm font-medium mt-1',
                  currentPeriod.paymentStatus === 'paid' && 'bg-green-100 text-green-800',
                  currentPeriod.paymentStatus === 'pending' && 'bg-yellow-100 text-yellow-800',
                  currentPeriod.paymentStatus === 'overdue' && 'bg-red-100 text-red-800'
                )}
              >
                {currentPeriod.paymentStatus.charAt(0).toUpperCase() + currentPeriod.paymentStatus.slice(1)}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat) => (
          <div
            key={stat.name}
            className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 p-6"
          >
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  {stat.name}
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                  {stat.isCurrency
                    ? formatCurrency(stat.value as number)
                    : stat.isTime
                    ? stat.value === 'Never'
                      ? 'Never'
                      : format(new Date(stat.value as string), 'PPp')
                    : formatNumber(stat.value as number)}
                </p>
                {stat.change && (
                  <p
                    className={clsx(
                      'text-sm font-medium mt-2',
                      stat.changeType === 'positive' ? 'text-green-600' : 'text-red-600'
                    )}
                  >
                    {stat.change} from last period
                  </p>
                )}
              </div>
              <div className="flex-shrink-0">
                <div className="p-3 bg-primary-50 dark:bg-primary-900/20 rounded-lg">
                  <stat.icon className="h-6 w-6 text-primary-600 dark:text-primary-400" />
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Usage Summary */}
      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Usage Summary
        </h3>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
          {usageStats.map((stat) => (
            <div key={stat.label}>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                {stat.label}
              </p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {formatNumber(stat.value)}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-500 mt-1">requests</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
