import '@src/Options.css';
import { t } from '@extension/i18n';
import { TabManager } from '@extension/shared';
import { PROJECT_URL_OBJECT, useStorage, withErrorBoundary, withSuspense } from '@extension/shared';
import { extensionConfigStorage, DEFAULT_OPERATIONAL_HOURS_CONFIG } from '@extension/storage';
import { cn, ErrorDisplay, LoadingSpinner, Select, Switch } from '@extension/ui';
import { Fragment, useState } from 'react';
import type { ExecutionConfig, OperationalHours } from '@extension/types';

const HOURS = Array.from({ length: 24 }, (_, i) => i);
const DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'] as const;

const getDayTranslation = (day: DayName) => t(`days_${day.toLowerCase()}`);

type DayName = (typeof DAYS)[number];

const JsonDisplay = ({ data, onClose }: { data: any; onClose: () => void }) => (
  <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
    <div className="max-h-[80vh] max-w-4xl overflow-auto rounded-lg bg-gray-800 p-6">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-100">Flow Database</h3>
        <button
          onClick={onClose}
          className="flex h-8 w-8 items-center justify-center text-xl font-bold text-gray-400 hover:text-gray-200">
          ✕
        </button>
      </div>
      <pre className="overflow-auto whitespace-pre-wrap rounded bg-gray-900 p-4 text-sm text-green-400">
        {JSON.stringify(data, null, 2)}
      </pre>
    </div>
  </div>
);

const Options = () => {
  const { enabled, config } = useStorage(extensionConfigStorage);
  const [showJsonModal, setShowJsonModal] = useState(false);
  const [flowData, setFlowData] = useState(null);

  const handleOperationalHoursChange = (
    day: DayName,
    field: keyof (typeof config.operationalHours)[string],
    value: boolean | number,
  ) => {
    const currentHours = config.operationalHours || {};
    const currentDayConfig = currentHours[day] || DEFAULT_OPERATIONAL_HOURS_CONFIG;

    extensionConfigStorage.updateConfig({
      operationalHours: {
        ...currentHours,
        [day]: {
          ...currentDayConfig,
          [field]: value,
        },
      },
    });
  };

  const handleConfigToggle = (key: keyof ExecutionConfig) => {
    extensionConfigStorage.updateConfig({
      [key]: !config[key],
    });
  };

  const handleRestoreDefaults = async () => {
    if (confirm(t('actions_confirm_restore'))) {
      try {
        await extensionConfigStorage.restoreDefaults();
        alert(t('actions_success_restored'));
      } catch (error) {
        console.error('Failed to restore defaults:', error);
      }
    }
  };

  const handleDeleteFlowDb = async () => {
    if (confirm(t('actions_confirm_delete_db'))) {
      try {
        // Clear storage-based flows and simple logs
        const flows = await extensionConfigStorage.flows.getAllFlowIds();
        await extensionConfigStorage.clearFlowDatabase();

        for (const id of flows) {
          await TabManager.getInstance().closeAllTabs(id);
        }

        // Clear advanced LogManager logs in background
        await chrome.runtime.sendMessage({
          type: 'logs.query',
          payload: {
            action: 'clearAllLogs',
          },
        });

        alert(t('actions_success_deleted'));
      } catch (error) {
        console.error('Failed to delete flow DB:', error);
        alert('Failed to delete flow database. Please try again.');
      }
    }
  };

  const handleShowFlowDb = async () => {
    try {
      const currentData = await extensionConfigStorage.get();
      setFlowData({ flows: currentData.flows });
      setShowJsonModal(true);
    } catch (error) {
      console.error('Failed to get flow data:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 p-6 text-gray-100">
      <div className="mx-auto max-w-2xl space-y-8">
        <header className="text-center">
          <h1 className="mb-1 text-2xl font-semibold">{t('options_title')}</h1>
          <p className="text-sm text-gray-400">{t('options_subtitle')}</p>
        </header>

        {/* Enable Extension Switch */}
        <div className="flex items-center justify-between rounded-lg bg-gray-800 p-4">
          <div>
            <h2 className="font-medium">{t('options_enable_extension')}</h2>
            <p className="text-sm text-gray-400">{t('options_enable_extension_description')}</p>
          </div>
          <Switch
            checked={enabled}
            onCheckedChange={extensionConfigStorage.toggleEnabled}
            className="data-[state=checked]:bg-blue-600 data-[state=unchecked]:bg-gray-200"
          />
        </div>

        {enabled && (
          <div className="space-y-8">
            {/* Authentication */}
            <section>
              <h2 className="mb-4 text-xl font-medium">{t('options_authentication')}</h2>
              <div className="rounded-lg bg-gray-800 p-4">
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-300">{t('options_api_token')}</label>
                  <input
                    type="password"
                    value={config.token || ''}
                    onChange={e => extensionConfigStorage.updateConfig({ token: e.target.value })}
                    className="w-full rounded-md border border-gray-600 bg-gray-700 px-3 py-2 text-gray-100 placeholder-gray-400 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder={t('options_api_token_placeholder')}
                  />
                </div>
              </div>
            </section>

            {/* Message Monitoring */}
            <section>
              <h2 className="mb-4 text-xl font-medium">{t('options_message_monitoring')}</h2>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                {/* Email Mode */}
                <div className="space-y-4 rounded-lg bg-gray-800 p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium">{t('options_email_monitoring')}</h3>
                      <p className="text-sm text-gray-400">{t('options_email_monitoring_description')}</p>
                    </div>
                    <Switch
                      checked={config.emailMode || false}
                      onCheckedChange={() => handleConfigToggle('emailMode')}
                      className="data-[state=checked]:bg-blue-600 data-[state=unchecked]:bg-gray-200"
                    />
                  </div>
                  <div className="space-y-3">
                    <div>
                      <label className="mb-1 block text-sm text-gray-300">{t('options_min_refresh')}</label>
                      <input
                        type="number"
                        value={config.emailRefreshMin || 30}
                        disabled={!config.emailMode}
                        onChange={e => extensionConfigStorage.updateConfig({ emailRefreshMin: Number(e.target.value) })}
                        className="w-full rounded-md border border-gray-600 bg-gray-700 px-3 py-2 text-gray-100 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-sm text-gray-300">{t('options_max_refresh')}</label>
                      <input
                        type="number"
                        value={config.emailRefreshMax || 60}
                        disabled={!config.emailMode}
                        onChange={e => extensionConfigStorage.updateConfig({ emailRefreshMax: Number(e.target.value) })}
                        className="w-full rounded-md border border-gray-600 bg-gray-700 px-3 py-2 text-gray-100 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                </div>

                {/* Inbox Mode */}
                <div className="space-y-4 rounded-lg bg-gray-800 p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium">{t('options_inbox_monitoring')}</h3>
                      <p className="text-sm text-gray-400">{t('options_inbox_monitoring_description')}</p>
                    </div>
                    <Switch
                      checked={config.inboxMode || false}
                      onCheckedChange={() => handleConfigToggle('inboxMode')}
                      className="data-[state=checked]:bg-blue-600 data-[state=unchecked]:bg-gray-200"
                    />
                  </div>

                  {config.inboxMode && (
                    <div className="space-y-3 border-t border-gray-700 pt-3">
                      <div>
                        <label className="mb-1 block text-sm text-gray-300">{t('options_reload_seconds')}</label>
                        <input
                          type="text"
                          value={(config.inboxReloadSeconds || [3, 7]).join(', ')}
                          onChange={e => {
                            const seconds = e.target.value
                              .split(',')
                              .map(s => parseInt(s.trim()))
                              .filter(n => !isNaN(n) && n >= 0 && n < 60);
                            extensionConfigStorage.updateConfig({ inboxReloadSeconds: seconds });
                          }}
                          placeholder="3, 7"
                          className="w-full rounded-md border border-gray-600 bg-gray-700 px-3 py-2 text-gray-100 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <p className="mt-1 text-xs text-gray-400">{t('options_reload_seconds_help')}</p>
                      </div>

                      <div>
                        <label className="mb-1 block text-sm text-gray-300">{t('options_max_links_per_scan')}</label>
                        <input
                          type="number"
                          value={config.inboxMaxLinksPerScan || 10}
                          onChange={e =>
                            extensionConfigStorage.updateConfig({
                              inboxMaxLinksPerScan: parseInt(e.target.value) || 10,
                            })
                          }
                          min="1"
                          max="50"
                          className="w-full rounded-md border border-gray-600 bg-gray-700 px-3 py-2 text-gray-100 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <p className="mt-1 text-xs text-gray-400">{t('options_max_links_per_scan_help')}</p>
                      </div>

                      <div>
                        <label className="mb-1 block text-sm text-gray-300">{t('options_post_reload_delay')}</label>
                        <input
                          type="number"
                          value={config.inboxPostReloadDelayMs || 2000}
                          onChange={e =>
                            extensionConfigStorage.updateConfig({
                              inboxPostReloadDelayMs: parseInt(e.target.value) || 2000,
                            })
                          }
                          min="500"
                          max="10000"
                          step="100"
                          className="w-full rounded-md border border-gray-600 bg-gray-700 px-3 py-2 text-gray-100 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <p className="mt-1 text-xs text-gray-400">{t('options_post_reload_delay_help')}</p>
                      </div>

                      <div>
                        <label className="mb-1 block text-sm text-gray-300">{t('options_inter_open_delay')}</label>
                        <input
                          type="number"
                          value={config.inboxInterOpenDelayMs || 400}
                          onChange={e =>
                            extensionConfigStorage.updateConfig({
                              inboxInterOpenDelayMs: parseInt(e.target.value) || 400,
                            })
                          }
                          min="100"
                          max="2000"
                          step="100"
                          className="w-full rounded-md border border-gray-600 bg-gray-700 px-3 py-2 text-gray-100 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <p className="mt-1 text-xs text-gray-400">{t('options_inter_open_delay_help')}</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </section>

            {/* Operational Hours */}
            <section>
              <h2 className="mb-4 text-xl font-medium">{t('options_operational_hours')}</h2>
              <div className="rounded-lg bg-gray-800 p-6">
                <div className="flex flex-col items-center space-y-4">
                  {DAYS.map(day => {
                    const dayConfig = config.operationalHours?.[day] || DEFAULT_OPERATIONAL_HOURS_CONFIG;
                    return (
                      <div key={day} className="flex w-full items-center justify-center gap-6">
                        <div className="flex w-36 items-center justify-between">
                          <span className="text-gray-300">{getDayTranslation(day)}</span>
                          <Switch
                            checked={dayConfig.enabled}
                            onCheckedChange={checked => handleOperationalHoursChange(day, 'enabled', checked)}
                            className="data-[state=checked]:bg-blue-600 data-[state=unchecked]:bg-gray-200"
                          />
                        </div>
                        <div className="flex items-center gap-3">
                          <Select
                            value={dayConfig.min}
                            onChange={value => handleOperationalHoursChange(day, 'min', Number(value))}
                            disabled={!dayConfig.enabled}
                            options={HOURS.map(hour => ({ value: hour, label: `${hour}:00` }))}
                            className="w-24 border-gray-600 bg-gray-700 text-gray-100"
                          />
                          <span className="text-gray-400">to</span>
                          <Select
                            value={dayConfig.max}
                            onChange={value => handleOperationalHoursChange(day, 'max', Number(value))}
                            disabled={!dayConfig.enabled}
                            options={HOURS.map(hour => ({ value: hour, label: `${hour}:00` }))}
                            className="w-24 border-gray-600 bg-gray-700 text-gray-100"
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </section>

            {/* Product Strategies */}
            <section>
              <h2 className="mb-4 text-xl font-medium">{t('options_product_strategies')}</h2>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                {/* Animals */}
                <div className="space-y-4 rounded-lg bg-gray-800 p-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-medium">{t('options_animal_insurance')}</h3>
                    <Switch
                      checked={config.animals || false}
                      onCheckedChange={() => handleConfigToggle('animals')}
                      className="data-[state=checked]:bg-blue-600 data-[state=unchecked]:bg-gray-200"
                    />
                  </div>
                  <div className="space-y-3">
                    <div>
                      <label className="mb-1 block text-sm text-gray-300">{t('options_processing_time')}</label>
                      <input
                        type="number"
                        min="0"
                        value={config.animalProcessingTimeSeconds || 0}
                        disabled={!config.animals}
                        onChange={e =>
                          extensionConfigStorage.updateConfig({ animalProcessingTimeSeconds: Number(e.target.value) })
                        }
                        className="w-full rounded-md border border-gray-600 bg-gray-700 px-3 py-2 text-gray-100 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                </div>
                {/* People */}
                <div className="space-y-4 rounded-lg bg-gray-800 p-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-medium">{t('options_people_insurance')}</h3>
                    <Switch
                      checked={config.people || false}
                      onCheckedChange={() => handleConfigToggle('people')}
                      className="data-[state=checked]:bg-blue-600 data-[state=unchecked]:bg-gray-200"
                    />
                  </div>
                  <div className="space-y-3">
                    <div>
                      <label className="mb-1 block text-sm text-gray-300">{t('options_processing_time')}</label>
                      <input
                        type="number"
                        min="0"
                        value={config.peopleProcessingTimeSeconds || 0}
                        disabled={!config.people}
                        onChange={e =>
                          extensionConfigStorage.updateConfig({ peopleProcessingTimeSeconds: Number(e.target.value) })
                        }
                        className="w-full rounded-md border border-gray-600 bg-gray-700 px-3 py-2 text-gray-100 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                </div>
                {/* Cancer */}
                <div className="space-y-4 rounded-lg bg-gray-800 p-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-medium">{t('options_cancer_insurance')}</h3>
                    <Switch
                      checked={config.people || false}
                      onCheckedChange={() => handleConfigToggle('cancer')}
                      className="data-[state=checked]:bg-blue-600 data-[state=unchecked]:bg-gray-200"
                    />
                  </div>
                  <div className="space-y-3">
                    <div>
                      <label className="mb-1 block text-sm text-gray-300">{t('options_processing_time')}</label>
                      <input
                        type="number"
                        min="0"
                        value={config.cancerProcessingTimeSeconds || 0}
                        disabled={!config.cancer}
                        onChange={e =>
                          extensionConfigStorage.updateConfig({ cancerProcessingTimeSeconds: Number(e.target.value) })
                        }
                        className="w-full rounded-md border border-gray-600 bg-gray-700 px-3 py-2 text-gray-100 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Actions */}
            <section>
              <h2 className="mb-4 text-xl font-medium">{t('options_actions')}</h2>
              <div className="space-y-4">
                {/* Restore Default Settings */}
                <div className="flex items-center justify-between rounded-lg bg-gray-800 p-4">
                  <div>
                    <h3 className="font-medium">{t('options_restore_defaults')}</h3>
                    <p className="text-sm text-gray-400">{t('options_restore_defaults_description')}</p>
                  </div>
                  <button
                    onClick={handleRestoreDefaults}
                    className="rounded bg-yellow-600 px-4 py-2 text-sm font-medium text-white hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-yellow-500">
                    {t('options_restore_defaults')}
                  </button>
                </div>

                {/* Delete Flow DB */}
                <div className="flex items-center justify-between rounded-lg bg-gray-800 p-4">
                  <div>
                    <h3 className="font-medium">{t('options_delete_flow_db')}</h3>
                    <p className="text-sm text-gray-400">{t('options_delete_flow_db_description')}</p>
                  </div>
                  <button
                    onClick={handleDeleteFlowDb}
                    className="rounded bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500">
                    {t('options_delete_flow_db')}
                  </button>
                </div>

                {/* Show Flow DB */}
                <div className="flex items-center justify-between rounded-lg bg-gray-800 p-4">
                  <div>
                    <h3 className="font-medium">{t('options_show_flow_db')}</h3>
                    <p className="text-sm text-gray-400">{t('options_show_flow_db_description')}</p>
                  </div>
                  <button
                    onClick={handleShowFlowDb}
                    className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500">
                    {t('options_show_flow_db')}
                  </button>
                </div>
              </div>
            </section>
          </div>
        )}
        {showJsonModal && flowData && <JsonDisplay data={flowData} onClose={() => setShowJsonModal(false)} />}
      </div>
    </div>
  );
};

export default withErrorBoundary(withSuspense(Options, <LoadingSpinner />), ErrorDisplay);
