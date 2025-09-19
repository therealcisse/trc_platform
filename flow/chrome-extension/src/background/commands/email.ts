import type {
  EmailCommand,
  CommandResponse,
  ExecutionContext
} from '@extension/types';
import type { MessageHandler } from '@extension/types';
import { ConfigService } from '@extension/shared';
import { MATCHER_IDS } from '@extension/types';

/**
 * Email command handler - Manages email workflow execution
 */
export const emailCommandHandler: MessageHandler<'email.openUnreadAndClickLink'> = async (
  payload: EmailCommand,
  sender: chrome.runtime.MessageSender
): Promise<CommandResponse> => {
  console.log('[Background] Email command received from tab:', sender.tab?.id);

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
        requestId: `email-${Date.now()}`
      };
    }

    // Create execution context
    const context: ExecutionContext = {
      tabId,
      url: sender.tab.url || '',
      matcherId: MATCHER_IDS.EMAIL,
      config,
      timeout: 30000, // 30 seconds timeout
      dryRun: false
    };

    // Inject and execute the email workflow
    const result = await chrome.scripting.executeScript({
      target: { tabId },
      func: async (contextJson: string, selectorsJson: string) => {
        // This runs in the content script context
        const context = JSON.parse(contextJson);
        const selectors = JSON.parse(selectorsJson);

        // Check if executor is available
        if (typeof (window as any).__emailExecutor === 'function') {
          return await (window as any).__emailExecutor(context, selectors);
        }

        // If not, we need to load it first
        // In production, this would be injected via manifest
        return {
          success: false,
          error: 'Email executor not loaded',
          matcherId: context.matcherId,
          executorName: 'email'
        };
      },
      args: [
        JSON.stringify(context),
        JSON.stringify(
          payload.selectors || {
            unreadEmail: '[aria-label^="Ungelesen HanseMerkur AuktionsPlattform"]',
            emailBody: '#x_body a',
            markAsReadButton: 'span',
          },
        ),
      ]
    });

    // Extract result from script execution
    const executionResult = result[0]?.result;

    if (!executionResult) {
      throw new Error('No result from email executor');
    }

    // Log the execution
    if (executionResult.success) {
      console.log('[Background] Email workflow completed successfully:', executionResult.data);
    } else {
      console.error('[Background] Email workflow failed:', executionResult.error);
    }

    return {
      success: executionResult.success,
      data: executionResult,
      error: executionResult.error,
      requestId: `email-${Date.now()}`
    };

  } catch (error) {
    console.error('[Background] Error handling email command:', error);

    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
      requestId: `email-${Date.now()}`
    };
  }
};

// Helper function to ensure email executor is loaded
export async function ensureEmailExecutorLoaded(tabId: number): Promise<void> {
  try {
    // Check if executor is already loaded
    const checkResult = await chrome.scripting.executeScript({
      target: { tabId },
      func: () => typeof (window as any).__emailExecutor === 'function'
    });

    if (checkResult[0]?.result) {
      return; // Already loaded
    }

    // Inject the executor script
    await chrome.scripting.executeScript({
      target: { tabId },
      files: ['content/email.iife.js'] // This would be the compiled JS file
    });

    console.log('[Background] Email executor injected into tab', tabId);
  } catch (error) {
    console.error('[Background] Error loading email executor:', error);
    throw error;
  }
}
