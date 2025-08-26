import axios, { AxiosError } from 'axios';
import { hasCSRFToken, bootstrapCsrf, getCSRFToken } from './csrf';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export const http = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // For session cookies
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken',
});

// Request interceptor
http.interceptors.request.use(
  async (config) => {
    // Check if CSRF token exists, if not bootstrap it
    if (!hasCSRFToken()) {
      await bootstrapCsrf();
    }

    // Add CSRF token to request headers
    const csrfToken = getCSRFToken();
    if (csrfToken) {
      config.headers['X-CSRFToken'] = csrfToken;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for comprehensive error handling
http.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    const status = error.response?.status;
    const errorData = error.response?.data;

    // Create a user-friendly error message
    const getErrorMessage = (): string => {
      if (errorData?.detail) {
        return errorData.detail;
      }

      switch (status) {
        case 400:
          return 'Invalid request. Please check your input.';
        case 401:
          return 'You need to login to continue.';
        case 403:
          return 'You do not have permission to perform this action.';
        case 404:
          return 'The requested resource was not found.';
        case 500:
        case 502:
        case 503:
        case 504:
          return 'A server error occurred. Please try again later.';
        default:
          if (!error.response) {
            return 'Network error. Please check your connection.';
          }
          return 'An unexpected error occurred.';
      }
    };

    // Handle specific status codes
    switch (status) {
      case 401:
        // Unauthorized - redirect to login
        // Store the current location to redirect back after login
        const currentPath = window.location.pathname;
        if (currentPath !== '/login' && currentPath !== '/register') {
          sessionStorage.setItem('redirectAfterLogin', currentPath);
          window.location.href = '/login';
        }
        break;

      case 403:
        // Forbidden - show permission denied
        console.error('Permission denied:', getErrorMessage());
        // You could dispatch a global notification here
        break;

      case 404:
        // Not found
        console.error('Resource not found:', getErrorMessage());
        break;

      case 400:
        // Bad request - validation errors
        console.error('Validation error:', getErrorMessage());
        break;

      case 500:
      case 502:
      case 503:
      case 504:
        // Server errors
        console.error('Server error:', getErrorMessage());
        break;

      default:
        // Network or other errors
        if (!error.response) {
          console.error('Network error:', getErrorMessage());
        }
    }

    // Enhance the error object with a user-friendly message
    const enhancedError = {
      ...error,
      userMessage: getErrorMessage(),
      statusCode: status,
    };

    return Promise.reject(enhancedError);
  }
);

export interface ApiError {
  detail: string;
  code?: string;
}
