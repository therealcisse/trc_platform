import { Dialog } from '@radix-ui/react-dialog';
import { useRef, useState, useLayoutEffect } from 'react';
import disclaimerEN from '../../DISCLAIMER.md?raw';
import disclaimerDE from '../../DISCLAIMER.de.md?raw';

export function DisclaimerModal({
  onAcknowledge,
  onClose,
  open,
}: {
  onAcknowledge: () => void;
  onClose: () => void;
  open?: boolean;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [scrolledToBottom, setScrolledToBottom] = useState(false);
  const [lang, setLang] = useState<'en' | 'de'>('en');

  const isAtBottom = (el: HTMLDivElement) => {
    const epsilon = 3;
    // More robust bottom check that tolerates fractional scroll values
    return el.scrollTop + el.clientHeight >= el.scrollHeight - epsilon;
  };

  const handleScroll = () => {
    const el = ref.current;
    if (!el) return;
    if (isAtBottom(el)) {
      setScrolledToBottom(true);
      console.log('TELEMETRY: Disclaimer Modal Scrolled to End');
    }
  };

  // Initial mount: determine if content already fits without scrolling
  useLayoutEffect(() => {
    const el = ref.current;
    if (el) {
      // Reset first
      setScrolledToBottom(isAtBottom(el));
    }
  }, []);

  // When language changes, reset scroll and re-evaluate in next frame
  useLayoutEffect(() => {
    const el = ref.current;
    if (el) {
      el.scrollTop = 0;
      // Re-evaluate after the DOM updates
      requestAnimationFrame(() => {
        if (ref.current) setScrolledToBottom(isAtBottom(ref.current));
      });
    } else {
      setScrolledToBottom(false);
    }
  }, [lang]);

  // When modal open state changes (if controlled), re-evaluate
  useLayoutEffect(() => {
    const el = ref.current;
    if (el) {
      requestAnimationFrame(() => {
        if (ref.current) setScrolledToBottom(isAtBottom(ref.current));
      });
    }
  }, [open]);

  return (
    <Dialog
      open={open ?? true}
      onOpenChange={(v) => {
        if (!v) onClose();
      }}
      aria-labelledby="disclaimer-title"
      aria-describedby="disclaimer-content"
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
            <h2 id="disclaimer-title" className="text-lg font-bold">
              {lang === 'en' ? 'Disclaimer' : 'Haftungsausschluss'}
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
            id="disclaimer-content"
            ref={ref}
            tabIndex={0}
            className="flex-1 overflow-y-auto px-6 pb-24"
            onScroll={handleScroll}
            aria-describedby="disclaimer-content-desc"
            style={{ outline: 'none' }}
          >
            <div id="disclaimer-content-desc">
              <pre className="whitespace-pre-wrap break-words text-sm sm:text-base leading-relaxed text-gray-900 dark:text-gray-100">
                {lang === 'en' ? disclaimerEN : disclaimerDE}
              </pre>
            </div>
          </div>
          <div className="absolute left-0 right-0 bottom-0 p-6 bg-white dark:bg-gray-900 border-t">
            <button
              type="button"
              className="w-full py-3 px-4 text-white font-medium rounded-lg bg-primary-600 hover:bg-primary-700 transition-colors disabled:opacity-50"
              onClick={() => {
                onAcknowledge();
                console.log('TELEMETRY: Disclaimer Modal Acknowledged');
              }}
              disabled={!scrolledToBottom}
            >
              {lang === 'en' ? 'Acknowledge' : 'Zur Kenntnis nehmen'}
            </button>
          </div>
        </div>
        <div className="w-[12.5%] h-full bg-black/30" />
      </div>
    </Dialog>
  );
}
