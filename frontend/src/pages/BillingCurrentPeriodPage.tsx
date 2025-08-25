import { useQuery } from '@tanstack/react-query';
import { billingService } from '../services/billing.service';
import { Navigate, Link } from 'react-router-dom';
import { CreditCardIcon } from '@heroicons/react/24/outline';

export const BillingCurrentPeriodPage = () => {
  const {
    data: currentPeriod,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['billing', 'current'],
    queryFn: billingService.getCurrentPeriod,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="max-w-md mx-auto text-center">
          <CreditCardIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            Error Loading Billing Period
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            Unable to load the current billing period. Please try again later.
          </p>
        </div>
      </div>
    );
  }

  // Redirect to the current period's detail page
  if (currentPeriod?.id) {
    return <Navigate to={`/billing-history/${currentPeriod.id}`} replace />;
  }

  // No current billing period found
  return (
    <div className="p-8">
      <div className="max-w-md mx-auto text-center">
        <CreditCardIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
          No Current Billing Period
        </h3>
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          There is no active billing period at the moment.
        </p>
        <Link
          to="/billing-history"
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          View Billing History
        </Link>
      </div>
    </div>
  );
};
