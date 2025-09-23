import { Dialog } from '@radix-ui/react-dialog';
import { useRef, useState, useLayoutEffect } from 'react';

export function TermsModal({ onAccept, onClose }: { onAccept: () => void; onClose: () => void }) {
  const termsRef = useRef<HTMLDivElement>(null);
  const [scrolledToBottom, setScrolledToBottom] = useState(false);

  const handleScroll = () => {
    const el = termsRef.current;
    if (!el) return;
    const epsilon = 3;
    if (el.scrollHeight - el.scrollTop <= el.clientHeight + epsilon) {
      setScrolledToBottom(true);
      console.log('TELEMETRY: Terms Modal Scrolled to End');
    }
  };

  useLayoutEffect(() => {
    setScrolledToBottom(false);
  }, []);

  useLayoutEffect(() => {
    const el = termsRef.current;
    if (el && el.scrollHeight <= el.clientHeight + 3) {
      setScrolledToBottom(true);
    }
  }, []);

  return (
    <Dialog
      open={true}
      onOpenChange={(v) => {
        if (!v) onClose();
      }}
      aria-labelledby="terms-title"
      aria-describedby="terms-content"
    >
      <div className="fixed inset-0 z-50 flex">
        {/* Left and right backdrop */}
        <div className="w-[12.5%] h-full bg-black/30" />
        {/* Modal */}
        <div
          className={`relative w-[75%] h-full flex flex-col bg-white dark:bg-gray-900 shadow-xl outline-none mx-auto transition duration-500 transform
            opacity-100 scale-100`}
        >
          <h2 id="terms-title" className="p-6 text-lg font-bold">
            Terms & Conditions
          </h2>
          <div
            id="terms-content"
            ref={termsRef}
            tabIndex={0}
            className="flex-1 overflow-y-auto px-6 pb-24"
            onScroll={handleScroll}
            aria-describedby="terms-content-desc"
            style={{ outline: 'none' }}
          >
            {/* Replace with real terms content */}
            <div id="terms-content-desc">[Place your terms & conditions content here]</div>
          </div>
          <div className="absolute left-0 right-0 bottom-0 p-6 bg-white dark:bg-gray-900 border-t">
            <button
              type="button"
              className="w-full py-3 px-4 text-white font-medium rounded-lg bg-primary-600 hover:bg-primary-700 transition-colors disabled:opacity-50"
              onClick={() => {
                onAccept();
                console.log('TELEMETRY: Terms Modal Accepted');
              }}
              disabled={!scrolledToBottom}
            >
              Accept terms
            </button>
          </div>
        </div>
        <div className="w-[12.5%] h-full bg-black/30" />
      </div>
    </Dialog>
  );
}
