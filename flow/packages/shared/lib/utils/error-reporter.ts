import { BackgroundUtils } from '../services/BackgroundUtils.js';
import type { ErrorReport } from '@extension/types';

export type FlowIdProvider = () => string | undefined;

function toStringSafe(x: unknown): string {
  try {
    if (x instanceof Error) return x.stack || `${x.name}: ${x.message}`;
    if (typeof x === 'string') return x;
    return JSON.stringify(x);
  } catch {
    return String(x);
  }
}

export function installGlobalErrorHandlers(opts: { matcherId: string; getFlowId?: FlowIdProvider }): void {
  const getFlowId = opts.getFlowId ?? (() => undefined);

  // window.onerror style
  window.addEventListener('error', e => {
    const flowId = getFlowId();
    const payload: Omit<ErrorReport, 'timestamp'> = {
      matcherId: opts.matcherId,
      flowId,
      source: 'window.error',
      message: e.message || 'Unknown window error',
      name: e.error?.name,
      stack: e.error?.stack,
      filename: e.filename,
      lineno: e.lineno,
      colno: e.colno,
      url: window.location.href,
      userAgent: navigator.userAgent,
      metadata: { type: 'window.error' },
    };

    BackgroundUtils.reportError(payload).catch(() => {
      // swallow to avoid recursive errors
    });
  });

  // Unhandled promise rejections
  window.addEventListener('unhandledrejection', e => {
    const flowId = getFlowId();
    const reasonStr = toStringSafe(e.reason);

    const payload: Omit<ErrorReport, 'timestamp'> = {
      matcherId: opts.matcherId,
      flowId,
      source: 'unhandledrejection',
      message: 'Unhandled promise rejection',
      name: (e.reason && (e.reason as any).name) || undefined,
      stack: (e.reason && (e.reason as any).stack) || undefined,
      reason: e.reason,
      url: window.location.href,
      userAgent: navigator.userAgent,
      metadata: { type: 'unhandledrejection', rawReason: reasonStr },
    };

    BackgroundUtils.reportError(payload).catch(() => {
      // swallow to avoid recursive errors
    });
  });
}
