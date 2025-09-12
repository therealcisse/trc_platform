import type {
  OffersCommand,
  CommandResponse,
  ExecutionContext
} from '@extension/types';
import type { MessageHandler } from '../types';
import { ConfigService } from '@extension/shared';

/**
 * Offers command handler - Manages offers workflow execution
 */
export const offersCommandHandler: MessageHandler<'offers.clickProductLink'> = async (
  payload: OffersCommand,
  sender: chrome.runtime.MessageSender
): Promise<CommandResponse> => {
  console.log('[Background] Offers command received from tab:', sender.tab?.id);

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
        requestId: `offers-${Date.now()}`
      };
    }

    // Create execution context
    const context: ExecutionContext = {
      tabId,
      url: sender.tab.url || '',
      matcherId: 'offers-matcher',
      config,
      timeout: 30000, // 30 seconds timeout
      dryRun: false
    };

    // First ensure product strategies are loaded
    const strategies = await chrome.storage.local.get(['productStrategies']);
    const productStrategies = strategies.productStrategies || [];

    // Inject and execute the offers workflow
    const result = await chrome.scripting.executeScript({
      target: { tabId },
      func: async (contextJson: string, selectorsJson: string, strategiesJson: string) => {
        // This runs in the content script context
        const context = JSON.parse(contextJson);
        const selectors = JSON.parse(selectorsJson);
        const strategies = JSON.parse(strategiesJson);

        // Check if executor is available
        if (typeof (window as any).__offersExecutor === 'function') {
          // Add strategies to context
          context.productStrategies = strategies;
          return await (window as any).__offersExecutor(context, selectors);
        }

        // If not, we need to load it first
        // In production, this would be injected via manifest
        return {
          success: false,
          error: 'Offers executor not loaded',
          matcherId: context.matcherId,
          executorName: 'offers'
        };
      },
      args: [
        JSON.stringify(context),
        JSON.stringify(payload.selectors || {
          offerMarkers: '.leaflet-marker-pane img[src="templates/design_version2_01/images/marker/marker-02.png"]',
          offerPopup: '.leaflet-popup-content a',
          browseList: 'div.browse_list .row',
          buyButton: '.buy_now a.btn',
          titleLink: '.title a'
        }),
        JSON.stringify(productStrategies)
      ]
    });

    // Extract result from script execution
    const executionResult = result[0]?.result;

    if (!executionResult) {
      throw new Error('No result from offers executor');
    }

    // Log the execution
    if (executionResult.success) {
      console.log('[Background] Offers workflow completed successfully:', executionResult.data);
    } else {
      console.error('[Background] Offers workflow failed:', executionResult.error);
    }

    return {
      success: executionResult.success,
      data: executionResult,
      error: executionResult.error,
      requestId: `offers-${Date.now()}`
    };

  } catch (error) {
    console.error('[Background] Error handling offers command:', error);

    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
      requestId: `offers-${Date.now()}`
    };
  }
};

// Helper function to ensure offers executor is loaded
export async function ensureOffersExecutorLoaded(tabId: number): Promise<void> {
  try {
    // Check if executor is already loaded
    const checkResult = await chrome.scripting.executeScript({
      target: { tabId },
      func: () => typeof (window as any).__offersExecutor === 'function'
    });

    if (checkResult[0]?.result) {
      return; // Already loaded
    }

    // Inject the executor script
    await chrome.scripting.executeScript({
      target: { tabId },
      files: ['content/executors/offers.js'] // This would be the compiled JS file
    });

    console.log('[Background] Offers executor injected into tab', tabId);
  } catch (error) {
    console.error('[Background] Error loading offers executor:', error);
    throw error;
  }
}
