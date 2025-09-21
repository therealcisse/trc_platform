import '@src/Popup.css';
import { t } from '@extension/i18n';
import { withErrorBoundary, withSuspense, ConfigService } from '@extension/shared';
import { Switch, ErrorDisplay, LoadingSpinner } from '@extension/ui';
import { useEffect, useState, useCallback } from 'react';
import type { LogEntry } from '@extension/shared';

interface FlowSummary {
  flowId: string;
  matcherId: string;
  startTime: number;
  lastActivity: number;
  logCount: number;
  hasErrors: boolean;
  status?: 'active' | 'done' | 'error';
}

const Popup = () => {
  const [enabled, setEnabled] = useState(false);
  const [loading, setLoading] = useState(true);
  const [flows, setFlows] = useState<FlowSummary[]>([]);
  const [selectedFlowId, setSelectedFlowId] = useState<string | null>(null);
  const [flowLogs, setFlowLogs] = useState<LogEntry[]>([]);
  const [autoRefresh] = useState(true);

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

  // Fetch all logs and extract flow summaries
  const fetchFlows = useCallback(async () => {
    try {
      const response = await chrome.runtime.sendMessage({
        type: 'logs.query',
        payload: { action: 'getAllLogs' },
      });

      if (response?.success && response.data) {
        const logs = response.data as LogEntry[];

        // Group logs by flowId
        const flowMap = new Map<string, FlowSummary>();

        logs.forEach(log => {
          if (!log.flowId) return;

          if (!flowMap.has(log.flowId)) {
            flowMap.set(log.flowId, {
              flowId: log.flowId,
              matcherId: log.matcherId,
              startTime: log.timestamp,
              lastActivity: log.timestamp,
              logCount: 1,
              hasErrors: log.level === 'error',
              status: 'active',
            });
          } else {
            const flow = flowMap.get(log.flowId)!;
            flow.logCount++;
            flow.lastActivity = Math.max(flow.lastActivity, log.timestamp);
            flow.startTime = Math.min(flow.startTime, log.timestamp);
            if (log.level === 'error') flow.hasErrors = true;

            // Determine status from log messages
            if (
              log.message.includes('completed successfully') ||
              log.message.includes('marked as done') ||
              log.message.includes('marked as completed')
            ) {
              flow.status = 'done';
            } else if (log.message.includes('Fatal error') || log.message.includes('failed')) {
              flow.status = 'error';
            }
          }
        });

        // Convert to array and sort by last activity (newest first)
        const flowArray = Array.from(flowMap.values()).sort((a, b) => b.lastActivity - a.lastActivity);

        setFlows(flowArray);
      }
    } catch (error) {
      console.error('Failed to fetch flows:', error);
    }
  }, []);

  // Fetch logs for selected flow
  const fetchFlowLogs = useCallback(async (flowId: string) => {
    try {
      const response = await chrome.runtime.sendMessage({
        type: 'logs.query',
        payload: { action: 'getFlowLogs', flowId },
      });

      if (response?.success && response.data) {
        const logs = response.data as LogEntry[];
        // Filter to show only important logs
        const importantLogs = logs.filter(
          log =>
            log.level === 'error' ||
            log.level === 'warn' ||
            log.message.includes('Starting') ||
            log.message.includes('completed') ||
            log.message.includes('Processing') ||
            log.message.includes('EXECUTING') ||
            log.message.includes('marked as done') ||
            log.message.includes('validated') ||
            log.message.includes('Captcha') ||
            log.message.includes('Product') ||
            log.message.includes('activated') ||
            log.message.includes('triggered'),
        );
        setFlowLogs(importantLogs);
      }
    } catch (error) {
      console.error('Failed to fetch flow logs:', error);
    }
  }, []);

  // Initial fetch and auto-refresh for flow list
  useEffect(() => {
    if (!selectedFlowId && autoRefresh) {
      fetchFlows();
      const interval = setInterval(fetchFlows, 3000); // Refresh every 3 seconds
      return () => clearInterval(interval);
    }
  }, [selectedFlowId, autoRefresh, fetchFlows]);

  // Auto-refresh for flow details
  useEffect(() => {
    if (selectedFlowId && autoRefresh) {
      fetchFlowLogs(selectedFlowId);
      const interval = setInterval(() => fetchFlowLogs(selectedFlowId), 2000); // Refresh every 2 seconds
      return () => clearInterval(interval);
    }
  }, [selectedFlowId, autoRefresh, fetchFlowLogs]);

  const handleToggleEnabled = async () => {
    try {
      await ConfigService.toggleEnabled();
      setEnabled(!enabled);
    } catch (error) {
      console.error('Error toggling extension state:', error);
    }
  };

  const handleFlowClick = (flowId: string) => {
    setSelectedFlowId(flowId);
    setFlowLogs([]);
  };

  const handleBack = () => {
    setSelectedFlowId(null);
    setFlowLogs([]);
  };

  const formatTime = (timestamp: number) =>
    new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });

  const formatDuration = (start: number, end: number) => {
    const duration = end - start;
    const seconds = Math.floor(duration / 1000);
    const minutes = Math.floor(seconds / 60);
    if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    }
    return `${seconds}s`;
  };

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case 'done':
        return <span className="rounded bg-green-100 px-2 py-0.5 text-xs text-green-700">{t('status_done')}</span>;
      case 'error':
        return <span className="rounded bg-red-100 px-2 py-0.5 text-xs text-red-700">{t('status_error')}</span>;
      default:
        return <span className="rounded bg-blue-100 px-2 py-0.5 text-xs text-blue-700">{t('status_active')}</span>;
    }
  };

  const getLogLevelBadge = (level: string) => {
    switch (level) {
      case 'error':
        return <span className="font-medium text-red-600">{t('log_level_error')}</span>;
      case 'warn':
        return <span className="font-medium text-yellow-600">{t('log_level_warn')}</span>;
      case 'info':
        return <span className="font-medium text-blue-600">{t('log_level_info')}</span>;
      default:
        return <span className="font-medium text-gray-500">{t('log_level_debug')}</span>;
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
    <div className="flex h-full w-full flex-col bg-white">
      {/* Header with Enable Switch */}
      <div className="flex items-center justify-between border-b bg-gray-50 p-4">
        <div className="flex items-center gap-3">
          <Switch
            checked={enabled}
            onCheckedChange={handleToggleEnabled}
            className="data-[state=checked]:bg-blue-600 data-[state=unchecked]:bg-gray-200"
          />
          <label className="cursor-pointer select-none text-sm font-medium text-gray-700" onClick={handleToggleEnabled}>
            {t('popup_enable_extension')}
          </label>
        </div>
        <div className="flex items-center gap-2">
          {autoRefresh && (
            <div className="flex items-center gap-1">
              <div className="h-2 w-2 animate-pulse rounded-full bg-green-500" />
              <span className="text-xs text-gray-500">{t('popup_live')}</span>
            </div>
          )}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-hidden">
        {!selectedFlowId ? (
          /* Flow List View */
          <div className="flex h-full flex-col">
            <div className="border-b bg-gray-100 px-4 py-2">
              <h2 className="text-sm font-semibold text-gray-700">
                {t('popup_active_flows', flows.length.toString())}
              </h2>
            </div>

            <div className="flex-1 overflow-y-auto">
              {flows.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  <div className="mb-2">{t('popup_no_flows')}</div>
                  <div className="text-xs">{t('popup_flows_appear_here')}</div>
                </div>
              ) : (
                <div className="divide-y">
                  {flows.map(flow => (
                    <button
                      key={flow.flowId}
                      onClick={() => handleFlowClick(flow.flowId)}
                      className="w-full p-3 text-left transition-colors hover:bg-gray-50">
                      <div className="mb-1 flex items-start justify-between">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs text-gray-600">{flow.flowId.substring(0, 8)}...</span>
                          {getStatusBadge(flow.status)}
                        </div>
                        {flow.hasErrors && (
                          <span className="text-xs font-medium text-red-600">{t('popup_has_errors')}</span>
                        )}
                      </div>

                      <div className="space-y-1 text-xs text-gray-500">
                        <div className="flex items-center gap-2">
                          <span>{t('popup_matcher', flow.matcherId)}</span>
                          <span>•</span>
                          <span>{t('popup_logs', flow.logCount.toString())}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span>{t('popup_started', formatTime(flow.startTime))}</span>
                          <span>•</span>
                          <span>{t('popup_duration', formatDuration(flow.startTime, flow.lastActivity))}</span>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ) : (
          /* Flow Detail View */
          <div className="flex h-full flex-col">
            <div className="flex items-center justify-between border-b bg-gray-100 px-4 py-2">
              <button
                onClick={handleBack}
                className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700">
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                {t('popup_back')}
              </button>

              <h2 className="text-sm font-semibold text-gray-700">
                {t('popup_flow', selectedFlowId.substring(0, 12) + '...')}
              </h2>

              <div className="text-xs text-gray-500">{t('popup_events', flowLogs.length.toString())}</div>
            </div>

            <div className="flex-1 overflow-y-auto p-2">
              {flowLogs.length === 0 ? (
                <div className="p-4 text-center text-sm text-gray-500">{t('popup_loading_logs')}</div>
              ) : (
                <div className="space-y-2">
                  {flowLogs.map((log, index) => (
                    <div
                      key={log.id || index}
                      className={`rounded border p-2 text-xs ${
                        log.level === 'error'
                          ? 'border-red-200 bg-red-50'
                          : log.level === 'warn'
                            ? 'border-yellow-200 bg-yellow-50'
                            : 'border-gray-200 bg-white'
                      }`}>
                      <div className="mb-1 flex items-start justify-between">
                        <div className="flex items-center gap-2">
                          {getLogLevelBadge(log.level)}
                          <span className="text-gray-500">{formatTime(log.timestamp)}</span>
                        </div>
                        <span className="text-gray-400">{log.matcherId}</span>
                      </div>

                      <div
                        className={`mt-1 ${
                          log.level === 'error'
                            ? 'text-red-700'
                            : log.level === 'warn'
                              ? 'text-yellow-700'
                              : 'text-gray-700'
                        }`}>
                        {log.message}
                      </div>

                      {log.metadata && Object.keys(log.metadata).length > 0 && (
                        <div className="mt-1 text-gray-500">
                          {Object.entries(log.metadata).map(([key, value]) => (
                            <div key={key}>
                              {key}: {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default withErrorBoundary(withSuspense(Popup, <LoadingSpinner />), ErrorDisplay);
