import '@src/Options.css';
import { t } from '@extension/i18n';
import { TabManager } from '@extension/shared';
import { PROJECT_URL_OBJECT, useStorage, withErrorBoundary, withSuspense } from '@extension/shared';
import { extensionConfigStorage, DEFAULT_OPERATIONAL_HOURS_CONFIG } from '@extension/storage';
import { cn, ErrorDisplay, LoadingSpinner, Select, Switch } from '@extension/ui';
import { Fragment, useState } from 'react';
import type { ExecutionConfig, OperationalHours, ProcessingTimeWindow } from '@extension/types';
import { LocalTime, LocalTimeUtils } from '@extension/types';

const HOUR_OPTIONS = Array.from({ length: 24 }, (_, h) => ({ value: h, label: String(h).padStart(2, '0') }));
const MINUTE_OPTIONS = Array.from({ length: 60 }, (_, m) => ({ value: m, label: String(m).padStart(2, '0') }));
const DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'] as const;

const getDayTranslation = (day: DayName) => t(`days_${day.toLowerCase()}`);

function TimePicker({
  value,
  disabled,
  onChange,
}: {
  value: LocalTime;
  disabled?: boolean;
  onChange: (t: LocalTime) => void;
}) {
  return (
    <div className="flex items-center gap-2">
      <Select
        value={value.hour}
        onChange={v => onChange(LocalTime.of(Number(v), value.minute))}
        disabled={disabled}
        options={HOUR_OPTIONS}
        className="w-20 border-gray-600 bg-gray-700 text-gray-100"
      />
      <span className="text-gray-400">:</span>
      <Select
        value={value.minute}
        onChange={v => onChange(LocalTime.of(value.hour, Number(v)))}
        disabled={disabled}
        options={MINUTE_OPTIONS}
        className="w-20 border-gray-600 bg-gray-700 text-gray-100"
      />
    </div>
  );
}

type DayName = (typeof DAYS)[number];

type ProductWindowsKey = 'animalProcessingTimeWindows' | 'peopleProcessingTimeWindows' | 'cancerProcessingTimeWindows';

type ProcessingTimeWindowsEditorProps = {
  windows: ProcessingTimeWindow[];
  disabled?: boolean;
  productWindowsKey: ProductWindowsKey;
  baseSeconds: number;
};

function ProcessingTimeWindowsEditor({
  windows,
  disabled,
  productWindowsKey,
  baseSeconds,
}: ProcessingTimeWindowsEditorProps) {
  const isWindowActiveNow = (w: ProcessingTimeWindow): boolean => {
    if (!w.enabled) return false;
    const now = LocalTime.now();
    const nowM = LocalTimeUtils.toMinutesOfDay(now);
    const minM = LocalTimeUtils.toMinutesOfDay(w.min);
    const maxM = LocalTimeUtils.toMinutesOfDay(w.max);
    if (minM <= maxM) return nowM >= minM && nowM <= maxM;
    return nowM >= minM || nowM <= maxM; // wrap-around
  };

  const updateWindows = (next: ProcessingTimeWindow[]) => {
    // Persist only the specific windows array
    extensionConfigStorage.updateConfig({ [productWindowsKey]: next } as unknown as Partial<ExecutionConfig>);
  };

  const addWindow = () => {
    const newWindow: ProcessingTimeWindow = {
      id: (globalThis.crypto?.randomUUID?.() ?? `win_${Math.random().toString(36).slice(2)}_${Date.now()}`) as string,
      min: LocalTime.of(9, 0),
      max: LocalTime.of(17, 0),
      duration: baseSeconds > 0 ? baseSeconds : 10,
      enabled: true,
    };
    updateWindows([...(windows ?? []), newWindow]);
  };

  const updateWindow = (id: string, patch: Partial<ProcessingTimeWindow>) => {
    const next = (windows ?? []).map(w => (w.id === id ? { ...w, ...patch } : w));
    updateWindows(next);
  };

  const moveWindow = (index: number, direction: -1 | 1) => {
    const arr = [...(windows ?? [])];
    const newIndex = index + direction;
    if (newIndex < 0 || newIndex >= arr.length) return;
    const [item] = arr.splice(index, 1);
    arr.splice(newIndex, 0, item);
    updateWindows(arr);
  };

  const duplicateWindow = (index: number) => {
    const arr = [...(windows ?? [])];
    const item = arr[index];
    if (!item) return;
    const clone: ProcessingTimeWindow = {
      ...item,
      id: (globalThis.crypto?.randomUUID?.() ?? `win_${Math.random().toString(36).slice(2)}_${Date.now()}`) as string,
    };
    arr.splice(index + 1, 0, clone);
    updateWindows(arr);
  };

  const deleteWindow = (id: string) => {
    const next = (windows ?? []).filter(w => w.id !== id);
    updateWindows(next);
  };

  const clearAll = () => {
    updateWindows([]);
  };

  const sortByStart = () => {
    const sorted = [...(windows ?? [])].sort((a, b) => {
      const aMin = LocalTimeUtils.toMinutesOfDay(a.min);
      const bMin = LocalTimeUtils.toMinutesOfDay(b.min);
      return aMin - bMin;
    });
    updateWindows(sorted);
  };

  return (
    <div className="space-y-3 rounded-md border border-gray-700 bg-gray-900 p-3">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-sm font-medium">{t('options_processing_time_windows')}</h4>
          <p className="text-xs text-gray-400">{t('options_processing_time_windows_help')}</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={addWindow}
            disabled={disabled}
            className={cn(
              'rounded-md bg-gray-700 px-3 py-1.5 text-xs text-gray-200 hover:bg-gray-600',
              disabled && 'opacity-50',
            )}>
            {t('options_processing_time_window_add')}
          </button>
          <button
            type="button"
            onClick={sortByStart}
            disabled={disabled || (windows ?? []).length < 2}
            className={cn(
              'rounded-md bg-gray-700 px-3 py-1.5 text-xs text-gray-200 hover:bg-gray-600',
              (disabled || (windows ?? []).length < 2) && 'opacity-50',
            )}>
            {t('options_processing_time_window_sort_by_start')}
          </button>
          <button
            type="button"
            onClick={clearAll}
            disabled={disabled || (windows ?? []).length === 0}
            className={cn(
              'rounded-md bg-gray-700 px-3 py-1.5 text-xs text-gray-200 hover:bg-gray-600',
              (disabled || (windows ?? []).length === 0) && 'opacity-50',
            )}>
            {t('options_processing_time_window_clear_all')}
          </button>
        </div>
      </div>

      <div className="space-y-2">
        {(windows ?? []).length === 0 ? (
          <p className="text-xs text-gray-400">{t('options_processing_time_window_empty')}</p>
        ) : (
          (windows ?? []).map((w, idx) => {
            const active = isWindowActiveNow(w);
            return (
              <div
                key={w.id}
                className={cn(
                  'flex flex-wrap items-center gap-3 rounded-md bg-gray-800 p-3',
                  !w.enabled && 'opacity-60',
                )}>
                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    onClick={() => moveWindow(idx, -1)}
                    disabled={disabled || idx === 0}
                    className={cn(
                      'h-7 w-7 rounded bg-gray-700 text-gray-200 hover:bg-gray-600',
                      (disabled || idx === 0) && 'opacity-50',
                    )}>
                    ↑
                  </button>
                  <button
                    type="button"
                    onClick={() => moveWindow(idx, 1)}
                    disabled={disabled || idx === (windows?.length ?? 0) - 1}
                    className={cn(
                      'h-7 w-7 rounded bg-gray-700 text-gray-200 hover:bg-gray-600',
                      (disabled || idx === (windows?.length ?? 0) - 1) && 'opacity-50',
                    )}>
                    ↓
                  </button>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-400">{t('options_processing_time_window_enabled')}</span>
                  <Switch
                    checked={w.enabled}
                    disabled={disabled}
                    onCheckedChange={checked => updateWindow(w.id, { enabled: !!checked })}
                    className="data-[state=checked]:bg-blue-600 data-[state=unchecked]:bg-gray-200"
                  />
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-400">{t('options_processing_time_window_from')}</span>
                  <TimePicker
                    value={w.min}
                    disabled={disabled || !w.enabled}
                    onChange={lt => updateWindow(w.id, { min: lt })}
                  />
                  <span className="text-xs text-gray-400">{t('options_processing_time_window_to')}</span>
                  <TimePicker
                    value={w.max}
                    disabled={disabled || !w.enabled}
                    onChange={lt => updateWindow(w.id, { max: lt })}
                  />
                </div>

                <div className="flex items-center gap-2">
                  <label className="text-xs text-gray-400" htmlFor={`duration_${w.id}`}>
                    {t('options_processing_time')}
                  </label>
                  <input
                    id={`duration_${w.id}`}
                    type="number"
                    min={1}
                    step={1}
                    value={w.duration}
                    disabled={disabled || !w.enabled}
                    onChange={e => {
                      const val = parseInt(e.target.value, 10);
                      updateWindow(w.id, { duration: Number.isFinite(val) && val > 0 ? val : 1 });
                    }}
                    className={cn(
                      'w-28 rounded-md border border-gray-600 bg-gray-700 px-2 py-1 text-gray-100 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500',
                    )}
                  />
                </div>

                <div className="ml-auto flex items-center gap-2">
                  {active && w.enabled && (
                    <span className="rounded bg-green-700 px-2 py-0.5 text-xs text-green-100">
                      {t('options_processing_time_window_active_now')}
                    </span>
                  )}

                  <button
                    type="button"
                    onClick={() => duplicateWindow(idx)}
                    disabled={disabled}
                    className={cn(
                      'rounded-md bg-gray-700 px-2 py-1 text-xs text-gray-200 hover:bg-gray-600',
                      disabled && 'opacity-50',
                    )}>
                    {t('options_processing_time_window_duplicate')}
                  </button>
                  <button
                    type="button"
                    onClick={() => deleteWindow(w.id)}
                    disabled={disabled}
                    className={cn(
                      'rounded-md bg-gray-700 px-2 py-1 text-xs text-gray-200 hover:bg-gray-600',
                      disabled && 'opacity-50',
                    )}>
                    {t('options_processing_time_window_delete')}
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

const JsonDisplay = ({ data, onClose }: { data: any; onClose: () => void }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(data, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="flex h-[80vh] w-full max-w-4xl flex-col rounded-lg bg-gray-800 p-6">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-100">Flow Database</h3>
          <div className="flex items-center gap-2">
            <button
              onClick={handleCopy}
              className="flex items-center gap-2 rounded-md bg-gray-700 px-3 py-1.5 text-sm text-gray-300 transition-colors hover:bg-gray-600 hover:text-gray-100">
              {/* Copy Icon */}
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="h-4 w-4">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
              </svg>
              {copied ? 'Copied!' : 'Copy'}
            </button>
            <button
              onClick={onClose}
              className="flex h-8 w-8 items-center justify-center text-xl font-bold text-gray-400 hover:text-gray-200">
              ✕
            </button>
          </div>
        </div>
        <div className="flex-1 overflow-auto rounded bg-gray-900">
          <pre className="min-h-full whitespace-pre p-4 text-start font-mono text-sm text-green-400">
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
};

const Options = () => {
  const { enabled, config } = useStorage(extensionConfigStorage);
  const [showJsonModal, setShowJsonModal] = useState(false);
  const [flowData, setFlowData] = useState(null);

  const handleOperationalHoursChange = (
    day: DayName,
    field: keyof (typeof config.operationalHours)[string],
    value: boolean | LocalTime,
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
        // alert(t('actions_success_restored'));
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

        // alert(t('actions_success_deleted'));
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
                  {config.emailMode && (
                    <div className="space-y-3">
                      <div>
                        <label className="mb-1 block text-sm text-gray-300">{t('options_min_refresh')}</label>
                        <input
                          type="number"
                          value={config.emailRefreshMin || 30}
                          disabled={!config.emailMode}
                          onChange={e =>
                            extensionConfigStorage.updateConfig({ emailRefreshMin: Number(e.target.value) })
                          }
                          className="w-full rounded-md border border-gray-600 bg-gray-700 px-3 py-2 text-gray-100 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div>
                        <label className="mb-1 block text-sm text-gray-300">{t('options_max_refresh')}</label>
                        <input
                          type="number"
                          value={config.emailRefreshMax || 60}
                          disabled={!config.emailMode}
                          onChange={e =>
                            extensionConfigStorage.updateConfig({ emailRefreshMax: Number(e.target.value) })
                          }
                          className="w-full rounded-md border border-gray-600 bg-gray-700 px-3 py-2 text-gray-100 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                    </div>
                  )}
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
                          value={config.inboxReloadSeconds.join(', ')}
                          onChange={e => {
                            const seconds = e.target.value
                              .split(',')
                              .map(s => parseInt(s.trim()))
                              .filter(n => !isNaN(n) && n >= 0 && n < 60);
                            extensionConfigStorage.updateConfig({ inboxReloadSeconds: seconds });
                          }}
                          placeholder="4, 7"
                          className="w-full rounded-md border border-gray-600 bg-gray-700 px-3 py-2 text-gray-100 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <p className="mt-1 text-xs text-gray-400">{t('options_reload_seconds_help')}</p>
                      </div>

                      <div>
                        <label className="mb-1 block text-sm text-gray-300">{t('options_max_links_per_scan')}</label>
                        <input
                          type="number"
                          value={config.inboxMaxLinksPerScan}
                          onChange={e =>
                            extensionConfigStorage.updateConfig({
                              inboxMaxLinksPerScan: parseInt(e.target.value) || 100,
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
                          value={config.inboxPostReloadDelayMs}
                          onChange={e =>
                            extensionConfigStorage.updateConfig({
                              inboxPostReloadDelayMs: parseInt(e.target.value) || 0,
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
                          value={config.inboxInterOpenDelayMs}
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
                          <TimePicker
                            value={dayConfig.min}
                            disabled={!dayConfig.enabled}
                            onChange={lt => handleOperationalHoursChange(day, 'min', lt)}
                          />
                          <span className="text-gray-400">to</span>
                          <TimePicker
                            value={dayConfig.max}
                            disabled={!dayConfig.enabled}
                            onChange={lt => handleOperationalHoursChange(day, 'max', lt)}
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
              <div className="flex flex-col gap-4">
                {/* Animals */}
                {/* Accident */}
                <div className="rounded-lg bg-gray-800 p-4">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="font-medium">{t('options_accident_insurance')}</h3>
                      <Switch
                        checked={config.accidents}
                        onCheckedChange={() => handleConfigToggle('accidents')}
                        className="data-[state=checked]:bg-blue-600 data-[state=unchecked]:bg-gray-200"
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-sm text-gray-300">{t('options_processing_time')}</label>
                      <input
                        type="number"
                        min="0"
                        value={config.accidentProcessingTimeSeconds}
                        disabled={!config.accidents}
                        onChange={e =>
                          extensionConfigStorage.updateConfig({ accidentProcessingTimeSeconds: Number(e.target.value) })
                        }
                        className="w-full rounded-md border border-gray-600 bg-gray-700 px-3 py-2 text-gray-100 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>

                    <ProcessingTimeWindowsEditor
                      windows={config.accidentProcessingTimeWindows}
                      disabled={!config.accidents}
                      productWindowsKey="accidentProcessingTimeWindows"
                      baseSeconds={config.accidentProcessingTimeSeconds}
                    />
                  </div>
                </div>
                <div className="rounded-lg bg-gray-800 p-4">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="font-medium">{t('options_animal_insurance')}</h3>
                      <Switch
                        checked={config.animals}
                        onCheckedChange={() => handleConfigToggle('animals')}
                        className="data-[state=checked]:bg-blue-600 data-[state=unchecked]:bg-gray-200"
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-sm text-gray-300">{t('options_processing_time')}</label>
                      <input
                        type="number"
                        min="0"
                        value={config.animalProcessingTimeSeconds}
                        disabled={!config.animals}
                        onChange={e =>
                          extensionConfigStorage.updateConfig({ animalProcessingTimeSeconds: Number(e.target.value) })
                        }
                        className="w-full rounded-md border border-gray-600 bg-gray-700 px-3 py-2 text-gray-100 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>

                    <ProcessingTimeWindowsEditor
                      windows={config.animalProcessingTimeWindows}
                      disabled={!config.animals}
                      productWindowsKey="animalProcessingTimeWindows"
                      baseSeconds={config.animalProcessingTimeSeconds}
                    />
                  </div>
                </div>
                {/* People */}
                <div className="rounded-lg bg-gray-800 p-4">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="font-medium">{t('options_people_insurance')}</h3>
                      <Switch
                        checked={config.people || false}
                        onCheckedChange={() => handleConfigToggle('people')}
                        className="data-[state=checked]:bg-blue-600 data-[state=unchecked]:bg-gray-200"
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-sm text-gray-300">{t('options_processing_time')}</label>
                      <input
                        type="number"
                        min="0"
                        value={config.peopleProcessingTimeSeconds}
                        disabled={!config.people}
                        onChange={e =>
                          extensionConfigStorage.updateConfig({ peopleProcessingTimeSeconds: Number(e.target.value) })
                        }
                        className="w-full rounded-md border border-gray-600 bg-gray-700 px-3 py-2 text-gray-100 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>

                    <ProcessingTimeWindowsEditor
                      windows={config.peopleProcessingTimeWindows}
                      disabled={!config.people}
                      productWindowsKey="peopleProcessingTimeWindows"
                      baseSeconds={config.peopleProcessingTimeSeconds}
                    />
                  </div>
                </div>
                {/* Cancer */}
                <div className="rounded-lg bg-gray-800 p-4">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="font-medium">{t('options_cancer_insurance')}</h3>
                      <Switch
                        checked={config.cancer || false}
                        onCheckedChange={() => handleConfigToggle('cancer')}
                        className="data-[state=checked]:bg-blue-600 data-[state=unchecked]:bg-gray-200"
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-sm text-gray-300">{t('options_processing_time')}</label>
                      <input
                        type="number"
                        min="0"
                        value={config.cancerProcessingTimeSeconds}
                        disabled={!config.cancer}
                        onChange={e =>
                          extensionConfigStorage.updateConfig({ cancerProcessingTimeSeconds: Number(e.target.value) })
                        }
                        className="w-full rounded-md border border-gray-600 bg-gray-700 px-3 py-2 text-gray-100 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>

                    <ProcessingTimeWindowsEditor
                      windows={config.cancerProcessingTimeWindows}
                      disabled={!config.cancer}
                      productWindowsKey="cancerProcessingTimeWindows"
                      baseSeconds={config.cancerProcessingTimeSeconds}
                    />
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
