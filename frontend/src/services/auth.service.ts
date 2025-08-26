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
      await http.post('/customers/logout', null, {
        withCredentials: true,
        headers: { 'X-CSRFToken': csrftoken },
      });
    } finally {
      // Clear cookies even if the logout request fails
      // This ensures local cleanup happens regardless
      queryClient.clear();
      clearAuthCookies();
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

  async resendVerificationEmail(email: string): Promise<void> {
    await http.post('/customers/resend-verification', { email });
  },
};
