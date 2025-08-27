import { useEffect, useState } from 'react';
import { useSearchParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { CheckCircleIcon, XCircleIcon, ArrowPathIcon } from '@heroicons/react/24/outline';

export const EmailVerificationPage = () => {
  const [searchParams] = useSearchParams();
  const { verifyEmail, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [errorMessage, setErrorMessage] = useState<string>('');

  useEffect(() => {
    const token = searchParams.get('token');

    if (!token) {
      setStatus('error');
      setErrorMessage(
        'No verification token provided. Please check your email for the correct link.'
      );
      return;
    }

    handleVerification(token);
  }, [searchParams]);

  const handleVerification = async (token: string) => {
    try {
      setStatus('loading');
      await verifyEmail(token);
      setStatus('success');

      // Redirect to dashboard after 3 seconds if authenticated
      setTimeout(() => {
        if (isAuthenticated) {
          navigate('/dashboard');
        } else {
          navigate('/login');
        }
      }, 3000);
    } catch (error: any) {
      setStatus('error');
      const message =
        error.response?.data?.detail || 'Verification failed. The link may be expired or invalid.';
      setErrorMessage(message);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <div className="bg-white dark:bg-gray-900 p-8 rounded-2xl shadow-xl w-full max-w-md">
        {status === 'loading' && (
          <div className="text-center">
            <ArrowPathIcon className="h-16 w-16 text-primary-600 animate-spin mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              Verifying your email...
            </h2>
            <p className="text-gray-600 dark:text-gray-400">
              Please wait while we verify your email address.
            </p>
          </div>
        )}

        {status === 'success' && (
          <div className="text-center">
            <CheckCircleIcon className="h-16 w-16 text-green-600 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              Email Verified Successfully!
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Your email has been verified. You can now access all features of your account.
            </p>
            {isAuthenticated ? (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Redirecting to dashboard in a few seconds...
              </p>
            ) : (
              <Link
                to="/login"
                className="inline-block px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg transition-colors"
              >
                Go to Login
              </Link>
            )}
          </div>
        )}

        {status === 'error' && (
          <div className="text-center">
            <XCircleIcon className="h-16 w-16 text-red-600 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              Verification Failed
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">{errorMessage}</p>
            <div className="space-y-3">
              <Link
                to="/resend-verification"
                className="block w-full px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg transition-colors text-center"
              >
                Request New Verification Email
              </Link>
              <Link
                to="/login"
                className="block w-full px-6 py-3 border border-gray-300 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 font-medium rounded-lg transition-colors text-center"
              >
                Back to Login
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
