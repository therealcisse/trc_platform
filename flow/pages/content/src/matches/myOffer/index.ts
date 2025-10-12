import {
  Log,
  FlowUtils,
  ConfigService,
  BackgroundUtils,
  TabManager,
  installGlobalErrorHandlers,
} from '@extension/shared';
import { MATCHER_IDS, ExecutionConfig } from '@extension/types';
import { clickWithVerification } from '@src/lib';
import type { Matcher, ExecutionContext, ExecutionResult, MyOfferSelectors } from '@extension/types';

/**
 * MyOffer Matcher - Detects myOffer pages and triggers myOffer processing
 */
// Install global error handlers early
installGlobalErrorHandlers({ matcherId: MATCHER_IDS.MY_OFFER });

class MyOfferMatcher implements Matcher {
  id = MATCHER_IDS.MY_OFFER;
  name = 'MyOffer Clicking Workflow';
  enabled = true;
  priority = 10;

  urlPatterns = [
    'http://localhost:8082/myOffer/*',
    'https://auktion.hansemerkur.de/my_message_center_show_message.php',
  ];

  domPreconditions = [
    {
      selector: 'body',
      shouldExist: true,
      timeout: 5000,
    },
  ];

  async run(): Promise<void> {
    const log = new Log(MATCHER_IDS.MY_OFFER);
    log.info('MyOffer matcher activated');

    try {
      // Get configuration and check if enabled
      const { config, enabled } = await BackgroundUtils.getExtensionConfig();

      if (!enabled) {
        log.info('Extension disabled');
        await log.write();
        return;
      }

      await this.handleBrowseMyOffer(config, log);
    } catch (error) {
      log.error(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, { error });
      await log.write();
      console.error('[MyOfferMatcher] Error:', error);
    }
  }

  private async handleBrowseMyOffer(config: ExecutionConfig, log: Log): Promise<void> {
    // Send command to process browse myOffer
    try {
      const context: ExecutionContext = {
        matcherId: MATCHER_IDS.MY_OFFER,
        url: window.location.href,
        config,
        dryRun: false,
      };
      const result = await executeMyOfferWorkflow(context, {
        itemLink: '.message_center_message tbody tr:first-child td.content p:nth-child(2) a',
        titleLink: '.message_center_message thead tr:nth-child(2) td:nth-child(2)',
        pdfLink: '.message_center_message td a[href*="/item/id/"]',
      });
      log.info(`Browse myOffer executor completed: ${result.success ? 'success' : 'failure'}`);
    } catch (e: any) {
      log.error(`Browse myOffer executor failed: ${e?.message || String(e)}`);
    }
    await log.write();
  }
}

// Register and run the matcher when content script loads
const myOfferMatcher = new MyOfferMatcher();

// Check if current URL matches
function checkAndRun() {
  const currentUrl = window.location.href;
  const matches = myOfferMatcher.urlPatterns.some(pattern => {
    // Convert simple wildcard pattern to regex
    const regex = new RegExp(pattern.replace(/\*/g, '.*'));
    return regex.test(currentUrl);
  });

  if (matches) {
    console.log('[MyOfferMatcher] URL matches, registering matcher');

    // Run the matcher after DOM is ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => myOfferMatcher.run());
    } else {
      // Small delay to ensure everything is ready
      setTimeout(() => myOfferMatcher.run(), 0);
    }
  }
}

// Check on initial load
checkAndRun();

/**
 * MyOffer Executor - Processes myOffer pages by identifying and clicking valid products
 */
export async function executeMyOfferWorkflow(
  context: ExecutionContext,
  selectors: MyOfferSelectors,
): Promise<ExecutionResult> {
  const log = new Log(context.matcherId);
  log.info(`Starting myOffer workflow`).setMetadata({ url: context.url });
  const startTime = Date.now();
  const errors: Error[] = [];
  const tabManager = TabManager.getInstance();

  try {
    await processMyOffer();

    // Process browse myOffer (list view)
    async function processMyOffer(): Promise<void> {
      try {
        const titleLink = document.querySelector(selectors.titleLink) as HTMLElement;

        if (!titleLink) {
          log.info('No title found, skipping');
          return;
        }

        const title = titleLink.textContent ?? '';

        log.info(`Product: ${title}`);

        const isLead = FlowUtils.isLead(title);
        const id = isLead ? `${FlowUtils.parseIDFromTitle(title)}-pdf` : FlowUtils.parseIDFromTitle(title);

        const flow = await ConfigService.getFlow(id);

        const flowLog = Log.withFlow(context.matcherId, id);

        if (!flow) {
          flowLog.info('❌ Flow not found');
          return;
        }

        if (flow.status === 'done' || flow.status === 'failed') {
          flowLog.info('❌ Flow is already done, closing all tabs');
          await tabManager.closeAllTabs(flow.id);
        }

        let href: string;
        let link: HTMLAnchorElement;
        if (isLead) {
          const pdf = document.querySelector(selectors.pdfLink) as HTMLAnchorElement;

          if (!pdf) {
            log.info('No pdf button found, skipping');
            return;
          }

          link = pdf;
          href = pdf.href;
        } else {
          const itemLink = document.querySelector(selectors.itemLink) as HTMLAnchorElement;
          if (!itemLink) {
            log.info('No item link found, skipping');
            return;
          }

          link = itemLink;
          href = itemLink.href;
        }

        log.info(`Opening myOffer: ${href}`);

        if (!context.dryRun) {
          flowLog.info(`Opening myOffer link: ${href}`);
          log.info(`Opened myOffer link in managed tab: ${href}`);

          await clickWithVerification(link, {
            verify: false,
            scroll: false,
          });
        } else {
          log.debug('Dry run: Would open myOffer in new tab');
        }

        flowLog.info(`Processed myOffer`);
      } catch (error) {
        log.error(`Error in browse myOffer processing: ${error}`);
        errors.push(error as Error);
      }
    }

    await log.write();

    return {
      success: true,
      matcherId: context.matcherId,
      executorName: 'myOffer',
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
    console.error('[MyOfferExecutor] Fatal error:', error);

    return {
      success: false,
      matcherId: context.matcherId,
      executorName: 'myOffer',
      error: error instanceof Error ? error.message : 'Unknown error',
      telemetry: {
        startTime,
        endTime: Date.now(),
        errors: [...errors, error as Error],
      },
    };
  }
}
