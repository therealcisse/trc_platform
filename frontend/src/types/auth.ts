export interface User {
  id: string;
  email: string;
  // isActive: boolean;
  // isStaff: boolean;
  isEmailVerified: boolean;
  dateJoined: Date;
  // isSuperuser?: boolean;
  // lastLogin?: Date | null;
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
