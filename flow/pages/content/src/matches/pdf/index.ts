import { Log, BackgroundUtils, TabManager } from '@extension/shared';
import { MATCHER_IDS } from '@extension/types';
import { registerMatcher } from '@src/lib';
import type { Matcher, ExecutionContext, ExecutionResult } from '@extension/types';

/**
 * PDF Matcher - Detects pdf pages and triggers pdf processing
 */
class PDFMatcher implements Matcher {
  id = MATCHER_IDS.PDF;
  name = 'PDF Clicking Workflow';
  enabled = true;
  priority = 10;

  urlPatterns = ['http://localhost:8082/pdf.html', 'https://auktion.hansemerkur.de/item/id/*'];

  domPreconditions = [
    {
      selector: 'body',
      shouldExist: true,
      timeout: 5000,
    },
  ];

  async run(): Promise<void> {
    const log = new Log(MATCHER_IDS.PDF);
    log.info('PDF matcher activated');

    try {
      // Get configuration and check if enabled
      const { config, enabled } = await BackgroundUtils.getExtensionConfig();

      if (!enabled) {
        log.info('Extension disabled');
        await log.write();
        return;
      }

      await this.handlePdfExport(config, log);
    } catch (error) {
      log.error(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, { error });
      await log.write();
      console.error('[PDFMatcher] Error:', error);
    }
  }

  private async handlePdfExport(config: any, log: Log): Promise<void> {
    // Send command to process browse pdf
    try {
      await BackgroundUtils.printPdf();
      log.info('Browse pdf executor triggered successfully');
    } catch (e: any) {
      log.error(`Browse pdf executor failed: ${e?.message || String(e)}`);
    }
    await log.write();
  }
}

// Register and run the matcher when content script loads
const pdfMatcher = new PDFMatcher();

// Check if current URL matches
function checkAndRun() {
  const currentUrl = window.location.href;
  const matches = pdfMatcher.urlPatterns.some(pattern => {
    // Convert simple wildcard pattern to regex
    const regex = new RegExp(pattern.replace(/\*/g, '.*'));
    return regex.test(currentUrl);
  });

  if (matches) {
    console.log('[PDFMatcher] URL matches, registering matcher');
    registerMatcher(pdfMatcher);

    // Run the matcher after DOM is ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => pdfMatcher.run());
    } else {
      // Small delay to ensure everything is ready
      setTimeout(() => pdfMatcher.run(), 0);
    }
  }
}

// Check on initial load
checkAndRun();

/**
 * PDF Executor - Processes pdf pages by identifying and clicking valid products
 */
export async function executePDFWorkflow(context: ExecutionContext): Promise<ExecutionResult> {
  const log = new Log(context.matcherId);
  log.info(`Starting pdf workflow for tab ${context.tabId}`).setMetadata({ tabId: context.tabId, url: context.url });
  const startTime = Date.now();
  const errors: Error[] = [];
  const tabManager = TabManager.getInstance();

  try {
    // Check if this is a managed tab
    const isManagedTab = tabManager.isTabManaged(context.tabId);

    if (!isManagedTab) {
      log.warn('Tab is not managed, skipping');
      await log.write();
      return {
        success: false,
        matcherId: context.matcherId,
        executorName: 'pdf',
        error: 'Tab is not managed',
      };
    }

    await processPDF();

    // Process browse pdf (list view)
    async function processPDF(): Promise<void> {
      try {
        // print pdf
      } catch (error) {
        log.error(`Error in browse pdf processing: ${error}`);
        errors.push(error as Error);
      }
    }

    await log.write();

    return {
      success: true,
      matcherId: context.matcherId,
      executorName: 'pdf',
      data: {},
      telemetry: {
        startTime,
        endTime: Date.now(),
        errors,
      },
    };
  } catch (error) {
    log.error(`Fatal error: ${error}`, { stack: error instanceof Error ? error.stack : undefined });
    await log.write();
    console.error('[PDFExecutor] Fatal error:', error);

    return {
      success: false,
      matcherId: context.matcherId,
      executorName: 'pdf',
      error: error instanceof Error ? error.message : 'Unknown error',
      telemetry: {
        startTime,
        endTime: Date.now(),
        errors: [...errors, error as Error],
      },
    };
  }
}

// Export for background script to inject
if (typeof window !== 'undefined') {
  (window as any).__pdfExecutor = executePDFWorkflow;
}
