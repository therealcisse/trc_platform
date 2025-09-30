import { ConfigService } from '@extension/shared';
import { MATCHER_IDS } from '@extension/types';
import type { PDFCommand, CommandResponse, ExecutionContext, MessageHandler } from '@extension/types';

/**
 * pdf command handler - Manages pdf workflow execution
 */
export const pdfCommandHandler: MessageHandler<'item.printProductConfirmation'> = async (
  payload: PDFCommand,
  sender: chrome.runtime.MessageSender,
): Promise<CommandResponse> => {
  console.log('[Background] pdf command received from tab:', sender.tab?.id);

  try {
    // Validate sender tab
    if (!sender.tab?.id) {
      throw new Error('No tab ID in sender');
    }

    const tabId = sender.tab.id;

    // Get extension configuration
    const [config, enabled] = await Promise.all([ConfigService.getConfig(), ConfigService.isEnabled()]);

    if (!enabled) {
      return {
        success: false,
        error: 'Extension is disabled',
        requestId: 'PDF',
      };
    }

    // Create execution context
    const context: ExecutionContext = {
      tabId,
      url: sender.tab.url || '',
      matcherId: MATCHER_IDS.PDF,
      config,
      timeout: 30000, // 30 seconds timeout
      dryRun: false,
    };

    // Inject and execute the pdf workflow
    const result = await chrome.scripting.executeScript({
      target: { tabId },
      func: async (contextJson: string) => {
        // This runs in the content script context
        const context = JSON.parse(contextJson);

        // Check if executor is available
        if (typeof (window as any).__pdfExecutor === 'function') {
          return await (window as any).__pdfExecutor(context);
        }

        // If not, we need to load it first
        // In production, this would be injected via manifest
        return {
          success: false,
          error: 'pdf executor not loaded',
          matcherId: context.matcherId,
          executorName: 'pdf',
        };
      },
      args: [
        JSON.stringify(context),
      ],
    });

    // Extract result from script execution
    const executionResult = result[0]?.result;

    if (!executionResult) {
      throw new Error('No result from pdf executor');
    }

    // Log the execution
    if (executionResult.success) {
      console.log('[Background] pdf workflow completed successfully:', executionResult.data);
    } else {
      console.error('[Background] pdf workflow failed:', executionResult.error);
    }

    return {
      success: executionResult.success,
      data: executionResult,
      error: executionResult.error,
      requestId: 'PDF',
    };
  } catch (error) {
    console.error('[Background] Error handling pdf command:', error);

    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
      requestId: 'PDF',
    };
  }
};

// Helper function to ensure pdf executor is loaded
export async function ensureItemExecutorLoaded(tabId: number): Promise<void> {
  try {
    // Check if executor is already loaded
    const checkResult = await chrome.scripting.executeScript({
      target: { tabId },
      func: () => typeof (window as any).__pdfExecutor === 'function',
    });

    if (checkResult[0]?.result) {
      return; // Already loaded
    }

    // Inject the executor script
    await chrome.scripting.executeScript({
      target: { tabId },
      files: ['content/pdf.iife.js'], // This would be the compiled JS file
    });

    console.log('[Background] pdf executor injected into tab', tabId);
  } catch (error) {
    console.error('[Background] Error loading pdf executor:', error);
    throw error;
  }
}

