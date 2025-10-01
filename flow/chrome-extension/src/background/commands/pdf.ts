import { ConfigService, sleep, TabManager } from '@extension/shared';
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

    await exportTabToPdf(tabId);

    await sleep(5000);

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
      func: async (contextJson: string, selectorsJson: string) => {
        // This runs in the content script context
        const context = JSON.parse(contextJson);
        const selectors = JSON.parse(selectorsJson);

        // Check if executor is available
        if (typeof (window as any).__pdfExecutor === 'function') {
          return await (window as any).__pdfExecutor(context, selectors);
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
        JSON.stringify(payload.selectors),
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
      requestId: "PDF",
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
export async function ensurePdfExecutorLoaded(tabId: number): Promise<void> {
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

// Requires "downloads", "debugger", and "tabs" permissions in manifest.json
// Also ensure host_permissions for the pages you will print.

export async function exportTabToPdf(tabId: number, filenameBase?: string): Promise<number | undefined> {
  const target = { tabId };
  const CDP_VERSION = "1.3"; // DevTools Protocol version

  // Sanitizes a string for use as a filename on Windows/macOS/Linux
  const sanitize = (s: string) => s.replace(/[\\/:*?"<>|]/g, "").trim();

  try {
    // Attach to the tab and enable Page domain
    await chrome.debugger.attach(target, CDP_VERSION); // bridge to CDP
    await chrome.debugger.sendCommand(target, "Page.enable");

    // Ask CDP to render as PDF, returns Base64 string
    const { data } = await chrome.debugger.sendCommand(target, "Page.printToPDF", {
      printBackground: true,
      displayHeaderFooter: false,
      preferCSSPageSize: true
      // add options as needed: landscape, paperWidth, paperHeight, margins, scale
    });

    // Build a filename
    const tab = await chrome.tabs.get(tabId);
    const base = filenameBase ?? tab.title ?? "page";
    const ymd = new Date().toISOString().slice(0, 10);
    const filename = `PDFExports/${sanitize(base)}-${ymd}.pdf`;

    // MV3 service workers cannot use URL.createObjectURL, so use a data URL
    const downloadId = await chrome.downloads.download({
      url: `data:application/pdf;base64,${data}`,
      filename,     // you can include subfolders like "MyApp/${filename}"
      saveAs: false // honors the user's "Ask where to save" setting
    });

    return downloadId;
  } catch (err) {
    console.error("exportTabToPdf failed:", err);
    return undefined;
  } finally {
    try { await chrome.debugger.detach(target); } catch {}
  }
}

