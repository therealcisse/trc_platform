import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { EnvelopeIcon, ClockIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

// Get max attempts from environment variable with default of 3
const MAX_VERIFICATION_ATTEMPTS = import.meta.env.VITE_MAX_VERIFICATION_ATTEMPTS
  ? parseInt(import.meta.env.VITE_MAX_VERIFICATION_ATTEMPTS)
  : 3;

const COOLDOWN_SECONDS = 60; // 60 seconds between requests
const STORAGE_KEY_ATTEMPTS = 'email_verification_attempts';
const STORAGE_KEY_LAST_REQUEST = 'email_verification_last_request';

const resendSchema = z.object({
  email: z.string().email('Invalid email address'),
});

type ResendFormData = z.infer<typeof resendSchema>;

interface VerificationAttempts {
  count: number;
  email: string;
  resetAt: number; // Timestamp when attempts reset (24 hours after first attempt)
}

export const ResendVerificationPage = () => {
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState<string>('');
  const [cooldownRemaining, setCooldownRemaining] = useState<number>(0);
  const [attemptsRemaining, setAttemptsRemaining] = useState<number>(MAX_VERIFICATION_ATTEMPTS);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    watch,
  } = useForm<ResendFormData>({
    resolver: zodResolver(resendSchema),
  });

  const watchedEmail = watch('email');

  // Check cooldown on mount and email change
  useEffect(() => {
    checkCooldownAndAttempts(watchedEmail);
  }, [watchedEmail]);

  // Update cooldown timer
  useEffect(() => {
    if (cooldownRemaining > 0) {
      const timer = setTimeout(() => {
        setCooldownRemaining(cooldownRemaining - 1);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [cooldownRemaining]);

  const checkCooldownAndAttempts = (email?: string) => {
    // Check last request time for cooldown
    const lastRequest = localStorage.getItem(STORAGE_KEY_LAST_REQUEST);
    if (lastRequest) {
      const elapsed = Date.now() - parseInt(lastRequest);
      const remainingCooldown = Math.max(0, COOLDOWN_SECONDS - Math.floor(elapsed / 1000));
      setCooldownRemaining(remainingCooldown);
    }

    // Check attempts for the email
    if (email) {
      const attemptsData = localStorage.getItem(STORAGE_KEY_ATTEMPTS);
      if (attemptsData) {
        const attempts: VerificationAttempts = JSON.parse(attemptsData);

        // Reset attempts after 24 hours
        if (Date.now() > attempts.resetAt) {
          localStorage.removeItem(STORAGE_KEY_ATTEMPTS);
          setAttemptsRemaining(MAX_VERIFICATION_ATTEMPTS);
        } else if (attempts.email === email) {
          setAttemptsRemaining(Math.max(0, MAX_VERIFICATION_ATTEMPTS - attempts.count));
        } else {
          // Different email, reset count
          setAttemptsRemaining(MAX_VERIFICATION_ATTEMPTS);
        }
      }
    }
  };

  const updateAttempts = (email: string) => {
    const attemptsData = localStorage.getItem(STORAGE_KEY_ATTEMPTS);
    let attempts: VerificationAttempts;

    if (attemptsData) {
      attempts = JSON.parse(attemptsData);
      if (attempts.email !== email) {
        // Different email, start fresh
        attempts = {
          count: 1,
          email,
          resetAt: Date.now() + 24 * 60 * 60 * 1000, // 24 hours from now
        };
      } else if (Date.now() > attempts.resetAt) {
        // Reset period expired
        attempts = {
          count: 1,
          email,
          resetAt: Date.now() + 24 * 60 * 60 * 1000,
        };
      } else {
        // Increment existing count
        attempts.count++;
      }
    } else {
      // First attempt
      attempts = {
        count: 1,
        email,
        resetAt: Date.now() + 24 * 60 * 60 * 1000,
      };
    }

    localStorage.setItem(STORAGE_KEY_ATTEMPTS, JSON.stringify(attempts));
    setAttemptsRemaining(Math.max(0, MAX_VERIFICATION_ATTEMPTS - attempts.count));
  };

  const onSubmit = async (data: ResendFormData) => {
    if (cooldownRemaining > 0) {
      setStatus('error');
      setMessage(
        `Please wait ${cooldownRemaining} seconds before requesting another verification email.`
      );
      return;
    }

    if (attemptsRemaining <= 0) {
      setStatus('error');
      setMessage(
        `Maximum verification attempts (${MAX_VERIFICATION_ATTEMPTS}) reached. Please try again in 24 hours or contact support.`
      );
      return;
    }

    try {
      setStatus('idle');
      setMessage('');

      // Call the API to resend verification email
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}/customers/resend-verification`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({ email: data.email }),
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to resend verification email');
      }

      // Update attempts and cooldown
      updateAttempts(data.email);
      localStorage.setItem(STORAGE_KEY_LAST_REQUEST, Date.now().toString());
      setCooldownRemaining(COOLDOWN_SECONDS);

      setStatus('success');
      setMessage('Verification email sent! Please check your inbox and spam folder.');
    } catch (error: any) {
      setStatus('error');
      setMessage(error.message || 'Failed to resend verification email. Please try again.');
    }
  };

  const isButtonDisabled = isSubmitting || cooldownRemaining > 0 || attemptsRemaining <= 0;

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <div className="bg-white dark:bg-gray-900 p-8 rounded-2xl shadow-xl w-full max-w-md">
        <div className="text-center mb-8">
          <EnvelopeIcon className="h-16 w-16 text-primary-600 mx-auto mb-4" />
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Resend Verification Email
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Enter your email address to receive a new verification link
          </p>
        </div>

        {attemptsRemaining < MAX_VERIFICATION_ATTEMPTS && attemptsRemaining > 0 && (
          <div className="mb-6 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
            <div className="flex items-start">
              <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mt-0.5 mr-2 flex-shrink-0" />
              <p className="text-sm text-yellow-800 dark:text-yellow-200">
                {attemptsRemaining} verification {attemptsRemaining === 1 ? 'attempt' : 'attempts'}{' '}
                remaining today
              </p>
            </div>
          </div>
        )}

        {cooldownRemaining > 0 && (
          <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <div className="flex items-center">
              <ClockIcon className="h-5 w-5 text-blue-600 dark:text-blue-400 mr-2" />
              <p className="text-sm text-blue-800 dark:text-blue-200">
                Please wait {cooldownRemaining} seconds before requesting another email
              </p>
            </div>
          </div>
        )}

        {status === 'success' && (
          <div className="mb-6 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
            <p className="text-sm text-green-800 dark:text-green-200">{message}</p>
          </div>
        )}

        {status === 'error' && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <p className="text-sm text-red-800 dark:text-red-200">{message}</p>
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
            >
              Email address
            </label>
            <input
              {...register('email')}
              type="email"
              autoComplete="email"
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-800 dark:text-white"
              placeholder="you@example.com"
            />
            {errors.email && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.email.message}</p>
            )}
          </div>

          <button
            type="submit"
            disabled={isButtonDisabled}
            className="w-full py-3 px-4 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting
              ? 'Sending...'
              : cooldownRemaining > 0
                ? `Wait ${cooldownRemaining}s`
                : attemptsRemaining <= 0
                  ? 'Max attempts reached'
                  : 'Send Verification Email'}
          </button>
        </form>

        <div className="mt-6 text-center space-y-2">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Already verified?{' '}
            <Link to="/login" className="font-medium text-primary-600 hover:text-primary-500">
              Sign in
            </Link>
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Need help?{' '}
            <a
              href="mailto:support@example.com"
              className="font-medium text-primary-600 hover:text-primary-500"
            >
              Contact support
            </a>
          </p>
        </div>
      </div>
    </div>
  );
};
