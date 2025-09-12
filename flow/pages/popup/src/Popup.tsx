import '@src/Popup.css';
import { useState, useEffect } from 'react';
import { withErrorBoundary, withSuspense, ConfigService } from '@extension/shared';
import { cn, ErrorDisplay, LoadingSpinner } from '@extension/ui';

const PowerIcon = ({ className }: { className?: string }) => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className={className}>
    <path
      fillRule="evenodd"
      d="M12 2.25a.75.75 0 01.75.75v9a.75.75 0 01-1.5 0V3a.75.75 0 01.75-.75zM6.166 5.106a.75.75 0 010 1.06 8.25 8.25 0 1011.668 0 .75.75 0 111.06-1.06c3.808 3.807 3.808 9.98 0 13.788-3.807 3.808-9.98 3.808-13.788 0-3.808-3.807-3.808-9.98 0-13.788a.75.75 0 011.06 0z"
      clipRule="evenodd"
    />
  </svg>
);

const Popup = () => {
  const [enabled, setEnabled] = useState(true);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadState = async () => {
      try {
        const isEnabled = await ConfigService.isEnabled();
        setEnabled(isEnabled);
      } catch (error) {
        console.error('Error loading extension state:', error);
      } finally {
        setLoading(false);
      }
    };

    loadState();
  }, []);

  const toggleEnabled = async () => {
    try {
      await ConfigService.setEnabled(!enabled);
      setEnabled(!enabled);
    } catch (error) {
      console.error('Error toggling extension state:', error);
    }
  };

  if (loading) {
    return (
      <div className="App flex items-center justify-center bg-white">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="App bg-white">
      <div className="App-content">
        {/* <h1 className="Title text-gray-900">TRC Platform Extension</h1> */}

        <button
          onClick={toggleEnabled}
          className={cn('PowerButton', enabled ? 'bg-green-500 text-white' : 'bg-red-500 text-white')}
          title={enabled ? 'Click to disable' : 'Click to enable'}>
          <PowerIcon />
        </button>
      </div>
    </div>
  );
};

export default withErrorBoundary(withSuspense(Popup, <LoadingSpinner />), ErrorDisplay);
