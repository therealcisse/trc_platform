import { useState } from 'react';
import privacyEN from '../../PRIVACY.en.md?raw';
import privacyDE from '../../PRIVACY.de.md?raw';

export const PrivacyPage = () => {
  const [lang, setLang] = useState<'en' | 'de'>('en');
  const content = lang === 'en' ? privacyEN : privacyDE;

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="mb-6 sm:mb-8 flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white">
            {lang === 'en' ? 'Privacy Policy' : 'Datenschutzerklärung'}
          </h1>
          <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400 mt-2">
            {lang === 'en'
              ? 'This page provides our GDPR/DSGVO-compliant privacy information.'
              : 'Diese Seite enthält unsere DSGVO-konforme Datenschutzerklärung.'}
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
    </div>
  );
};
