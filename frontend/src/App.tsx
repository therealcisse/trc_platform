import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import AcceptTermsPage from './pages/auth/AcceptTerms';
import AcceptDisclaimerPage from './pages/auth/AcceptDisclaimer';
import { TermsGuard } from './components/TermsGuard';
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
import { BillingCurrentPeriodPage } from './pages/BillingCurrentPeriodPage';
import { UsagePage } from './pages/UsagePage';
import { AccountPage } from './pages/AccountPage';
import { ChangePasswordPage } from './pages/account/ChangePasswordPage';
import { TermsPage } from './pages/TermsPage';
import { DisclaimerPage } from './pages/DisclaimerPage';
import { PrivacyPage } from './pages/PrivacyPage';
import { ImpressumPage } from './pages/ImpressumPage';
import { CookiesPage } from './pages/CookiesPage';

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
          <Route path="/accept-terms" element={<AcceptTermsPage />} />
          <Route path="/accept-disclaimer" element={<AcceptDisclaimerPage />} />
          <Route path="/terms" element={<TermsPage />} />
          <Route path="/disclaimer" element={<DisclaimerPage />} />
          <Route path="/privacy" element={<PrivacyPage />} />
          <Route path="/impressum" element={<ImpressumPage />} />
          <Route path="/cookies" element={<CookiesPage />} />

          {/* Protected routes (terms enforced) */}
          <Route
            element={
              <TermsGuard>
                <ProtectedRoute />
              </TermsGuard>
            }
          >
            <Route element={<MainLayout />}>
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/tokens" element={<TokensPage />} />
              <Route path="/billing-history" element={<BillingPage />} />
              <Route path="/billing-current-period" element={<BillingCurrentPeriodPage />} />
              <Route path="/billing-history/:periodId" element={<BillingPeriodDetailsPage />} />
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
