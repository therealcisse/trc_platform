import { Dialog } from '@radix-ui/react-dialog';
import { useRef, useState, useLayoutEffect } from 'react';

import termsEN from '../../TERMS.md?raw';
import termsDE from '../../TERMS.de.md?raw';

export function TermsModal({
  onAccept,
  onClose,
  open,
}: {
  onAccept: () => void;
  onClose: () => void;
  open?: boolean;
}) {
  const termsRef = useRef<HTMLDivElement>(null);
  const [scrolledToBottom, setScrolledToBottom] = useState(false);
  const [lang, setLang] = useState<'en' | 'de'>('en');

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

  // Reset when language changes
  useLayoutEffect(() => {
    setScrolledToBottom(false);
    const el = termsRef.current;
    if (el) el.scrollTop = 0;
  }, [lang]);

  useLayoutEffect(() => {
    const el = termsRef.current;
    if (el && el.scrollHeight <= el.clientHeight + 3) {
      setScrolledToBottom(true);
    }
  }, []);

  return (
    <Dialog
      open={open ?? true}
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
          <div className="p-6 flex items-center justify-between gap-4">
            <h2 id="terms-title" className="text-lg font-bold">
              {lang === 'en' ? 'Terms & Conditions' : 'Allgemeine Geschäftsbedingungen (AGB)'}
            </h2>
            <div className="flex items-center gap-2">
              <button
                className={`px-2 py-1 rounded-md text-xs border ${
                  lang === 'en'
                    ? 'bg-primary-600 text-white border-primary-600'
                    : 'bg-transparent text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-700'
                }`}
                onClick={() => setLang('en')}
                aria-pressed={lang === 'en'}
              >
                English
              </button>
              <button
                className={`px-2 py-1 rounded-md text-xs border ${
                  lang === 'de'
                    ? 'bg-primary-600 text-white border-primary-600'
                    : 'bg-transparent text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-700'
                }`}
                onClick={() => setLang('de')}
                aria-pressed={lang === 'de'}
              >
                Deutsch
              </button>
            </div>
          </div>
          <div
            id="terms-content"
            ref={termsRef}
            tabIndex={0}
            className="flex-1 overflow-y-auto px-6 pb-24"
            onScroll={handleScroll}
            aria-describedby="terms-content-desc"
            style={{ outline: 'none' }}
          >
            <div id="terms-content-desc">
              <pre className="whitespace-pre-wrap break-words text-sm sm:text-base leading-relaxed text-gray-900 dark:text-gray-100">
                {lang === 'en' ? termsEN : termsDE}
              </pre>
            </div>
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
