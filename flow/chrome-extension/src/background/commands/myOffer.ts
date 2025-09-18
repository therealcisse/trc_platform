import type {
  MyOfferCommand,
  CommandResponse,
} from '@extension/types';
import type { MessageHandler } from '@extension/types';
import { ConfigService } from '@extension/shared';
import { MATCHER_IDS } from '@extension/types';

/**
 * myOffer command handler - Manages myOffer workflow execution
 */
export const myOfferCommandHandler: MessageHandler<'myOffer.clickProductLink'> = async (
  payload: MyOfferCommand,
  sender: chrome.runtime.MessageSender
): Promise<CommandResponse> => {
  console.log('[Background] myOffer command received from tab:', sender.tab?.id);

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
        requestId: payload.id
      };
    }

    // Create execution context
    const context: Record<string, any> = {
      tabId,
      url: sender.tab.url || '',
      matcherId: MATCHER_IDS.MY_OFFER,
      config,
      timeout: 30000, // 30 seconds timeout
      dryRun: false
    };

    // Get product strategies from ConfigService
    const productStrategies = await ConfigService.getProductStrategies();

    // Inject and execute the myOffer workflow
    const result = await chrome.scripting.executeScript({
      target: { tabId },
      func: async (contextJson: string, selectorsJson: string, strategiesJson: string) => {
        // This runs in the content script context
        const context = JSON.parse(contextJson);
        const selectors = JSON.parse(selectorsJson);
        const strategies = JSON.parse(strategiesJson);

        // Check if executor is available
        if (typeof (window as any).__myOfferExecutor === 'function') {
          // Add strategies to context
          context.productStrategies = strategies;
          return await (window as any).__myOfferExecutor(context, selectors);
        }

        // If not, we need to load it first
        // In production, this would be injected via manifest
        return {
          success: false,
          error: 'myOffer executor not loaded',
          matcherId: context.matcherId,
          executorName: 'myOffer'
        };
      },
      args: [
        JSON.stringify(context),
        JSON.stringify(payload.selectors || {
          itemLink: '#my_area table.message_center_message td.content a',
          titleLink: 'h1.item_title',
          requestTimestampElement: '.message_center_message thead tr td:last-child',
        }),
        JSON.stringify(productStrategies)
      ]
    });

    // Extract result from script execution
    const executionResult = result[0]?.result;

    if (!executionResult) {
      throw new Error('No result from myOffer executor');
    }

    // Log the execution
    if (executionResult.success) {
      console.log('[Background] myOffer workflow completed successfully:', executionResult.data);
    } else {
      console.error('[Background] myOffer workflow failed:', executionResult.error);
    }

    return {
      success: executionResult.success,
      data: executionResult,
      error: executionResult.error,
      requestId: payload.id
    };

  } catch (error) {
    console.error('[Background] Error handling myOffer command:', error);

    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
      requestId: payload.id
    };
  }
};

// Helper function to ensure myOffer executor is loaded
export async function ensureMyOfferExecutorLoaded(tabId: number): Promise<void> {
  try {
    // Check if executor is already loaded
    const checkResult = await chrome.scripting.executeScript({
      target: { tabId },
      func: () => typeof (window as any).__myOfferExecutor === 'function'
    });

    if (checkResult[0]?.result) {
      return; // Already loaded
    }

    // Inject the executor script
    await chrome.scripting.executeScript({
      target: { tabId },
      files: ['content/myOffer.iife.js'] // This would be the compiled JS file
    });

    console.log('[Background] myOffer executor injected into tab', tabId);
  } catch (error) {
    console.error('[Background] Error loading myOffer executor:', error);
    throw error;
  }
}


