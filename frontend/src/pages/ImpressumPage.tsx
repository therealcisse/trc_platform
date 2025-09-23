export const ImpressumPage = () => {
  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="mb-6 sm:mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white">Impressum</h1>
        <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400 mt-2">
          Provider identification in accordance with § 5 TMG (Telemediengesetz).
        </p>
      </div>

      <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-4 sm:p-6 space-y-3 text-sm sm:text-base text-gray-900 dark:text-gray-100">
        <div>
          <h2 className="font-semibold">Service Provider</h2>
          <p>Amadou Cisse</p>
          <p>Marienhof 7</p>
          <p>22399 Hamburg</p>
          <p>Germany</p>
        </div>
        <div>
          <h2 className="font-semibold">Contact</h2>
          <p>
            Email:{' '}
            <a
              className="text-primary-600 dark:text-primary-400 hover:underline"
              href="mailto:amadou.cisse@proton.me"
            >
              amadou.cisse@proton.me
            </a>
          </p>
        </div>
        <div className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">
          <p>
            EU Online Dispute Resolution (ODR) platform:{' '}
            <a
              className="text-primary-600 dark:text-primary-400 hover:underline"
              href="https://ec.europa.eu/consumers/odr/"
              target="_blank"
              rel="noreferrer"
            >
              https://ec.europa.eu/consumers/odr/
            </a>
            .
          </p>
          <p>
            We are neither obliged nor willing to participate in dispute resolution before a
            consumer arbitration board unless required by mandatory law.
          </p>
        </div>
      </div>
    </div>
  );
};
