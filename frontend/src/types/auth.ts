export interface User {
  id: string;
  email: string;
  isEmailVerified: boolean;
  userAcceptedTerms: boolean;
  userAcknowledgedDisclaimer: boolean; // NEW: indicates whether the user has acknowledged the Disclaimer
  dateJoined: Date;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterCredentials {
  email: string;
  password: string;
  confirmPassword: string;
  inviteCode: string;
  userAcceptedTerms: boolean;
}

export interface ChangePasswordData {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isEmailVerified: boolean;
}
