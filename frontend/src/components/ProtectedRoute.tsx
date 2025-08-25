import { Navigate, Outlet, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { ExclamationCircleIcon } from '@heroicons/react/24/outline';

// Define routes that require email verification
const VERIFICATION_REQUIRED_ROUTES = [
  '/tokens',
  '/usage',
  '/billing',
  '/account/password'
];

export const ProtectedRoute = () => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check if current route requires email verification
  const requiresVerification = VERIFICATION_REQUIRED_ROUTES.some(
    route => location.pathname.startsWith(route)
  );

  if (requiresVerification && user && !user.emailVerified) {
    // Show access restricted message for unverified users
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex items-center justify-center">
        <div className="max-w-md w-full bg-white dark:bg-gray-900 rounded-lg shadow-lg p-8">
          <ExclamationCircleIcon className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-center text-gray-900 dark:text-white mb-4">
            Email Verification Required
          </h2>
          <p className="text-gray-600 dark:text-gray-400 text-center mb-6">
            You need to verify your email address to access this feature.
          </p>
          <div className="space-y-3">
            <Link
              to="/dashboard"
              className="block w-full text-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              Go to Dashboard
            </Link>
            <Link
              to="/resend-verification"
              className="block w-full text-center px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors text-gray-700 dark:text-gray-300"
            >
              Resend Verification Email
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return <Outlet />;
};
