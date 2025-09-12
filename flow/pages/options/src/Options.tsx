import '@src/Options.css';
import { t } from '@extension/i18n';
import { useEffect, useState } from 'react';
import { PROJECT_URL_OBJECT, withErrorBoundary, withSuspense, ConfigService } from '@extension/shared';
import { cn, ErrorDisplay, LoadingSpinner, ToggleButton } from '@extension/ui';
import TimeRangeSelector from './components/TimeRangeSelector';
import { DAYS_OF_WEEK, DEFAULT_TIMEZONE, type OptionsFormData } from './types';

const DEFAULT_CONFIG: OptionsFormData = {
  enabled: true,
  operationalHours: {
    0: { enabled: false, min: 0, max: 0 },
    1: { enabled: true, min: 8, max: 17 },
    2: { enabled: true, min: 8, max: 17 },
    3: { enabled: true, min: 8, max: 17 },
    4: { enabled: true, min: 8, max: 17 },
    5: { enabled: true, min: 8, max: 17 },
    6: { enabled: false, min: 0, max: 0 },
  },
  emailMode: true,
  emailRefreshMin: 30,
  emailRefreshMax: 60,
  timerMode: false,
  randomDelay: {
    min: 5,
    max: 30,
  },
  animals: true,
  animalTimerMin: 10,
  animalTimerMax: 30,
  cancer: true,
  cancerTimerMin: 15,
  cancerTimerMax: 45,
  people: true,
  peopleTimerMin: 20,
  peopleTimerMax: 60,
};

const Options = () => {
  const [config, setConfig] = useState<OptionsFormData>(DEFAULT_CONFIG);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadConfig = async () => {
      try {
        const [config, enabled] = await Promise.all([ConfigService.getConfig(), ConfigService.isEnabled()]);
        setConfig({ ...config, enabled });
      } catch (error) {
        console.error('Error loading config:', error);
      } finally {
        setLoading(false);
      }
    };

    loadConfig();
  }, []);

  const handleConfigChange = async (updates: Partial<OptionsFormData>) => {
    const newConfig = { ...config, ...updates };
    setConfig(newConfig);

    try {
      const { enabled, ...rest } = newConfig;
      await Promise.all([ConfigService.updateConfig(rest), ConfigService.setEnabled(enabled)]);
    } catch (error) {
      console.error('Error saving config:', error);
    }
  };

  const handleOperationalHourChange = (dayIndex: number, value: (typeof config.operationalHours)[number]) => {
    handleConfigChange({
      operationalHours: {
        ...config.operationalHours,
        [dayIndex]: value,
      },
    });
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-2xl space-y-8">
        <div>
          <h2 className="text-lg font-medium text-gray-900">Extension Options</h2>
          <p className="mt-1 text-sm text-gray-500">Configure the extension behavior and operational hours.</p>
        </div>

        <div className="space-y-6 rounded-lg bg-white p-6 shadow">
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-medium text-gray-900">Enable Extension</h3>
                <p className="text-sm text-gray-500">Enable or disable the extension globally</p>
              </div>
              <ToggleButton
                selected={config.enabled}
                onClick={() => handleConfigChange({ enabled: !config.enabled })}
                className="flex-shrink-0">
                {config.enabled ? 'Enabled' : 'Disabled'}
              </ToggleButton>
            </div>

            <div className="border-t border-gray-200 pt-6">
              <div>
                <label htmlFor="token" className="block text-base font-medium text-gray-900">
                  API Token
                </label>
                <div className="mt-2">
                  <input
                    type="password"
                    id="token"
                    value={config.token}
                    onChange={e => handleConfigChange({ token: e.target.value })}
                    placeholder="Enter your API token"
                    className="focus:ring-primary-500 focus:border-primary-500 block w-full rounded-md border-2 border-gray-300 bg-white px-3 py-2 text-base shadow-sm"
                  />
                </div>
                <p className="mt-2 text-sm text-gray-600">Your API token for authenticating with the backend service</p>
              </div>
            </div>
          </div>

          <div className="border-t border-gray-200 pt-6">
            <h3 className="mb-4 text-base font-medium text-gray-900">Operational Hours</h3>
            <div className="space-y-4">
              {DAYS_OF_WEEK.map((day, index) => (
                <div key={day} className="flex items-center justify-between">
                  <span className="w-24 text-sm font-medium text-gray-900">{day}</span>
                  <TimeRangeSelector
                    value={config.operationalHours[index]}
                    onChange={value => handleOperationalHourChange(index, value)}
                  />
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-6 border-t border-gray-200 pt-6">
            <h3 className="text-base font-medium text-gray-900">Product Settings</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-medium text-gray-900">People Insurance</h4>
                  <p className="text-sm text-gray-500">Enable people insurance products</p>
                </div>
                <ToggleButton
                  selected={config.people}
                  onClick={() => handleConfigChange({ people: !config.people })}
                  className="flex-shrink-0">
                  {config.people ? 'Enabled' : 'Disabled'}
                </ToggleButton>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-medium text-gray-900">Animal Insurance</h4>
                  <p className="text-sm text-gray-500">Enable animal insurance products</p>
                </div>
                <ToggleButton
                  selected={config.animals}
                  onClick={() => handleConfigChange({ animals: !config.animals })}
                  className="flex-shrink-0">
                  {config.animals ? 'Enabled' : 'Disabled'}
                </ToggleButton>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-medium text-gray-900">Cancer Scan</h4>
                  <p className="text-sm text-gray-500">Enable cancer scan products</p>
                </div>
                <ToggleButton
                  selected={config.cancer}
                  onClick={() => handleConfigChange({ cancer: !config.cancer })}
                  className="flex-shrink-0">
                  {config.cancer ? 'Enabled' : 'Disabled'}
                </ToggleButton>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default withErrorBoundary(withSuspense(Options, <LoadingSpinner />), ErrorDisplay);
