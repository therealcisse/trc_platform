/**
 * CSRF Token Management Utilities
 */

// Cache the CSRF token for the session
let cachedCSRFToken: string | null = null;

// Storage key for persisting CSRF token across page reloads
const CSRF_STORAGE_KEY = 'csrfToken';

/**
 * Set CSRF token from backend response
 * This is used when the backend sends the token in the response body
 */
export function setCSRFToken(token: string): void {
  cachedCSRFToken = token;
  // Also store in sessionStorage for persistence across page reloads
  try {
    sessionStorage.setItem(CSRF_STORAGE_KEY, token);
  } catch (e) {
    console.warn('Failed to store CSRF token in sessionStorage:', e);
  }
}

/**
 * Get CSRF token
 * First checks memory cache, then sessionStorage, then cookies as fallback
 */
export function getCSRFToken(): string | null {
  // Return cached value if available
  if (cachedCSRFToken) {
    return cachedCSRFToken;
  }

  // Try to get from sessionStorage
  try {
    const storedToken = sessionStorage.getItem(CSRF_STORAGE_KEY);
    if (storedToken) {
      cachedCSRFToken = storedToken;
      return storedToken;
    }
  } catch (e) {
    console.warn('Failed to read CSRF token from sessionStorage:', e);
  }

  // Fallback to cookie (for same-origin deployments or development)
  const name = 'csrftoken';
  let cookieValue = null;

  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      // Check if this cookie string begins with the name we want
      if (cookie.substring(0, name.length + 1) === name + '=') {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }

  // Cache the token if found in cookies
  if (cookieValue) {
    cachedCSRFToken = cookieValue;
    // Store in sessionStorage for consistency
    try {
      sessionStorage.setItem(CSRF_STORAGE_KEY, cookieValue);
    } catch (e) {
      // Ignore storage errors
    }
  }

  return cookieValue;
}

/**
 * Clear all authentication-related cookies and tokens
 * Useful for complete logout cleanup
 *
 * Note: The Django backend already handles cookie deletion on logout,
 * but this function ensures client-side cleanup as a fallback.
 */
export function clearAuthCookies(): void {
  // Clear the cached CSRF token
  cachedCSRFToken = null;

  // Clear from sessionStorage
  try {
    sessionStorage.removeItem(CSRF_STORAGE_KEY);
  } catch (e) {
    // Ignore storage errors
  }

  // Get current domain and protocol
  const isSecure = window.location.protocol === 'https:';
  const domain = window.location.hostname;

  // Base cookie clear string
  const expiry = 'expires=Thu, 01 Jan 1970 00:00:00 UTC';

  // Clear cookies with various attribute combinations to ensure removal
  // This accounts for different ways the cookies might have been set
  const cookiesToClear = ['csrftoken', 'sessionid'];

  cookiesToClear.forEach((cookieName) => {
    // Clear with just path
    document.cookie = `${cookieName}=; ${expiry}; path=/;`;

    // Clear with domain and path
    document.cookie = `${cookieName}=; ${expiry}; path=/; domain=${domain};`;

    // Clear with .domain (for parent domain cookies)
    document.cookie = `${cookieName}=; ${expiry}; path=/; domain=.${domain};`;

    // Clear with SameSite=None (must include Secure on HTTPS)
    if (isSecure) {
      document.cookie = `${cookieName}=; ${expiry}; path=/; SameSite=None; Secure;`;
      document.cookie = `${cookieName}=; ${expiry}; path=/; domain=${domain}; SameSite=None; Secure;`;
      document.cookie = `${cookieName}=; ${expiry}; path=/; domain=.${domain}; SameSite=None; Secure;`;
    } else {
      // For HTTP, try with SameSite=None (though this might not work in all browsers)
      document.cookie = `${cookieName}=; ${expiry}; path=/; SameSite=None;`;
      document.cookie = `${cookieName}=; ${expiry}; path=/; domain=${domain}; SameSite=None;`;
    }

    // Also try Lax and Strict variants
    document.cookie = `${cookieName}=; ${expiry}; path=/; SameSite=Lax;`;
    document.cookie = `${cookieName}=; ${expiry}; path=/; SameSite=Strict;`;
  });

  // Clear any auth-related localStorage/sessionStorage items
  // Add any keys your app uses for auth state
  const authStorageKeys = ['authToken', 'user', 'redirectAfterLogin'];
  authStorageKeys.forEach((key) => {
    localStorage.removeItem(key);
    sessionStorage.removeItem(key);
  });
}

/**
 * Check if CSRF token exists
 */
export function hasCSRFToken(): boolean {
  return getCSRFToken() !== null;
}

/**
 * Bootstrap CSRF token by making a request to the CSRF endpoint
 */
export async function bootstrapCsrf(): Promise<void> {
  try {
    const { default: axios } = await import('axios');
    const response = await axios.get(
      `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}/auth/csrf/`,
      {
        withCredentials: true,
      }
    );

    // Get token from response body
    const token = response.data?.csrfToken;
    if (token) {
      setCSRFToken(token);
      console.log('CSRF token successfully bootstrapped from response');
    } else {
      // Fallback: try to read from cookie
      cachedCSRFToken = null;
      const cookieToken = getCSRFToken();
      if (cookieToken) {
        console.log('CSRF token found in cookies');
      } else {
        console.warn('CSRF bootstrap completed but token not found');
      }
    }
  } catch (error) {
    console.error('Failed to bootstrap CSRF token:', error);
    throw error;
  }
}

/**
 * Debug function to inspect current cookies
 * Useful for troubleshooting cookie issues
 */
export function debugCookies(): Record<string, string> {
  const cookies: Record<string, string> = {};

  if (document.cookie && document.cookie !== '') {
    const cookieArray = document.cookie.split(';');
    cookieArray.forEach((cookie) => {
      const [name, value] = cookie.trim().split('=');
      if (name) {
        cookies[name] = value || '';
      }
    });
  }

  console.log('Current cookies:', cookies);
  console.log('Has csrftoken:', 'csrftoken' in cookies);
  console.log('Has sessionid:', 'sessionid' in cookies);

  return cookies;
}
