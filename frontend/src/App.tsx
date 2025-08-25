import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { MainLayout } from './layouts/MainLayout';
import { LoginPage } from './pages/auth/LoginPage';
import { RegisterPage } from './pages/auth/RegisterPage';
import { EmailVerificationPage } from './pages/auth/EmailVerificationPage';
import { ResendVerificationPage } from './pages/auth/ResendVerificationPage';
import { DashboardPage } from './pages/DashboardPage';
import { TokensPage } from './pages/TokensPage';
import { BillingPage } from './pages/BillingPage';
import { BillingPeriodDetailsPage } from './pages/BillingPeriodDetailsPage';
import { UsagePage } from './pages/UsagePage';
import { AccountPage } from './pages/AccountPage';
import { ChangePasswordPage } from './pages/account/ChangePasswordPage';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/verify-email" element={<EmailVerificationPage />} />
          <Route path="/resend-verification" element={<ResendVerificationPage />} />

          {/* Protected routes */}
          <Route element={<ProtectedRoute />}>
            <Route element={<MainLayout />}>
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/tokens" element={<TokensPage />} />
              <Route path="/billing" element={<BillingPage />} />
              <Route path="/billing/:periodId" element={<BillingPeriodDetailsPage />} />
              <Route path="/usage" element={<UsagePage />} />
              <Route path="/account" element={<AccountPage />} />
              <Route path="/account/password" element={<ChangePasswordPage />} />
            </Route>
          </Route>

          {/* Default redirect */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
