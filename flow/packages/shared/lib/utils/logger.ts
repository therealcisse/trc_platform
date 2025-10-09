import type { MatcherId } from '@extension/types';

export interface LogEntry {
  id: string;
  timestamp: number;
  matcherId: MatcherId | string;
  flowId?: string;
  level: 'info' | 'warn' | 'error' | 'debug';
  message: string;
  metadata?: Record<string, any>;
}

interface LogStorage {
  entries: Map<string, LogEntry[]>;
  flowIndex: Map<string, string[]>;
  matcherIndex: Map<string, string[]>;
}

export class LogManager {
  private static instance: LogManager;
  private storage: LogStorage = {
    entries: new Map(),
    flowIndex: new Map(),
    matcherIndex: new Map(),
  };

  private constructor() {}

  static getInstance(): LogManager {
    if (!LogManager.instance) {
      LogManager.instance = new LogManager();
    }
    return LogManager.instance;
  }

  private generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  addEntry(entry: Omit<LogEntry, 'id'>): string {
    const id = this.generateId();
    const fullEntry: LogEntry = { ...entry, id };

    // Group entries by timestamp bucket (e.g., by minute)
    const bucketKey = Math.floor(entry.timestamp / 60000).toString(); // 1-minute buckets
    const bucket = this.storage.entries.get(bucketKey) || [];
    bucket.push(fullEntry);
    this.storage.entries.set(bucketKey, bucket);

    // Index by flowId
    if (entry.flowId) {
      const flowIds = this.storage.flowIndex.get(entry.flowId) || [];
      flowIds.push(id);
      this.storage.flowIndex.set(entry.flowId, flowIds);
    }

    // Index by matcherId
    const matcherIds = this.storage.matcherIndex.get(entry.matcherId) || [];
    matcherIds.push(id);
    this.storage.matcherIndex.set(entry.matcherId, matcherIds);

    return id;
  }

  getEntry(id: string): LogEntry | undefined {
    // Search through all buckets for the entry
    for (const [, bucket] of this.storage.entries) {
      const entry = bucket.find(e => e.id === id);
      if (entry) return entry;
    }
    return undefined;
  }

  getAllLogs(): LogEntry[] {
    const allLogs: LogEntry[] = [];
    for (const [, bucket] of this.storage.entries) {
      allLogs.push(...bucket);
    }
    return allLogs.sort((a, b) => a.timestamp - b.timestamp);
  }

  getLogsByFlowId(flowId: string): LogEntry[] {
    const entryIds = this.storage.flowIndex.get(flowId) || [];
    return entryIds
      .map(id => this.getEntry(id))
      .filter((entry): entry is LogEntry => entry !== undefined)
      .sort((a, b) => a.timestamp - b.timestamp);
  }

  getLogsByMatcherId(matcherId: string): LogEntry[] {
    const entryIds = this.storage.matcherIndex.get(matcherId) || [];
    return entryIds
      .map(id => this.getEntry(id))
      .filter((entry): entry is LogEntry => entry !== undefined)
      .sort((a, b) => a.timestamp - b.timestamp);
  }

  clearAllLogs(): void {
    this.storage.entries.clear();
  }

  clearOldLogs(olderThanMs: number = 3600000): void {
    // Default: 1 hour
    const cutoff = Date.now() - olderThanMs;
    const cutoffBucket = Math.floor(cutoff / 60000).toString();

    // Remove old buckets
    for (const [bucketKey] of this.storage.entries) {
      if (bucketKey < cutoffBucket) {
        const bucket = this.storage.entries.get(bucketKey) || [];

        // Clean up indexes
        bucket.forEach(entry => {
          if (entry.flowId) {
            const flowIds = this.storage.flowIndex.get(entry.flowId) || [];
            const filtered = flowIds.filter(id => id !== entry.id);
            if (filtered.length > 0) {
              this.storage.flowIndex.set(entry.flowId, filtered);
            } else {
              this.storage.flowIndex.delete(entry.flowId);
            }
          }

          const matcherIds = this.storage.matcherIndex.get(entry.matcherId) || [];
          const filtered = matcherIds.filter(id => id !== entry.id);
          if (filtered.length > 0) {
            this.storage.matcherIndex.set(entry.matcherId, filtered);
          } else {
            this.storage.matcherIndex.delete(entry.matcherId);
          }
        });

        this.storage.entries.delete(bucketKey);
      }
    }
  }

  exportLogs(): string {
    return JSON.stringify(this.getAllLogs(), null, 2);
  }
}

// Enhanced Log class
export class FlowLog {
  private matcherId: MatcherId | string;
  private flowId?: string;
  private messages: Array<{ message: string; timestamp: number; level: 'info' | 'warn' | 'error' | 'debug' }> = [];
  private metadata: Record<string, any> = {};
  private logManager = LogManager.getInstance();

  constructor(matcherId: MatcherId | string, flowId?: string) {
    this.matcherId = matcherId;
    this.flowId = flowId;
  }

  static withFlow(matcherId: MatcherId | string, flowId: string): FlowLog {
    return new FlowLog(matcherId, flowId);
  }

  info(message: string, metadata?: Record<string, any>): this {
    this.addMessage('info', message, metadata);
    return this;
  }

  warn(message: string, metadata?: Record<string, any>): this {
    this.addMessage('warn', message, metadata);
    return this;
  }

  error(message: string, metadata?: Record<string, any>): this {
    this.addMessage('error', message, metadata);
    return this;
  }

  debug(message: string, metadata?: Record<string, any>): this {
    this.addMessage('debug', message, metadata);
    return this;
  }

  // Backward compatibility with existing push method
  push(message: string): this {
    return this.info(message);
  }

  private addMessage(
    level: 'info' | 'warn' | 'error' | 'debug',
    message: string,
    metadata?: Record<string, any>,
  ): void {
    const timestamp = Date.now();
    this.messages.push({ message, timestamp, level });

    // Immediately add to LogManager for real-time tracking
    this.logManager.addEntry({
      timestamp,
      matcherId: this.matcherId,
      flowId: this.flowId,
      level,
      message,
      metadata: { ...this.metadata, ...metadata },
    });

    function formatLogDate(date: Date = new Date()): string {
      const pad = (num: number, size: number = 2): string => String(num).padStart(size, '0');

      const year: number = date.getFullYear();
      const month: string = pad(date.getMonth() + 1);
      const day: string = pad(date.getDate());

      const hours: string = pad(date.getHours());
      const minutes: string = pad(date.getMinutes());
      const seconds: string = pad(date.getSeconds());
      const millis: string = pad(date.getMilliseconds(), 3);

      // Example format: 2025-09-23 21:15:42.123
      return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}.${millis}`;
    }

    // Also log to console with appropriate level
    const prefix = `[${formatLogDate()}][${this.matcherId}]${this.flowId ? `[${this.flowId}]` : ''}`;
    switch (level) {
      case 'error':
        console.error(`${prefix} ${message}`, metadata || '');
        break;
      case 'warn':
        console.warn(`${prefix} ${message}`, metadata || '');
        break;
      case 'debug':
        console.debug(`${prefix} ${message}`, metadata || '');
        break;
      default:
        console.log(`${prefix} ${message}`, metadata || '');
    }
  }

  setMetadata(metadata: Record<string, any>): this {
    this.metadata = { ...this.metadata, ...metadata };
    return this;
  }

  async write(): Promise<void> {
    // // Dynamic import to avoid circular dependency
    // if (this.messages.length > 0 && typeof window !== 'undefined') {
    //   try {
    //     // Check if we're in a content script context
    //     if (chrome?.runtime?.sendMessage) {
    //       await chrome.runtime.sendMessage({
    //         type: 'extension.log',
    //         payload: {
    //           matcherId: this.matcherId,
    //           flowId: this.flowId,
    //           messages: this.messages,
    //           metadata: this.metadata,
    //           timestamp: Date.now(),
    //         },
    //       });
    //     }
    //   } catch (error) {
    //     console.error('Failed to send log to background:', error);
    //   }
    // }
  }

  // Static methods for querying logs
  static getAllLogs(): LogEntry[] {
    return LogManager.getInstance().getAllLogs();
  }

  static getFlowLogs(flowId: string): LogEntry[] {
    return LogManager.getInstance().getLogsByFlowId(flowId);
  }

  static getMatcherLogs(matcherId: MatcherId | string): LogEntry[] {
    return LogManager.getInstance().getLogsByMatcherId(matcherId);
  }

  static exportFlowTimeline(flowId: string): string {
    const logs = LogManager.getInstance().getLogsByFlowId(flowId);
    const timeline = logs
      .sort((a, b) => a.timestamp - b.timestamp)
      .map(entry => {
        const time = new Date(entry.timestamp).toISOString();
        return `${time} [${entry.level.toUpperCase()}] [${entry.matcherId}] ${entry.message}`;
      })
      .join('\n');

    return `Flow Timeline: ${flowId}\n${'='.repeat(50)}\n${timeline}`;
  }

  static cleanupOldLogs(olderThanMs?: number): void {
    LogManager.getInstance().clearOldLogs(olderThanMs);
  }

  /**
   * Query logs from background script
   * These methods work in background context or via message passing
   */
  static async queryLogs(params: {
    action: 'getAllLogs' | 'getFlowLogs' | 'getMatcherLogs' | 'exportFlowTimeline';
    flowId?: string;
    matcherId?: string;
  }): Promise<LogEntry[] | string> {
    // Check if we're in background context
    if (typeof chrome !== 'undefined' && !chrome.runtime?.sendMessage) {
      // We're in background - use LogManager directly
      const logManager = LogManager.getInstance();
      switch (params.action) {
        case 'getAllLogs':
          return logManager.getAllLogs();
        case 'getFlowLogs':
          return logManager.getLogsByFlowId(params.flowId!);
        case 'getMatcherLogs':
          return logManager.getLogsByMatcherId(params.matcherId!);
        case 'exportFlowTimeline':
          return FlowLog.exportFlowTimeline(params.flowId!);
        default:
          throw new Error(`Unknown action: ${params.action}`);
      }
    }

    // We're in content script - send message to background
    if (chrome?.runtime?.sendMessage) {
      const response = await chrome.runtime.sendMessage({
        type: 'logs.query',
        payload: params,
      });

      if (response.success) {
        return response.data;
      }
      throw new Error(response.error);
    }

    // Fallback to local LogManager (won't have all logs)
    return LogManager.getInstance().getAllLogs();
  }

  /**
   * Get log statistics (works from any context)
   */
  static async getStats(): Promise<{
    totalLogs: number;
    logsByLevel: Record<string, number>;
    logsByMatcher: Record<string, number>;
    oldestLog: Date | null;
    newestLog: Date | null;
  }> {
    if (typeof chrome !== 'undefined' && chrome.runtime?.sendMessage) {
      const response = await chrome.runtime.sendMessage({
        type: 'logs.stats',
        payload: {},
      });

      if (response.success) {
        return response.data;
      }
    }

    // Fallback for background context or no messaging
    return {
      totalLogs: 0,
      logsByLevel: {},
      logsByMatcher: {},
      oldestLog: null,
      newestLog: null,
    };
  }
}

// Export an alias for backward compatibility
export { FlowLog as Log };
