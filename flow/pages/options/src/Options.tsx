import '@src/Options.css';
import { t } from '@extension/i18n';
import { TabManager } from '@extension/shared';
import { PROJECT_URL_OBJECT, useStorage, withErrorBoundary, withSuspense } from '@extension/shared';
import {
  extensionConfigStorage,
  extensionRuntimeStorage,
  DEFAULT_OPERATIONAL_HOURS_CONFIG,
  migrateToLatest,
  DEFAULT_CONFIG,
} from '@extension/storage';
import { cn, ErrorDisplay, LoadingSpinner, Select, Switch } from '@extension/ui';
import { Fragment, useState } from 'react';
import type { ExecutionConfig, OperationalHours, ProcessingTimeWindow, ExtensionStorage, Flow } from '@extension/types';
import { LocalTime, LocalTimeUtils } from '@extension/types';

const HOUR_OPTIONS = Array.from({ length: 24 }, (_, h) => ({ value: h, label: String(h).padStart(2, '0') }));
const MINUTE_OPTIONS = Array.from({ length: 60 }, (_, m) => ({ value: m, label: String(m).padStart(2, '0') }));
const DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'] as const;

const getDayTranslation = (day: DayName) => t(`days_${day.toLowerCase()}` as any);

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
        onChange={v => onChange(LocalTime.of(Number(v), value.minute, 0))}
        disabled={disabled}
        options={HOUR_OPTIONS}
        className="w-20 border-gray-600 bg-gray-700 text-gray-100"
      />
      <span className="text-gray-400">:</span>
      <Select
        value={value.minute}
        onChange={v => onChange(LocalTime.of(value.hour, Number(v), 0))}
        disabled={disabled}
        options={MINUTE_OPTIONS}
        className="w-20 border-gray-600 bg-gray-700 text-gray-100"
      />
    </div>
  );
}

type DayName = (typeof DAYS)[number];

type ProductWindowsKey =
  | 'animalProcessingTimeWindows'
  | 'peopleProcessingTimeWindows'
  | 'cancerProcessingTimeWindows'
  | 'accidentProcessingTimeWindows'
  | 'healthProcessingTimeWindows';

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
    const nowS = LocalTimeUtils.toSecondsOfDay(now);
    const minS = LocalTimeUtils.toSecondsOfDay(w.min);
    const maxS = LocalTimeUtils.toSecondsOfDay(w.max);
    if (minS <= maxS) return nowS >= minS && nowS < maxS; // half-open [min, max)
    return nowS >= minS || nowS < maxS; // wrap-around
  };

  const updateWindows = (next: ProcessingTimeWindow[]) => {
    // Persist only the specific windows array
    extensionConfigStorage.updateConfig({ [productWindowsKey]: next } as unknown as Partial<ExecutionConfig>);
  };

  const addWindow = () => {
    const newWindow: ProcessingTimeWindow = {
      id: (globalThis.crypto?.randomUUID?.() ?? `win_${Math.random().toString(36).slice(2)}_${Date.now()}`) as string,
      min: LocalTime.of(8, 0, 0),
      max: LocalTime.of(20, 0, 0),
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
      const aMin = LocalTimeUtils.toSecondsOfDay(a.min);
      const bMin = LocalTimeUtils.toSecondsOfDay(b.min);
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
                      updateWindow(w.id, { duration: Number.isFinite(val) && val >= 0 ? val : 1 });
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

const JsonDisplay = ({ data, title, onClose }: { data: any; title: string; onClose: () => void }) => {
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
          <h3 className="text-lg font-medium text-gray-100">{title}</h3>
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
  const { enabled, debugMode, config } = useStorage(extensionConfigStorage);
  const [showJsonModal, setShowJsonModal] = useState(false);
  const [flowData, setFlowData] = useState<{ flows: Record<string, Flow> } | null>(null);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [configData, setConfigData] = useState<ExtensionStorage | null>(null);

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
        const flows = await extensionRuntimeStorage.flows.getAllFlowIds();
        await extensionRuntimeStorage.clearFlowDatabase();

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
      const currentData = await extensionRuntimeStorage.get();
      setFlowData({ flows: currentData.flows });
      setShowJsonModal(true);
    } catch (error) {
      console.error('Failed to get flow data:', error);
    }
  };

  const handleShowExtensionConfig = async () => {
    try {
      const currentData = await extensionConfigStorage.get();
      setConfigData(currentData);
      setShowConfigModal(true);
    } catch (error) {
      console.error('Failed to get extension config:', error);
    }
  };

  const handleBackupConfig = async () => {
    try {
      const data = await extensionConfigStorage.get();
      const json = JSON.stringify(data, null, 2);
      const suggestedName = `extension-config-${new Date().toISOString().replace(/[:]/g, '-')}.json`;

      const anyWindow = window as unknown as { showSaveFilePicker?: Function };
      if (typeof anyWindow.showSaveFilePicker === 'function') {
        // Use File System Access API when available
        const handle = await anyWindow.showSaveFilePicker({
          suggestedName,
          types: [
            {
              description: 'JSON Files',
              accept: { 'application/json': ['.json'] },
            },
          ],
        });
        const writable = await handle.createWritable();
        await writable.write(new Blob([json], { type: 'application/json' }));
        await writable.close();
      } else {
        // Fallback to an anchor download for broad browser support
        const blob = new Blob([json], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = suggestedName;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Failed to backup config:', error);
      alert(t('actions_error_backup'));
    }
  };

  const handleRestoreConfig = async () => {
    try {
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = 'application/json';

      input.onchange = async () => {
        const file = input.files?.[0];
        if (!file) return;
        try {
          const text = await file.text();
          const raw = JSON.parse(text);

          if (!confirm(t('actions_confirm_restore_from_file'))) {
            return;
          }

          const migrated = await migrateToLatest(raw, DEFAULT_CONFIG);
          await extensionConfigStorage.set(migrated);

          alert(t('actions_success_restore'));
        } catch (err) {
          console.error('Failed to restore config:', err);
          alert(t('actions_error_restore_invalid'));
        } finally {
          input.remove();
        }
      };

      // Trigger the file chooser
      input.click();
    } catch (error) {
      console.error('Restore dialog failed:', error);
      alert(t('actions_error_restore_invalid'));
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
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium">{t('options_inbox_buys_immediately')}</h4>
                          <p className="text-sm text-gray-400">{t('options_inbox_buys_immediately_description')}</p>
                        </div>
                        <Switch
                          checked={!!config.inboxBuysImmediately}
                          onCheckedChange={() => handleConfigToggle('inboxBuysImmediately')}
                          className="data-[state=checked]:bg-blue-600 data-[state=unchecked]:bg-gray-200"
                        />
                      </div>
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

                      {/* Inbox Auto-Refresh outside operational hours */}
                      <div className="inline-grid">
                        <label className="mb-1 block text-sm text-gray-300">
                          {t('options_inbox_auto_refresh_label')}
                        </label>
                        <Select
                          value={Math.round(config.inboxAutoRefreshMs / 60000)}
                          onChange={v => extensionConfigStorage.updateConfig({ inboxAutoRefreshMs: Number(v) * 60000 })}
                          options={[
                            // { value: -1, label: t('options_inbox_auto_refresh_disabled') },
                            { value: 1, label: '1' },
                            { value: 5, label: '5' },
                            { value: 10, label: '10' },
                            { value: 15, label: '15' },
                            { value: 30, label: '30' },
                          ]}
                          className="border-gray-600 bg-gray-700 text-gray-100"
                        />
                        <p className="mt-1 text-xs text-gray-400">{t('options_inbox_auto_refresh_description')}</p>
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
                    {config.accidents && (
                      <div>
                        <label className="mb-1 block text-sm text-gray-300">{t('options_processing_time')}</label>
                        <input
                          type="number"
                          min="0"
                          value={config.accidentProcessingTimeSeconds}
                          disabled={!config.accidents}
                          onChange={e =>
                            extensionConfigStorage.updateConfig({
                              accidentProcessingTimeSeconds: Number(e.target.value),
                            })
                          }
                          className="w-full rounded-md border border-gray-600 bg-gray-700 px-3 py-2 text-gray-100 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                    )}

                    {config.accidents && (
                      <ProcessingTimeWindowsEditor
                        windows={config.accidentProcessingTimeWindows}
                        disabled={!config.accidents}
                        productWindowsKey="accidentProcessingTimeWindows"
                        baseSeconds={config.accidentProcessingTimeSeconds}
                      />
                    )}
                  </div>
                </div>
                <div className="rounded-lg bg-gray-800 p-4">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="font-medium">{t('animals_title')}</h3>
                    </div>

                    {/* New centered row for Dogs and Cats switches, wrapped like Processing time windows */}
                    <div className="space-y-3 rounded-md border border-gray-700 bg-gray-900 p-3">
                      <div className="flex w-full items-center justify-center gap-12 py-2">
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-gray-300">{t('animals_dogs')}</span>
                          <Switch
                            checked={config.animal.dogs}
                            onCheckedChange={checked =>
                              extensionConfigStorage.updateConfig({
                                animal: { ...config.animal, dogs: !!checked },
                              })
                            }
                            className="data-[state=checked]:bg-blue-600 data-[state=unchecked]:bg-gray-200"
                          />
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-gray-300">{t('animals_cats')}</span>
                          <Switch
                            checked={config.animal.cats}
                            onCheckedChange={checked =>
                              extensionConfigStorage.updateConfig({
                                animal: { ...config.animal, cats: !!checked },
                              })
                            }
                            className="data-[state=checked]:bg-blue-600 data-[state=unchecked]:bg-gray-200"
                          />
                        </div>
                      </div>
                    </div>

                    {(config.animal.dogs || config.animal.cats) && (
                      <div>
                        <label className="mb-1 block text-sm text-gray-300">{t('options_processing_time')}</label>
                        <input
                          type="number"
                          min="0"
                          value={config.animalProcessingTimeSeconds}
                          disabled={!config.animal.dogs && !config.animal.cats}
                          onChange={e =>
                            extensionConfigStorage.updateConfig({ animalProcessingTimeSeconds: Number(e.target.value) })
                          }
                          className="w-full rounded-md border border-gray-600 bg-gray-700 px-3 py-2 text-gray-100 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                    )}

                    {(config.animal.dogs || config.animal.cats) && (
                      <ProcessingTimeWindowsEditor
                        windows={config.animalProcessingTimeWindows}
                        productWindowsKey="animalProcessingTimeWindows"
                        disabled={!config.animal.dogs && !config.animal.cats}
                        baseSeconds={config.animalProcessingTimeSeconds}
                      />
                    )}
                  </div>
                </div>
                {/* Health */}
                <div className="rounded-lg bg-gray-800 p-4">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="font-medium">{t('options_people_insurance')}</h3>
                      <Switch
                        checked={config.health}
                        onCheckedChange={() => handleConfigToggle('health')}
                        className="data-[state=checked]:bg-blue-600 data-[state=unchecked]:bg-gray-200"
                      />
                    </div>
                    {config.health && (
                      <div>
                        <label className="mb-1 block text-sm text-gray-300">{t('options_processing_time')}</label>
                        <input
                          type="number"
                          min="0"
                          value={config.healthProcessingTimeSeconds}
                          disabled={!config.health}
                          onChange={e =>
                            extensionConfigStorage.updateConfig({ healthProcessingTimeSeconds: Number(e.target.value) })
                          }
                          className="w-full rounded-md border border-gray-600 bg-gray-700 px-3 py-2 text-gray-100 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                    )}

                    {config.health && (
                      <ProcessingTimeWindowsEditor
                        windows={config.healthProcessingTimeWindows}
                        disabled={!config.health}
                        productWindowsKey="healthProcessingTimeWindows"
                        baseSeconds={config.healthProcessingTimeSeconds}
                      />
                    )}
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
                    {config.cancer && (
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
                    )}

                    {config.cancer && (
                      <ProcessingTimeWindowsEditor
                        windows={config.cancerProcessingTimeWindows}
                        disabled={!config.cancer}
                        productWindowsKey="cancerProcessingTimeWindows"
                        baseSeconds={config.cancerProcessingTimeSeconds}
                      />
                    )}
                  </div>
                </div>
              </div>
            </section>

            {/* Actions */}
            <section>
              <h2 className="mb-4 text-xl font-medium">{t('options_actions')}</h2>
              <div className="space-y-4">
                {/* Enable Debug Mode */}
                <div className="flex items-center justify-between rounded-lg bg-gray-800 p-4">
                  <div>
                    <h3 className="font-medium">{t('options_enable_debug_mode')}</h3>
                    <p className="text-sm text-gray-400">{t('options_enable_debug_mode_description')}</p>
                  </div>
                  <Switch
                    checked={!!debugMode}
                    onCheckedChange={() => extensionConfigStorage.toggleDebugMode()}
                    className="data-[state=checked]:bg-blue-600 data-[state=unchecked]:bg-gray-200"
                  />
                </div>
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

                {/* Show Extension Config */}
                <div className="flex items-center justify-between rounded-lg bg-gray-800 p-4">
                  <div>
                    <h3 className="font-medium">{t('options_show_extension_config')}</h3>
                    <p className="text-sm text-gray-400">{t('options_show_extension_config_description')}</p>
                  </div>
                  <button
                    onClick={handleShowExtensionConfig}
                    className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500">
                    {t('options_show_extension_config')}
                  </button>
                </div>

                {/* Backup Config */}
                <div className="flex items-center justify-between rounded-lg bg-gray-800 p-4">
                  <div>
                    <h3 className="font-medium">{t('options_backup_config')}</h3>
                    <p className="text-sm text-gray-400">{t('options_backup_config_description')}</p>
                  </div>
                  <button
                    onClick={handleBackupConfig}
                    className="rounded bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500">
                    {t('options_backup_config')}
                  </button>
                </div>

                {/* Restore Config */}
                <div className="flex items-center justify-between rounded-lg bg-gray-800 p-4">
                  <div>
                    <h3 className="font-medium">{t('options_restore_config')}</h3>
                    <p className="text-sm text-gray-400">{t('options_restore_config_description')}</p>
                  </div>
                  <button
                    onClick={handleRestoreConfig}
                    className="rounded bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500">
                    {t('options_restore_config')}
                  </button>
                </div>
              </div>
            </section>
          </div>
        )}
        {showJsonModal && flowData && (
          <JsonDisplay
            data={flowData}
            title={t('json_display_flow_database_title')}
            onClose={() => setShowJsonModal(false)}
          />
        )}
        {showConfigModal && configData && (
          <JsonDisplay
            data={configData}
            title={t('json_display_extension_config_title')}
            onClose={() => setShowConfigModal(false)}
          />
        )}
      </div>
    </div>
  );
};

export default withErrorBoundary(withSuspense(Options, <LoadingSpinner />), ErrorDisplay);
