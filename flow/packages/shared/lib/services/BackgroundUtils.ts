import { sendBackgroundCommand } from './sendBackgroundCommand.js';
import type {
  ExecutionConfig,
  TelemetryEvent,
  BuyOfferSelectors,
  InboxSelectors,
  ItemSelectors,
  MyOfferSelectors,
  EmailSelectors,
} from '@extension/types';

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
   * Schedule tab closure after navigation with timeout
   */
  static async scheduleCloseAfterNavigation(args: { flowId: string; timeoutMs: number }): Promise<void> {
    const response = await sendBackgroundCommand('flows.scheduleCloseAfterNavigation', args);

    if (!response.success) {
      throw new Error(`Failed to schedule close after navigation: ${response.error}`);
    }
  }

  /**
   * Check if a flow is currently being purchased
   */
  static async isBuying(flowId: string): Promise<boolean> {
    const response = await sendBackgroundCommand('state.buying', {
      action: 'check',
      flowId,
    });

    if (!response.success) {
      throw new Error(`Failed to check buying state: ${response.error}`);
    }

    return response.data?.buying === true;
  }

  /**
   * Mark a flow as being purchased with timeout
   */
  static async markBuying(args: { flowId: string; timeout: number }): Promise<void> {
    const response = await sendBackgroundCommand('state.buying', {
      action: 'mark',
      flowId: args.flowId,
      timeout: args.timeout,
    });

    if (!response.success) {
      throw new Error(`Failed to mark buying state: ${response.error}`);
    }
  }

  /**
   * Clear buying state for a flow
   */
  static async clearBuying(flowId: string): Promise<void> {
    const response = await sendBackgroundCommand('state.buying', {
      action: 'clear',
      flowId,
    });

    if (!response.success) {
      throw new Error(`Failed to clear buying state: ${response.error}`);
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
   * Execute buy offer workflow
   */
  static async executeBuyOffer(args: { id: string; selectors: BuyOfferSelectors }): Promise<any> {
    const response = await sendBackgroundCommand('buyOffer.execute', args);

    if (!response.success) {
      throw new Error(`Failed to execute buy offer: ${response.error}`);
    }

    return response.data;
  }

  /**
   * Scan inbox and open MyOffer links
   */
  static async scanInboxAndOpenMyOfferLink(args: { selectors: InboxSelectors }): Promise<any> {
    const response = await sendBackgroundCommand('inbox.openMyOfferLink', args);

    if (!response.success) {
      throw new Error(`Failed to scan inbox and open links: ${response.error}`);
    }

    return response.data;
  }

  /**
   * Click item buy button
   */
  static async clickItemBuyButton(args: { id: string; selectors: ItemSelectors }): Promise<any> {
    const response = await sendBackgroundCommand('item.clickProductLink', args);

    if (!response.success) {
      throw new Error(`Failed to click item buy button: ${response.error}`);
    }

    return response.data;
  }

  /**
   * Open MyOffer item link
   */
  static async openMyOfferItemLink(args: { selectors: MyOfferSelectors }): Promise<any> {
    const response = await sendBackgroundCommand('myOffer.clickProductLink', args);

    if (!response.success) {
      throw new Error(`Failed to open MyOffer item link: ${response.error}`);
    }

    return response.data;
  }

  /**
   * Open unread email and click item link
   */
  static async openUnreadEmailAndClickItemLink(args: { selectors: EmailSelectors }): Promise<any> {
    const response = await sendBackgroundCommand('email.openUnreadAndClickLink', args);

    if (!response.success) {
      throw new Error(`Failed to open unread email and click link: ${response.error}`);
    }

    return response.data;
  }
}
