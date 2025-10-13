import { sendBackgroundCommand } from './sendBackgroundCommand.js';
import type { ExecutionConfig, TelemetryEvent, PDFCommand, ErrorReport } from '@extension/types';

/**
 * Typed client utilities for background commands used by content scripts.
 * Provides descriptive method names, strong typing, and throw-based error handling.
 * Eliminates repetitive success checks at callsites.
 */
export class BackgroundUtils {
  /**
   * Get extension configuration and enabled state
   */
  static async getExtensionConfig(): Promise<{ config: ExecutionConfig; enabled: boolean }> {
    const response = await sendBackgroundCommand('extension.getConfig', {});

    if (!response.success || !response.data) {
      throw new Error(`Failed to get extension config: ${response.error || 'No data returned'}`);
    }

    return response.data as { config: ExecutionConfig; enabled: boolean };
  }

  /**
   * Start a new email flow or check if it already exists
   * @returns { existed: boolean } - true if flow already existed, false if newly created
   */
  static async startEmailFlow(args: { id: string }): Promise<{ existed: boolean }> {
    const response = await sendBackgroundCommand('extension.startFlow', {
      type: 'email',
      id: args.id,
    });

    if (!response.success) {
      throw new Error(`Failed to start email flow: ${response.error}`);
    }

    return { existed: response.data === true };
  }

  /**
   * Start a new inbox flow or check if it already exists
   * @returns { existed: boolean } - true if flow already existed, false if newly created
   */
  static async startInboxFlow(args: { id: string; requestTimestamp: number }): Promise<{ existed: boolean }> {
    const response = await sendBackgroundCommand('extension.startFlow', {
      type: 'inbox',
      id: args.id,
      requestTimestamp: args.requestTimestamp,
    });

    if (!response.success) {
      throw new Error(`Failed to start inbox flow: ${response.error}`);
    }

    return { existed: response.data === true };
  }

  /**
   * Start an inbox flow and open the target URL in a single background round trip.
   * Returns { existed: true } when flow already existed and no tab is opened.
   * When newly started, returns { existed: false, tabId }.
   */
  static async startInboxFlowAndOpen(args: {
    id: string;
    requestTimestamp: number;
    url: string;
  }): Promise<{ existed: boolean; tabId?: number }> {
    const response = await sendBackgroundCommand('extension.startFlowAndOpen', {
      type: 'inbox',
      id: args.id,
      requestTimestamp: args.requestTimestamp,
      url: args.url,
    });

    if (!response.success) {
      throw new Error(`Failed to start inbox flow and open: ${response.error}`);
    }

    // New handler returns a structured data object
    if (response.data && typeof response.data === 'object') {
      const existed = response.data.existed === true || response.data === true; // back-compat
      const tabId = 'tabId' in response.data ? response.data.tabId : undefined;
      return { existed, tabId };
    }

    // Back-compat fallback if background returns boolean
    return { existed: response.data === true };
  }

  /**
   * Start a new manual flow or check if it already exists
   * @returns { existed: boolean } - true if flow already existed, false if newly created
   */
  static async startManualFlow(args: { id: string }): Promise<{ existed: boolean }> {
    const response = await sendBackgroundCommand('extension.startFlow', {
      type: 'manual',
      id: args.id,
    });

    if (!response.success) {
      throw new Error(`Failed to start inbox flow: ${response.error}`);
    }

    return { existed: response.data === true };
  }

  /**
   * Schedule tab closure after navigation with timeout
   */
  static async scheduleCloseAfterNavigation(args: { flowId: string; timeoutMs: number }): Promise<void> {
    const response = await sendBackgroundCommand('flows.scheduleCloseAfterNavigation', args);

    if (!response.success) {
      throw new Error(`Failed to schedule close after navigation: ${response.error}`);
    }
  }

  /**
   * Send telemetry events to background
   */
  static async sendTelemetry(events: TelemetryEvent[]): Promise<void> {
    const response = await sendBackgroundCommand('extension.telemetry', { events });

    if (!response.success) {
      throw new Error(`Failed to send telemetry: ${response.error}`);
    }
  }

  /**
   * Print PDF
   */
  static async printPdf(payload: PDFCommand): Promise<void> {
    const response = await sendBackgroundCommand('item.printProductConfirmation', payload);

    if (!response.success) {
      throw new Error(`Failed to execute buy offer: ${response.error}`);
    }
  }

  /**
   * Report an error to the background script
   */
  static async reportError(payload: Omit<ErrorReport, 'timestamp'> & { timestamp?: number }): Promise<void> {
    const finalPayload: ErrorReport = {
      timestamp: Date.now(),
      ...payload,
    } as ErrorReport;

    const response = await sendBackgroundCommand('extension.error', finalPayload);
    if (!response.success) {
      throw new Error(`Failed to report error: ${response.error}`);
    }
  }
}
