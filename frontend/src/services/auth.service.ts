import { http } from '../lib/http';
import { queryClient } from '../lib/queryClient';
import { clearAuthCookies, getCSRFToken } from '../lib/csrf';
import type {
  User,
  LoginCredentials,
  RegisterCredentials,
  ChangePasswordData,
} from '../types/auth';

export const authService = {
  async login(credentials: LoginCredentials): Promise<User> {
    const { data } = await http.post('/customers/login', credentials);
    return data;
  },

  async register(credentials: RegisterCredentials): Promise<void> {
    const { password, confirmPassword, inviteCode } = credentials;
    if (password !== confirmPassword) {
      throw new Error('Passwords do not match');
    }

    await http.post('/customers/register', {
      email: credentials.email,
      password: credentials.password,
      inviteCode: inviteCode,
    });
  },

  async logout(): Promise<void> {
    try {
      const csrftoken = getCSRFToken();
      // The Django backend will handle cookie deletion in the response
      await http.post('/customers/logout', null, {
        withCredentials: true,
        headers: { 'X-CSRFToken': csrftoken },
      });
    } catch (error) {
      // Even if the logout request fails, we should still clean up locally
      console.error('Logout request failed:', error);
    } finally {
      // Clear all client-side state
      // This ensures local cleanup happens regardless of server response
      queryClient.clear();

      // Clear auth cookies as a fallback
      // The Django backend already does this, but we ensure cleanup on client
      clearAuthCookies();

      // Force redirect to login page
      // This ensures the user can't stay on protected pages
      window.location.href = '/login';
    }
  },

  async getCurrentUser(): Promise<User> {
    const { data } = await http.get('/customers/me');
    return data;
  },

  async changePassword(data: ChangePasswordData): Promise<void> {
    const { newPassword, confirmPassword } = data;
    if (newPassword !== confirmPassword) {
      throw new Error('New passwords do not match');
    }
    await http.post('/customers/password/change', {
      currentPassword: data.currentPassword,
      newPassword: data.newPassword,
    });
  },

  async verifyEmail(token: string): Promise<void> {
    await http.get(`/customers/verify-email?token=${token}`);
  },

  async resendVerificationEmail(): Promise<void> {
    await http.post('/customers/resend-verification');
  },
};
