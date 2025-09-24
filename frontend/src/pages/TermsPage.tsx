import { Link } from 'react-router-dom';
import { useState } from 'react';
import termsEN from '../../TERMS.md?raw';
import termsDE from '../../TERMS.de.md?raw';

export const TermsPage = () => {
  const [lang, setLang] = useState<'en' | 'de'>('en');
  const content = lang === 'en' ? termsEN : termsDE;

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="mb-6 sm:mb-8 flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white">
            {lang === 'en' ? 'Terms & Conditions' : 'Allgemeine Geschäftsbedingungen (AGB)'}
          </h1>
          <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400 mt-2">
            {lang === 'en'
              ? 'This page shows the current Terms governing the web app and API.'
              : 'Diese Seite zeigt die aktuellen AGB für die Web‑Anwendung und die API.'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            className={`px-3 py-1 rounded-md text-sm border ${
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
            className={`px-3 py-1 rounded-md text-sm border ${
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

      <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-4 sm:p-6">
        <pre className="whitespace-pre-wrap break-words text-sm sm:text-base leading-relaxed text-gray-900 dark:text-gray-100">
          {content}
        </pre>
      </div>

      <div className="mt-6">
        <Link
          to="/account"
          className="text-sm text-primary-600 dark:text-primary-400 hover:underline"
        >
          {lang === 'en' ? 'Back' : 'Zurück'}
        </Link>
      </div>
    </div>
  );
};
