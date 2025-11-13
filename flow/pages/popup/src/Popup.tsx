import '@src/Popup.css';
import { t } from '@extension/i18n';
import { withErrorBoundary, withSuspense, ConfigService } from '@extension/shared';
import { Switch, ErrorDisplay, LoadingSpinner } from '@extension/ui';
import { useEffect, useState, useCallback } from 'react';
import type { Flow } from '@extension/types';

const Popup = () => {
  const [enabled, setEnabled] = useState(false);
  const [loading, setLoading] = useState(true);
  const [flows, setFlows] = useState<Flow[]>([]);

  // Load initial enabled state
  useEffect(() => {
    const loadState = async () => {
      try {
        const isEnabled = await ConfigService.isEnabled();
        setEnabled(isEnabled);
      } catch (error) {
        console.error('Error loading extension state:', error);
      } finally {
        setLoading(false);
      }
    };

    loadState();
  }, []);

  // Fetch flows from database
  const fetchFlows = useCallback(async () => {
    try {
      const flowsResponse = await chrome.runtime.sendMessage({
        type: 'extension.getAllFlows',
        payload: {},
      });

      if (flowsResponse?.success && flowsResponse.data) {
        const dbFlows = flowsResponse.data as Flow[];
        // Sort by timestamp (newest first)
        const sortedFlows = [...dbFlows].sort((a, b) => b.timestamp - a.timestamp);
        setFlows(sortedFlows);
      }
    } catch (error) {
      console.error('Failed to fetch flows:', error);
    }
  }, []);

  // Auto-refresh flows every 5 seconds
  useEffect(() => {
    fetchFlows();
    const interval = setInterval(fetchFlows, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, [fetchFlows]);

  const handleToggleEnabled = async () => {
    try {
      await ConfigService.toggleEnabled();
      setEnabled(!enabled);
    } catch (error) {
      console.error('Error toggling extension state:', error);
    }
  };

  const formatTime = (timestamp: number) =>
    new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });

  const formatDuration = (flow: Flow) => {
    let duration: number;
    let suffix: string;

    if (flow.status === 'done' && flow.doneTimestamp) {
      // For completed flows, use fixed duration
      duration = flow.doneTimestamp - flow.timestamp;
      suffix = '';
    } else {
      // For running flows, calculate time elapsed
      duration = Date.now() - flow.timestamp;
      suffix = ' ago';
    }

    const seconds = Math.floor(duration / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) {
      return `${hours}h ${minutes % 60}m${suffix}`;
    }
    if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s${suffix}`;
    }
    return `${seconds}s${suffix}`;
  };

  const getStatusBadge = (status: 'running' | 'done' | 'failed') => {
    switch (status) {
      case 'done':
        return <span className="rounded bg-green-100 px-2 py-0.5 text-xs text-green-700">{t('status_done')}</span>;
      case 'failed':
        return <span className="rounded bg-red-100 px-2 py-0.5 text-xs text-red-700">{t('status_failed')}</span>;
      case 'running':
        return <span className="rounded bg-blue-100 px-2 py-0.5 text-xs text-blue-700">{t('status_running')}</span>;
    }
  };

  const getSourceBadge = (source: 'email' | 'inbox' | 'manual') => {
    switch (source) {
      case 'email':
        return <span className="rounded bg-purple-100 px-2 py-0.5 text-xs text-purple-700">{t('source_email')}</span>;
      case 'inbox':
        return <span className="rounded bg-orange-100 px-2 py-0.5 text-xs text-orange-700">{t('source_inbox')}</span>;
      case 'manual':
        return <span className="rounded bg-orange-100 px-2 py-0.5 text-xs text-orange-700">{t('source_manual')}</span>;
    }
  };

  if (loading) {
    return (
      <div className="flex h-full w-full items-center justify-center bg-white">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="fixed inset-0 flex h-full w-full flex-col bg-white">
      {/* Header with Enable Switch - Fixed height */}
      <div className="flex h-14 flex-shrink-0 items-center justify-between border-b bg-gray-50 px-4">
        <div className="flex items-center gap-3">
          <label className="cursor-pointer select-none text-sm font-medium text-gray-700" onClick={handleToggleEnabled}>
            {t('popup_enable_extension')}
          </label>
        </div>
        <div className="flex items-center gap-2">
          <Switch
            checked={enabled}
            onCheckedChange={handleToggleEnabled}
            className="data-[state=checked]:bg-blue-600 data-[state=unchecked]:bg-gray-200"
          />
        </div>
      </div>

      {/* Main Content Area - Takes remaining height */}
      <div className="flex min-h-0 flex-1 flex-col">
        <div className="flex-shrink-0 border-b bg-gray-100 px-4 py-2">
          <h2 className="text-sm font-semibold text-gray-700">{t('popup_active_flows', flows.length.toString())}</h2>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto">
          {flows.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <div className="mb-2">{t('popup_no_flows')}</div>
              <div className="text-xs">{t('popup_flows_appear_here')}</div>
            </div>
          ) : (
            <div className="divide-y">
              {flows.map(flow => (
                <div key={flow.id} className="p-3 transition-colors hover:bg-gray-50">
                  <div className="mb-1 flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs text-gray-600">{flow.id}</span>
                      {getStatusBadge(flow.status)}
                    </div>
                    {getSourceBadge(flow.source)}
                  </div>

                  <div className="space-y-1 text-xs text-gray-500">
                    <div className="flex items-center gap-2">
                      <span>{t('popup_started', formatTime(flow.requestTimestamp))}</span>
                      <span>•</span>
                      <span>
                        {flow.status === 'done' || flow.status === 'failed'
                          ? t('popup_duration', formatDuration(flow))
                          : formatDuration(flow)}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default withErrorBoundary(withSuspense(Popup, <LoadingSpinner />), ErrorDisplay);
