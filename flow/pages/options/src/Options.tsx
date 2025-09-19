import '@src/Options.css';
import { t } from '@extension/i18n';
import { PROJECT_URL_OBJECT, useStorage, withErrorBoundary, withSuspense } from '@extension/shared';
import { extensionConfigStorage, DEFAULT_OPERATIONAL_HOURS_CONFIG } from '@extension/storage';
import { cn, ErrorDisplay, LoadingSpinner, Select, Switch } from '@extension/ui';
import { type ExecutionConfig, type OperationalHours } from '@extension/types';
import { Fragment } from 'react';

const HOURS = Array.from({ length: 24 }, (_, i) => i);
const DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'] as const;

type DayName = (typeof DAYS)[number];

const Options = () => {
  const { enabled, config } = useStorage(extensionConfigStorage);

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

  return (
    <div className="min-h-screen bg-gray-900 p-6 text-gray-100">
      <div className="mx-auto max-w-2xl space-y-8">
        <header className="text-center">
          <h1 className="mb-1 text-2xl font-semibold">Extension Settings</h1>
          <p className="text-sm text-gray-400">Configure your extension preferences</p>
        </header>

        {/* Enable Extension Switch */}
        <div className="flex items-center justify-between rounded-lg bg-gray-800 p-4">
          <div>
            <h2 className="font-medium">Enable Extension</h2>
            <p className="text-sm text-gray-400">Turn the extension on or off</p>
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
              <h2 className="mb-4 text-xl font-medium">Authentication</h2>
              <div className="rounded-lg bg-gray-800 p-4">
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-300">API Token</label>
                  <input
                    type="password"
                    value={config.token || ''}
                    onChange={e => extensionConfigStorage.updateConfig({ token: e.target.value })}
                    className="w-full rounded-md border border-gray-600 bg-gray-700 px-3 py-2 text-gray-100 placeholder-gray-400 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter your API token"
                  />
                </div>
              </div>
            </section>

            {/* Message Monitoring */}
            <section>
              <h2 className="mb-4 text-xl font-medium">Message Monitoring</h2>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                {/* Email Mode */}
                <div className="space-y-4 rounded-lg bg-gray-800 p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium">Email Monitoring</h3>
                      <p className="text-sm text-gray-400">Monitor emails for new offers</p>
                    </div>
                    <Switch
                      checked={config.emailMode || false}
                      onCheckedChange={() => handleConfigToggle('emailMode')}
                      className="data-[state=checked]:bg-blue-600 data-[state=unchecked]:bg-gray-200"
                    />
                  </div>
                  <div className="space-y-3">
                    <div>
                      <label className="mb-1 block text-sm text-gray-300">Min Refresh (seconds)</label>
                      <input
                        type="number"
                        value={config.emailRefreshMin || 30}
                        disabled={!config.emailMode}
                        onChange={e => extensionConfigStorage.updateConfig({ emailRefreshMin: Number(e.target.value) })}
                        className="w-full rounded-md border border-gray-600 bg-gray-700 px-3 py-2 text-gray-100 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-sm text-gray-300">Max Refresh (seconds)</label>
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
                      <h3 className="font-medium">Inbox Monitoring</h3>
                      <p className="text-sm text-gray-400">Monitor inbox for new offers</p>
                    </div>
                    <Switch
                      checked={config.inboxMode || false}
                      onCheckedChange={() => handleConfigToggle('inboxMode')}
                      className="data-[state=checked]:bg-blue-600 data-[state=unchecked]:bg-gray-200"
                    />
                  </div>
                  <div className="space-y-3">
                    <div>
                      <label className="mb-1 block text-sm text-gray-300">Min Refresh (seconds)</label>
                      <input
                        type="number"
                        value={config.inboxRefreshMin || 30}
                        disabled={!config.inboxMode}
                        onChange={e => extensionConfigStorage.updateConfig({ inboxRefreshMin: Number(e.target.value) })}
                        className="w-full rounded-md border border-gray-600 bg-gray-700 px-3 py-2 text-gray-100 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-sm text-gray-300">Max Refresh (seconds)</label>
                      <input
                        type="number"
                        value={config.inboxRefreshMax || 60}
                        disabled={!config.inboxMode}
                        onChange={e => extensionConfigStorage.updateConfig({ inboxRefreshMax: Number(e.target.value) })}
                        className="w-full rounded-md border border-gray-600 bg-gray-700 px-3 py-2 text-gray-100 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Operational Hours */}
            <section>
              <h2 className="mb-4 text-xl font-medium">Operational Hours</h2>
              <div className="rounded-lg bg-gray-800 p-6">
                <div className="flex flex-col items-center space-y-4">
                  {DAYS.map(day => {
                    const dayConfig = config.operationalHours?.[day] || DEFAULT_OPERATIONAL_HOURS_CONFIG;
                    return (
                      <div key={day} className="flex w-full items-center justify-center gap-6">
                        <div className="flex w-36 items-center justify-between">
                          <span className="text-gray-300">{day}</span>
                          <Switch
                            checked={dayConfig.enabled}
                            onCheckedChange={checked => handleOperationalHoursChange(day, 'enabled', checked)}
                            className="ml-4"
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
              <h2 className="mb-4 text-xl font-medium">Product Strategies</h2>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                {/* Animals */}
                <div className="space-y-4 rounded-lg bg-gray-800 p-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-medium">Animal Insurance</h3>
                    <Switch
                      checked={config.animals || false}
                      onCheckedChange={() => handleConfigToggle('animals')}
                      className="data-[state=checked]:bg-blue-600 data-[state=unchecked]:bg-gray-200"
                    />
                  </div>
                  <div className="space-y-3">
                    <div>
                      <label className="mb-1 block text-sm text-gray-300">Min Timer (seconds)</label>
                      <input
                        type="number"
                        value={config.animalTimerMin || 10}
                        disabled={!config.animals}
                        onChange={e => extensionConfigStorage.updateConfig({ animalTimerMin: Number(e.target.value) })}
                        className="w-full rounded-md border border-gray-600 bg-gray-700 px-3 py-2 text-gray-100 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-sm text-gray-300">Max Timer (seconds)</label>
                      <input
                        type="number"
                        value={config.animalTimerMax || 30}
                        disabled={!config.animals}
                        onChange={e => extensionConfigStorage.updateConfig({ animalTimerMax: Number(e.target.value) })}
                        className="w-full rounded-md border border-gray-600 bg-gray-700 px-3 py-2 text-gray-100 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-sm text-gray-300">Processing Time (seconds)</label>
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
                    <h3 className="font-medium">People Insurance</h3>
                    <Switch
                      checked={config.people || false}
                      onCheckedChange={() => handleConfigToggle('people')}
                      className="data-[state=checked]:bg-blue-600 data-[state=unchecked]:bg-gray-200"
                    />
                  </div>
                  <div className="space-y-3">
                    <div>
                      <label className="mb-1 block text-sm text-gray-300">Min Timer (minutes)</label>
                      <input
                        type="number"
                        value={config.peopleTimerMin || 20}
                        disabled={!config.people}
                        onChange={e => extensionConfigStorage.updateConfig({ peopleTimerMin: Number(e.target.value) })}
                        className="w-full rounded-md border border-gray-600 bg-gray-700 px-3 py-2 text-gray-100 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-sm text-gray-300">Max Timer (minutes)</label>
                      <input
                        type="number"
                        value={config.peopleTimerMax || 60}
                        disabled={!config.people}
                        onChange={e => extensionConfigStorage.updateConfig({ peopleTimerMax: Number(e.target.value) })}
                        className="w-full rounded-md border border-gray-600 bg-gray-700 px-3 py-2 text-gray-100 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-sm text-gray-300">Processing Time (seconds)</label>
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
                    <h3 className="font-medium">Cancer Insurance</h3>
                    <Switch
                      checked={config.people || false}
                      onCheckedChange={() => handleConfigToggle('cancer')}
                      className="data-[state=checked]:bg-blue-600 data-[state=unchecked]:bg-gray-200"
                    />
                  </div>
                  <div className="space-y-3">
                    <div>
                      <label className="mb-1 block text-sm text-gray-300">Min Timer (minutes)</label>
                      <input
                        type="number"
                        value={config.cancerTimerMin || 20}
                        disabled={!config.cancer}
                        onChange={e => extensionConfigStorage.updateConfig({ cancerTimerMin: Number(e.target.value) })}
                        className="w-full rounded-md border border-gray-600 bg-gray-700 px-3 py-2 text-gray-100 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-sm text-gray-300">Max Timer (minutes)</label>
                      <input
                        type="number"
                        value={config.cancerTimerMax || 60}
                        disabled={!config.cancer}
                        onChange={e => extensionConfigStorage.updateConfig({ cancerTimerMax: Number(e.target.value) })}
                        className="w-full rounded-md border border-gray-600 bg-gray-700 px-3 py-2 text-gray-100 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-sm text-gray-300">Processing Time (seconds)</label>
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
          </div>
        )}
      </div>
    </div>
  );
};

export default withErrorBoundary(withSuspense(Options, <LoadingSpinner />), ErrorDisplay);
