/**
 * CSRF Token Management Utilities
 */

/**
 * Get CSRF token from cookie
 * Django sets the CSRF token in a cookie named 'csrftoken'
 */
export function getCSRFToken(): string | null {
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
  return cookieValue;
}

/**
 * Clear all authentication-related cookies
 * Useful for complete logout cleanup
 */
export function clearAuthCookies(): void {
  // Clear CSRF token
  document.cookie = 'csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
  // Clear session ID
  document.cookie = 'sessionid=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
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
  const { default: axios } = await import('axios');
  await axios.get(`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}/auth/csrf/`, {
    withCredentials: true
  });
}
