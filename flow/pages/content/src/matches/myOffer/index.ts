import { ProductFactory, Log, FlowUtils, ConfigService } from '@extension/shared';
import { isInvalidProduct, MATCHER_IDS } from '@extension/types';
import { registerMatcher } from '@src/lib';
import { sendBackgroundCommand, TabManager } from '@extension/shared';
import type {
  Matcher,
  ExecutionContext,
  ExecutionResult,
  MyOfferSelectors,
  ExecutionConfig,
  CommandResponse,
} from '@extension/types';

/**
 * MyOffer Matcher - Detects myOffer pages and triggers myOffer processing
 */
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
      const configResponse = (await sendBackgroundCommand('extension.getConfig', {})) as CommandResponse<{
        config: ExecutionConfig;
        enabled: boolean;
      }>;
      const result = configResponse.data;
      if (!result) {
        log.warn('No configuration found');
        await log.write();
        return;
      }

      if (!result.enabled) {
        log.info('Extension disabled');
        await log.write();
        return;
      }

      await this.handleBrowseMyOffer(result.config, log);
    } catch (error) {
      log.error(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, { error });
      await log.write();
      console.error('[MyOfferMatcher] Error:', error);
    }
  }

  private async handleBrowseMyOffer(config: any, log: Log): Promise<void> {
    // Send command to process browse myOffer
    const response = await sendBackgroundCommand('myOffer.clickProductLink', {
      selectors: {
        itemLink: '.message_center_message tbody tr:first-child td.content p:nth-child(2) a',
        titleLink: 'h3.panel-title',
      },
    });

    if (response.success) {
      log.info('Browse myOffer executor triggered successfully');
    } else {
      log.error(`Browse myOffer executor failed: ${response.error}`);
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
    registerMatcher(myOfferMatcher);

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
  log
    .info(`Starting myOffer workflow for tab ${context.tabId}`)
    .setMetadata({ tabId: context.tabId, url: context.url });
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
        executorName: 'myOffer',
        error: 'Tab is not managed',
      };
    }

    await processMyOffer();

    // Process browse myOffer (list view)
    async function processMyOffer(): Promise<void> {
      try {
        const itemLlink = document.querySelector(selectors.itemLink) as HTMLAnchorElement;
        const titleLink = document.querySelector(selectors.titleLink) as HTMLElement;

        if (!itemLlink) {
          log.info('No item link found, skipping');
          return;
        }

        if (!titleLink) {
          log.info('No title found, skipping');
          return;
        }

        const title = titleLink.textContent ?? '';

        log.info(`Product: ${title}`);

        const href = itemLlink.href;
        log.info(`Opening myOffer: ${href}`);

        const id = FlowUtils.parseIDFromTitle(title);
        const flowLog = Log.withFlow(context.matcherId, id);

        const flow = await ConfigService.getFlow(id);
        if (flow && flow.status === 'done') {
          flowLog.info('❌ Flow is already done, closing all tabs');
          await tabManager.closeAllTabs(flow.id);
        }

        if (!context.dryRun) {
          // Open link in new managed tab
          tabManager.openTab(href, id);
          flowLog.info(`Opening myOffer link: ${href}`);
          log.info(`Opened myOffer link in managed tab: ${href}`);
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

// Export for background script to inject
if (typeof window !== 'undefined') {
  (window as any).__myOfferExecutor = executeMyOfferWorkflow;
}
