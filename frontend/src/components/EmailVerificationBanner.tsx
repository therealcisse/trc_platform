import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ExclamationTriangleIcon, XMarkIcon, ClockIcon } from '@heroicons/react/24/outline';
import { useAuth } from '../contexts/AuthContext';
import { authService } from '../services/auth.service';

const COOLDOWN_SECONDS = 60;
const MAX_VERIFICATION_ATTEMPTS = import.meta.env.VITE_MAX_VERIFICATION_ATTEMPTS 
  ? parseInt(import.meta.env.VITE_MAX_VERIFICATION_ATTEMPTS) 
  : 3;

export const EmailVerificationBanner = () => {
  const { user, refreshUser } = useAuth();
  const [showBanner, setShowBanner] = useState(true);
  const [isResending, setIsResending] = useState(false);
  const [resendSuccess, setResendSuccess] = useState(false);
  const [resendError, setResendError] = useState<string | null>(null);
  const [cooldownRemaining, setCooldownRemaining] = useState(0);
  const [attemptsRemaining, setAttemptsRemaining] = useState(MAX_VERIFICATION_ATTEMPTS);

  // Don't show banner if email is verified or user doesn't exist
  if (!user || user.isEmailVerified || !showBanner) {
    return null;
  }

  useEffect(() => {
    // Check for existing cooldown
    const lastRequest = localStorage.getItem('banner_verification_last_request');
    if (lastRequest) {
      const elapsed = Date.now() - parseInt(lastRequest);
      const remaining = Math.max(0, COOLDOWN_SECONDS - Math.floor(elapsed / 1000));
      setCooldownRemaining(remaining);
    }

    // Check attempts
    const attempts = localStorage.getItem('banner_verification_attempts');
    if (attempts) {
      const attemptsData = JSON.parse(attempts);
      if (attemptsData.date === new Date().toDateString()) {
        setAttemptsRemaining(Math.max(0, MAX_VERIFICATION_ATTEMPTS - attemptsData.count));
      } else {
        // New day, reset attempts
        localStorage.removeItem('banner_verification_attempts');
      }
    }
  }, []);

  useEffect(() => {
    if (cooldownRemaining > 0) {
      const timer = setTimeout(() => {
        setCooldownRemaining(cooldownRemaining - 1);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [cooldownRemaining]);

  const handleResendVerification = async () => {
    if (cooldownRemaining > 0 || attemptsRemaining <= 0) {
      return;
    }

    setIsResending(true);
    setResendError(null);
    setResendSuccess(false);

    try {
      await authService.resendVerificationEmail(user.email);
      
      // Update cooldown
      localStorage.setItem('banner_verification_last_request', Date.now().toString());
      setCooldownRemaining(COOLDOWN_SECONDS);
      
      // Update attempts
      const attempts = localStorage.getItem('banner_verification_attempts');
      const today = new Date().toDateString();
      let attemptsData = attempts ? JSON.parse(attempts) : { date: today, count: 0 };
      
      if (attemptsData.date !== today) {
        attemptsData = { date: today, count: 1 };
      } else {
        attemptsData.count++;
      }
      
      localStorage.setItem('banner_verification_attempts', JSON.stringify(attemptsData));
      setAttemptsRemaining(Math.max(0, MAX_VERIFICATION_ATTEMPTS - attemptsData.count));
      
      setResendSuccess(true);
      
      // Clear success message after 5 seconds
      setTimeout(() => {
        setResendSuccess(false);
      }, 5000);
      
      // Check for verification after 10 seconds
      setTimeout(async () => {
        await refreshUser();
      }, 10000);
    } catch (error: any) {
      setResendError(error.response?.data?.detail || 'Failed to resend verification email');
    } finally {
      setIsResending(false);
    }
  };

  return (
    <div className="bg-yellow-50 dark:bg-yellow-900/20 border-b border-yellow-200 dark:border-yellow-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center flex-1">
            <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mr-3 flex-shrink-0" />
            <div className="flex-1">
              <p className="text-sm text-yellow-800 dark:text-yellow-200">
                <span className="font-medium">Email not verified.</span>{' '}
                Please check your inbox to verify your email address.{' '}
                {resendSuccess ? (
                  <span className="text-green-700 dark:text-green-400">
                    Verification email sent! Check your inbox.
                  </span>
                ) : resendError ? (
                  <span className="text-red-700 dark:text-red-400">{resendError}</span>
                ) : cooldownRemaining > 0 ? (
                  <span className="inline-flex items-center">
                    <ClockIcon className="h-4 w-4 mr-1" />
                    Wait {cooldownRemaining}s to resend
                  </span>
                ) : attemptsRemaining <= 0 ? (
                  <span>
                    Maximum attempts reached.{' '}
                    <Link
                      to="/resend-verification"
                      className="underline hover:text-yellow-900 dark:hover:text-yellow-100"
                    >
                      Try again tomorrow
                    </Link>
                  </span>
                ) : (
                  <>
                    <button
                      onClick={handleResendVerification}
                      disabled={isResending}
                      className="underline hover:text-yellow-900 dark:hover:text-yellow-100 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isResending ? 'Sending...' : 'Resend verification email'}
                    </button>
                    {attemptsRemaining < MAX_VERIFICATION_ATTEMPTS && (
                      <span className="ml-2">
                        ({attemptsRemaining} {attemptsRemaining === 1 ? 'attempt' : 'attempts'} left)
                      </span>
                    )}
                  </>
                )}
              </p>
            </div>
          </div>
          <button
            onClick={() => setShowBanner(false)}
            className="ml-3 flex-shrink-0 text-yellow-600 dark:text-yellow-400 hover:text-yellow-700 dark:hover:text-yellow-300"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
};
