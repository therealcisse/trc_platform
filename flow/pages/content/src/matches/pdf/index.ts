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
