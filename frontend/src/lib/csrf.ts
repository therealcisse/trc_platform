/**
 * CSRF Token Management Utilities
 */

// Cache the CSRF token for the session to avoid repeated cookie parsing
let cachedCSRFToken: string | null = null;

/**
 * Get CSRF token from cookie
 * Django sets the CSRF token in a cookie named 'csrftoken'
 */
export function getCSRFToken(): string | null {
  // Return cached value if available
  if (cachedCSRFToken) {
    return cachedCSRFToken;
  }

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

  // Cache the token if found
  if (cookieValue) {
    cachedCSRFToken = cookieValue;
  }

  return cookieValue;
}

/**
 * Clear all authentication-related cookies
 * Useful for complete logout cleanup
 *
 * Note: The Django backend already handles cookie deletion on logout,
 * but this function ensures client-side cleanup as a fallback.
 */
export function clearAuthCookies(): void {
  // Clear the cached CSRF token
  cachedCSRFToken = null;

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
 * Check if CSRF token exists (with caching)
 */
export function hasCSRFToken(): boolean {
  // First check cache
  if (cachedCSRFToken) {
    return true;
  }

  // Then check cookie
  const token = getCSRFToken();
  if (token) {
    cachedCSRFToken = token;
    return true;
  }

  return false;
}

/**
 * Bootstrap CSRF token by making a request to the CSRF endpoint
 */
export async function bootstrapCsrf(): Promise<void> {
  try {
    const { default: axios } = await import('axios');
    await axios.get(`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}/auth/csrf/`, {
      withCredentials: true,
    });

    // Clear cache to force re-read from cookie
    cachedCSRFToken = null;

    // Try to read and cache the new token
    const newToken = getCSRFToken();
    if (newToken) {
      console.log('CSRF token successfully bootstrapped');
    } else {
      console.warn('CSRF bootstrap completed but token not found in cookies');
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
