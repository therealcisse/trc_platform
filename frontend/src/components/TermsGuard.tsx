import { useAuth } from '../contexts/AuthContext';
import { useLocation, Navigate } from 'react-router-dom';

export function TermsGuard({ children }: { children: React.ReactNode }) {
  const { user, isAuthenticated, isLoading } = useAuth();
  const location = useLocation();
  if (isLoading) return null;
  if (
    isAuthenticated &&
    user &&
    !user.userAcceptedTerms &&
    location.pathname !== '/accept-terms' &&
    location.pathname !== '/logout'
  ) {
    return <Navigate to="/accept-terms" replace />;
  }
  return <>{children}</>;
}
