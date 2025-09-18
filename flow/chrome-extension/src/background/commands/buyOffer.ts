import type {
  BuyOfferCommand,
  CommandResponse,
  ExecutionContext
} from '@extension/types';
import type { MessageHandler } from '@extension/types';
import { ConfigService } from '@extension/shared';

/**
 * Buy Offer command handler - Manages purchase workflow execution
 */
export const buyOfferCommandHandler: MessageHandler<'buyOffer.execute'> = async (
  payload: BuyOfferCommand,
  sender: chrome.runtime.MessageSender
): Promise<CommandResponse> => {
  console.log('[Background] Buy offer command received from tab:', sender.tab?.id);

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
        requestId: `buyOffer-${Date.now()}`
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
      matcherId: 'buy-offer-matcher',
      productId: payload.productId,
      config,
      timeout: 60000, // 60 seconds timeout due to delay
      dryRun: false
    };

    // Inject and execute the buy offer workflow
    const result = await chrome.scripting.executeScript({
      target: { tabId },
      func: async (contextJson: string, selectorsJson: string) => {
        // This runs in the content script context
        const context = JSON.parse(contextJson);
        const selectors = JSON.parse(selectorsJson);

        // Check if executor is available
        if (typeof (window as any).__buyOfferExecutor === 'function') {
          return await (window as any).__buyOfferExecutor(context, selectors);
        }

        // If not, we need to load it first
        // In production, this would be injected via manifest
        return {
          success: false,
          error: 'Buy offer executor not loaded',
          matcherId: context.matcherId,
          executorName: 'buyOffer'
        };
      },
      args: [
        JSON.stringify(context),
        JSON.stringify(payload.selectors || {
          productTitle: '#page_buy_now h2',
          buyFormButton: '#buyFormBtn'
        })
      ]
    });

    // Extract result from script execution
    const executionResult = result[0]?.result;

    if (!executionResult) {
      throw new Error('No result from buy offer executor');
    }

    // Log the execution
    if (executionResult.success) {
      console.log('[Background] Buy offer workflow completed successfully:', executionResult.data);
    } else {
      console.error('[Background] Buy offer workflow failed:', executionResult.error);
    }

    return {
      success: executionResult.success,
      data: executionResult,
      error: executionResult.error,
      requestId: `buyOffer-${Date.now()}`
    };

  } catch (error) {
    console.error('[Background] Error handling buy offer command:', error);

    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
      requestId: `buyOffer-${Date.now()}`
    };
  }
};

// Helper function to ensure buy offer executor is loaded
export async function ensureBuyOfferExecutorLoaded(tabId: number): Promise<void> {
  try {
    // Check if executor is already loaded
    const checkResult = await chrome.scripting.executeScript({
      target: { tabId },
      func: () => typeof (window as any).__buyOfferExecutor === 'function'
    });

    if (checkResult[0]?.result) {
      return; // Already loaded
    }

    // Inject the executor script
    await chrome.scripting.executeScript({
      target: { tabId },
      files: ['content/executors/buyOffer.js'] // This would be the compiled JS file
    });

    console.log('[Background] Buy offer executor injected into tab', tabId);
  } catch (error) {
    console.error('[Background] Error loading buy offer executor:', error);
    throw error;
  }
}
