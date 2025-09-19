import type {
  InboxCommand,
  CommandResponse,
  ExecutionContext,
} from '@extension/types';
import type { MessageHandler } from '@extension/types';
import { ConfigService, Log } from '@extension/shared';
import { MATCHER_IDS } from '@extension/types';

/**
 * Main inbox command handler - processes all links in background
 */
export const inboxCommandHandler: MessageHandler<'inbox.openMyOfferLink'> = async (
  payload: InboxCommand,
  sender: chrome.runtime.MessageSender
): Promise<CommandResponse> => {
  console.log('[Background] Inbox command received from tab:', sender.tab?.id);
  const log = new Log(MATCHER_IDS.INBOX);

  try {
    if (!sender.tab?.id) {
      throw new Error('No tab ID in sender');
    }

    const tabId = sender.tab.id;

    const [config, enabled] = await Promise.all([
      ConfigService.getConfig(),
      ConfigService.isEnabled()
    ]);

    if (!enabled || !config.inboxMode) {
      return {
        success: false,
        error: 'Inbox mode is disabled',
        requestId: `inbox-${Date.now()}`
      };
    }

    const context: ExecutionContext = {
      tabId,
      url: sender.tab.url || '',
      matcherId: MATCHER_IDS.INBOX,
      config,
      timeout: 30000,
    };

    // Execute script to extract links from the page
    const result = await chrome.scripting.executeScript({
      target: { tabId },
      func: async (contextJson: string, selectorsJson: string) => {
        const context = JSON.parse(contextJson);
        const selectors = JSON.parse(selectorsJson);

        if (typeof (window as any).__inboxExecutor === 'function') {
          return await (window as any).__inboxExecutor(context, selectors);
        }

        return {
          success: false,
          error: 'Inbox executor not loaded',
          matcherId: context.matcherId,
          executorName: 'inbox'
        };
      },
      args: [
        JSON.stringify(context),
        JSON.stringify(payload.selectors || {
          titleLinks: 'table a[href*="show_message"]',
          messageRow: 'tr',
          requestTimestampElement: 'td:nth-child(3)', // Erhalten column

        })
      ]
    });

    console.log('[Background] Inbox processing complete:', JSON.stringify(result));

    return {
      success: true,
      data: {},
      requestId: `inbox-${Date.now()}`
    };

  } catch (error) {
    console.error('[Background] Error handling inbox command:', error);
    log.error(`Fatal error: ${error}`);
    await log.write();

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
