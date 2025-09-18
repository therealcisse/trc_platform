import type {
  ItemCommand,
  CommandResponse,
  ExecutionContext
} from '@extension/types';
import type { MessageHandler } from '@extension/types';
import { ConfigService } from '@extension/shared';

/**
 * item command handler - Manages item workflow execution
 */
export const itemCommandHandler: MessageHandler<'item.clickProductLink'> = async (
  payload: ItemCommand,
  sender: chrome.runtime.MessageSender
): Promise<CommandResponse> => {
  console.log('[Background] item command received from tab:', sender.tab?.id);

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
        requestId: `item-${Date.now()}`
      };
    }

    const flow = await ConfigService.getFlow(payload.id)

    if (!flow) {
      return {
        success: false,
        error: 'Flow not found',
        requestId: `item-${Date.now()}`
      };

    }

    // Create execution context
    const context: ExecutionContext = {
      tabId,
      url: sender.tab.url || '',
      matcherId: 'item-matcher',
      config,
      flowId: flow.id,
      timeout: 30000, // 30 seconds timeout
      dryRun: false
    };

    // Get product strategies from ConfigService
    const productStrategies = await ConfigService.getProductStrategies();

    // Inject and execute the item workflow
    const result = await chrome.scripting.executeScript({
      target: { tabId },
      func: async (contextJson: string, selectorsJson: string, strategiesJson: string) => {
        // This runs in the content script context
        const context = JSON.parse(contextJson);
        const selectors = JSON.parse(selectorsJson);
        const strategies = JSON.parse(strategiesJson);

        // Check if executor is available
        if (typeof (window as any).__itemExecutor === 'function') {
          // Add strategies to context
          context.productStrategies = strategies;
          return await (window as any).__itemExecutor(context, selectors);
        }

        // If not, we need to load it first
        // In production, this would be injected via manifest
        return {
          success: false,
          error: 'item executor not loaded',
          matcherId: context.matcherId,
          executorName: 'item'
        };
      },
      args: [
        JSON.stringify(context),
        JSON.stringify(payload.selectors || {
          buyButton: '.buy_now a.btn',
          titleLink: 'h1.item_title',
        }),
        JSON.stringify(productStrategies)
      ]
    });

    // Extract result from script execution
    const executionResult = result[0]?.result;

    if (!executionResult) {
      throw new Error('No result from item executor');
    }

    // Log the execution
    if (executionResult.success) {
      console.log('[Background] item workflow completed successfully:', executionResult.data);
    } else {
      console.error('[Background] item workflow failed:', executionResult.error);
    }

    return {
      success: executionResult.success,
      data: executionResult,
      error: executionResult.error,
      requestId: `item-${Date.now()}`
    };

  } catch (error) {
    console.error('[Background] Error handling item command:', error);

    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
      requestId: `item-${Date.now()}`
    };
  }
};

// Helper function to ensure item executor is loaded
export async function ensureItemExecutorLoaded(tabId: number): Promise<void> {
  try {
    // Check if executor is already loaded
    const checkResult = await chrome.scripting.executeScript({
      target: { tabId },
      func: () => typeof (window as any).__itemExecutor === 'function'
    });

    if (checkResult[0]?.result) {
      return; // Already loaded
    }

    // Inject the executor script
    await chrome.scripting.executeScript({
      target: { tabId },
      files: ['content/item.iife.js'] // This would be the compiled JS file
    });

    console.log('[Background] item executor injected into tab', tabId);
  } catch (error) {
    console.error('[Background] Error loading item executor:', error);
    throw error;
  }
}

