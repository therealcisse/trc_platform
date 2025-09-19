import { LogManager, type LogEntry } from '@extension/shared';
import type { MatcherId } from '@extension/types';

// Initialize LogManager in background context
const logManager = LogManager.getInstance();

// Background logger service that handles log operations
export class BackgroundLoggerService {
  /**
   * Process incoming log entries from content scripts
   */
  static handleLogMessage(payload: {
    matcherId: MatcherId | string;
    flowId?: string;
    messages: Array<{ message: string; timestamp: number; level: 'info' | 'warn' | 'error' | 'debug' }>;
    metadata?: Record<string, any>;
  }): void {
    const { matcherId, flowId, messages, metadata } = payload;

    // Add each message to the LogManager
    messages.forEach(({ message, timestamp, level }) => {
      logManager.addEntry({
        timestamp,
        matcherId,
        flowId,
        level,
        message,
        metadata,
      });
    });

    console.log(`[LoggerService] Stored ${messages.length} log entries for ${flowId || matcherId}`);
  }

  /**
   * Query logs by various criteria
   */
  static queryLogs(params: {
    action: 'getAllLogs' | 'getFlowLogs' | 'getMatcherLogs' | 'exportFlowTimeline' | 'clearOldLogs';
    flowId?: string;
    matcherId?: string;
    olderThanMs?: number;
  }): LogEntry[] | string | void {
    switch (params.action) {
      case 'getAllLogs':
        return logManager.getAllLogs();

      case 'getFlowLogs':
        if (!params.flowId) throw new Error('flowId required for getFlowLogs');
        return logManager.getLogsByFlowId(params.flowId);

      case 'getMatcherLogs':
        if (!params.matcherId) throw new Error('matcherId required for getMatcherLogs');
        return logManager.getLogsByMatcherId(params.matcherId);

      case 'exportFlowTimeline':
        if (!params.flowId) throw new Error('flowId required for exportFlowTimeline');
        const logs = logManager.getLogsByFlowId(params.flowId);
        const timeline = logs
          .sort((a, b) => a.timestamp - b.timestamp)
          .map(entry => {
            const time = new Date(entry.timestamp).toISOString();
            return `${time} [${entry.level.toUpperCase()}] [${entry.matcherId}] ${entry.message}`;
          })
          .join('\n');
        return `Flow Timeline: ${params.flowId}\n${'='.repeat(50)}\n${timeline}`;

      case 'clearOldLogs':
        logManager.clearOldLogs(params.olderThanMs);
        return;

      default:
        throw new Error(`Unknown log query action: ${params.action}`);
    }
  }

  /**
   * Get logs for debugging in background console
   */
  static debugLogs(flowId?: string): void {
    if (flowId) {
      const logs = logManager.getLogsByFlowId(flowId);
      console.group(`[LoggerService] Flow Logs: ${flowId}`);
      logs.forEach(log => {
        const time = new Date(log.timestamp).toISOString();
        console.log(`${time} [${log.level.toUpperCase()}] ${log.message}`, log.metadata || '');
      });
      console.groupEnd();
    } else {
      const logs = logManager.getAllLogs();
      console.group('[LoggerService] All Logs');
      logs.forEach(log => {
        const time = new Date(log.timestamp).toISOString();
        console.log(`${time} [${log.flowId || 'no-flow'}] [${log.level.toUpperCase()}] ${log.message}`, log.metadata || '');
      });
      console.groupEnd();
    }
  }

  /**
   * Export logs to file for debugging
   */
  static exportAllLogs(): string {
    return JSON.stringify(logManager.getAllLogs(), null, 2);
  }

  /**
   * Get statistics about stored logs
   */
  static getLogStats(): {
    totalLogs: number;
    logsByLevel: Record<string, number>;
    logsByMatcher: Record<string, number>;
    oldestLog: Date | null;
    newestLog: Date | null;
  } {
    const logs = logManager.getAllLogs();
    const stats = {
      totalLogs: logs.length,
      logsByLevel: {} as Record<string, number>,
      logsByMatcher: {} as Record<string, number>,
      oldestLog: null as Date | null,
      newestLog: null as Date | null,
    };

    if (logs.length === 0) return stats;

    logs.forEach(log => {
      // Count by level
      stats.logsByLevel[log.level] = (stats.logsByLevel[log.level] || 0) + 1;

      // Count by matcher
      stats.logsByMatcher[log.matcherId] = (stats.logsByMatcher[log.matcherId] || 0) + 1;
    });

    // Get time range
    const sortedLogs = logs.sort((a, b) => a.timestamp - b.timestamp);
    stats.oldestLog = new Date(sortedLogs[0].timestamp);
    stats.newestLog = new Date(sortedLogs[sortedLogs.length - 1].timestamp);

    return stats;
  }
}

// Expose logger service to global scope for debugging
if (typeof globalThis !== 'undefined') {
  (globalThis as any).LoggerService = BackgroundLoggerService;
}
