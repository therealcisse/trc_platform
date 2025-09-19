import type {
  InboxCommand,
  CommandResponse,
  ExecutionContext
} from '@extension/types';
import type { MessageHandler } from '@extension/types';
import { ConfigService } from '@extension/shared';
import { MATCHER_IDS } from '@extension/types';

/**
 * Inbox command handler - Manages inbox workflow execution
 */
export const inboxCommandHandler: MessageHandler<'inbox.openMyOfferLink'> = async (
  payload: InboxCommand,
  sender: chrome.runtime.MessageSender
): Promise<CommandResponse> => {
  console.log('[Background] Inbox command received from tab:', sender.tab?.id);

  try {
    // Validate sender tab
    if (!sender.tab?.id) {
      throw new Error('No tab ID in sender');
    }

    const tabId = sender.tab.id;

    // Get extension configuration
    const [config, enabled] = await Promise.all([
      ConfigService.getConfig(),
      ConfigService.isEnabled()
    ]);

    if (!enabled) {
      return {
        success: false,
        error: 'Extension is disabled',
        requestId: `inbox-${Date.now()}`
      };
    }

    // Create execution context
    const context: Record<string, any> = {
      tabId,
      url: sender.tab.url || '',
      matcherId: MATCHER_IDS.INBOX,
      config,
      timeout: 30000, // 30 seconds timeout
      dryRun: false
    };

    // Inject and execute the inbox workflow
    const result = await chrome.scripting.executeScript({
      target: { tabId },
      func: async (contextJson: string, selectorsJson: string) => {
        // This runs in the content script context
        const context = JSON.parse(contextJson);
        const selectors = JSON.parse(selectorsJson);

        // Check if executor is available
        if (typeof (window as any).__inboxExecutor === 'function') {
          return await (window as any).__inboxExecutor(context, selectors);
        }

        // If not, we need to load it first
        // In production, this would be injected via manifest
        return {
          success: false,
          error: 'Inbox executor not loaded',
          matcherId: context.matcherId,
          executorName: 'inbox'
        };
      },
      args: [
        JSON.stringify(context),
        JSON.stringify(
          payload.selectors || {
            unreadInbox: '[aria-label^="Ungelesen HanseMerkur AuktionsPlattform"]',
            inboxBody: '#x_body a',
            markAsReadButton: 'span',
          },
        ),
      ]
    });

    // Extract result from script execution
    const executionResult = result[0]?.result;

    if (!executionResult) {
      throw new Error('No result from inbox executor');
    }

    // Log the execution
    if (executionResult.success) {
      console.log('[Background] Inbox workflow completed successfully:', executionResult.data);
    } else {
      console.error('[Background] Inbox workflow failed:', executionResult.error);
    }

    return {
      success: executionResult.success,
      data: executionResult,
      error: executionResult.error,
      requestId: `inbox-${Date.now()}`
    };

  } catch (error) {
    console.error('[Background] Error handling inbox command:', error);

    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
      requestId: `inbox-${Date.now()}`
    };
  }
};

// Helper function to ensure inbox executor is loaded
export async function ensureInboxExecutorLoaded(tabId: number): Promise<void> {
  try {
    // Check if executor is already loaded
    const checkResult = await chrome.scripting.executeScript({
      target: { tabId },
      func: () => typeof (window as any).__inboxExecutor === 'function'
    });

    if (checkResult[0]?.result) {
      return; // Already loaded
    }

    // Inject the executor script
    await chrome.scripting.executeScript({
      target: { tabId },
      files: ['content/inbox.iife.js'] // This would be the compiled JS file
    });

    console.log('[Background] Inbox executor injected into tab', tabId);
  } catch (error) {
    console.error('[Background] Error loading inbox executor:', error);
    throw error;
  }
}
