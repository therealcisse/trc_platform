import { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { DisclaimerModal } from '../../components/DisclaimerModal';
import { useNavigate } from 'react-router-dom';
import { http } from '../../lib/http';

export default function AcceptDisclaimerPage() {
  const [open, setOpen] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { refreshUser } = useAuth();
  const navigate = useNavigate();

  const handleAcknowledge = async () => {
    try {
      await http.post('/customers/accept_disclaimer/');
      await refreshUser();
      navigate('/dashboard');
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Could not acknowledge disclaimer. Please try again.');
      setOpen(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-white dark:bg-gray-900">
      <DisclaimerModal
        open={open}
        onAcknowledge={handleAcknowledge}
        onClose={() => setOpen(true)} /* Prevent closing, must acknowledge */
      />
      {error && <div className="text-red-600 text-center mt-8">{error}</div>}
    </div>
  );
}
