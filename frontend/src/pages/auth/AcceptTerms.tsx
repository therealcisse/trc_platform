import { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { TermsModal } from '../../components/TermsModal';
import { useNavigate } from 'react-router-dom';
import { http } from '../../lib/http';

export default function AcceptTermsPage() {
  const [open, setOpen] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { refreshUser } = useAuth();
  const navigate = useNavigate();

  const handleAccept = async () => {
    try {
      await http.post('/customers/accept_terms/');
      await refreshUser();
      navigate('/dashboard');
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Could not accept terms. Please try again.');
      setOpen(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-white dark:bg-gray-900">
      <TermsModal
        open={open}
        onAccept={handleAccept}
        onClose={() => setOpen(true)} /* Prevent closing, must accept */
      />
      {error && <div className="text-red-600 text-center mt-8">{error}</div>}
    </div>
  );
}
