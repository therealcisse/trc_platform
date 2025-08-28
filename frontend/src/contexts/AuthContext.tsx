import React, { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import {
  type User,
  type LoginCredentials,
  type RegisterCredentials,
  type ChangePasswordData,
} from '../types/auth';
import { authService } from '../services/auth.service';
import { setCSRFToken } from '../lib/csrf';
import { useNavigate } from 'react-router-dom';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (credentials: RegisterCredentials) => Promise<void>;
  logout: () => Promise<void>;
  changePassword: (data: ChangePasswordData) => Promise<void>;
  verifyEmail: (token: string) => Promise<void>;
  resendVerificationEmail: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const response = await authService.getCurrentUser();
      // Handle CSRF token if present in response
      if ((response as any).csrfToken) {
        setCSRFToken((response as any).csrfToken);
        const { csrfToken, ...userData } = response as any;
        setUser(userData);
      } else {
        setUser(response);
      }
    } catch (error) {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (credentials: LoginCredentials) => {
    await authService.login(credentials);
    // Refresh user data to ensure we have the latest information
    await refreshUser();
    navigate('/dashboard');
  };

  const register = async (credentials: RegisterCredentials) => {
    await authService.register(credentials);
    navigate('/login', {
      state: {
        message: 'Registration successful! Please check your email to verify your account.',
      },
    });
  };

  const logout = async () => {
    try {
      await authService.logout();
    } catch (error) {
      // Log error but continue with local cleanup
      console.error('Logout request failed:', error);
    } finally {
      // Always clear local state regardless of API call result
      setUser(null);
      // Clear any stored redirect path
      sessionStorage.removeItem('redirectAfterLogin');
      // Clear any other session/local storage items if needed
      localStorage.removeItem('userPreferences');
      // Navigate to login page
      navigate('/login');
    }
  };

  const changePassword = async (data: ChangePasswordData) => {
    await authService.changePassword(data);
  };

  const verifyEmail = async (token: string) => {
    await authService.verifyEmail(token);
    await refreshUser();
  };

  const resendVerificationEmail = async () => {
    await authService.resendVerificationEmail();
  };

  const refreshUser = async () => {
    const response = await authService.getCurrentUser();
    // Handle CSRF token if present in response
    if ((response as any).csrfToken) {
      setCSRFToken((response as any).csrfToken);
      const { csrfToken, ...userData } = response as any;
      setUser(userData);
    } else {
      setUser(response);
    }
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
    changePassword,
    verifyEmail,
    resendVerificationEmail,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
