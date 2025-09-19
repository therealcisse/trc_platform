import { registerMatcher, sendBackgroundCommand } from '@src/lib';
import { ProductFactory, Log } from '@extension/shared';
import { isInvalidProduct } from '@extension/types';
import type {
  Matcher,
  ExecutionContext,
  ExecutionResult,
  MyOfferSelectors,
  ExecutionConfig,
  CommandResponse,
} from '@extension/types';
import { MATCHER_IDS } from '@extension/types';

/**
 * MyOffer Matcher - Detects myOffer pages and triggers myOffer processing
 */
class MyOfferMatcher implements Matcher {
  id = MATCHER_IDS.MY_OFFER;
  name = 'MyOffer Clicking Workflow';
  enabled = true;
  priority = 10;

  urlPatterns = ['https://auktion.hansemerkur.de/my_message_center_show_message.php'];

  domPreconditions = [
    {
      selector: 'body',
      shouldExist: true,
      timeout: 5000,
    },
  ];

  async run(): Promise<void> {
    const currentUrl = window.location.href;
    const id = FlowUtils.parseIDFromHref(currentUrl);
    const log = Log.withFlow(MATCHER_IDS.MY_OFFER, id);
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

      // id already extracted at the start

      await this.handleBrowseMyOffer(result.config, id, log);
    } catch (error) {
      log.error(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, { error });
      await log.write();
      console.error('[MyOfferMatcher] Error:', error);
    }
  }

  private async handleBrowseMyOffer(config: any, id: string, log: Log): Promise<void> {
    // Send command to process browse myOffer
    const response = await sendBackgroundCommand('myOffer.clickProductLink', {
      id,
      selectors: {
        itemLink: '#my_area table.message_center_message td.content a',
        titleLink: 'h1.item_title',
        requestTimestampElement: '.message_center_message thead tr td:last-child',
      },
    });

    if (response.success) {
      log.info('Browse myOffer executor triggered successfully');
    } else {
      log.error(`Browse myOffer executor failed: ${response.error}`);
    }
    await log.write();
  }

  private setupAutoRefresh(config: any): void {
    let checkCount = 0;
    const maxChecks = 4;

    const refreshInterval = setInterval(() => {
      if (config.emailMode) {
        clearInterval(refreshInterval);
        return;
      }

      checkCount++;
      if (checkCount > maxChecks) {
        console.log('[MyOfferMatcher] Max checks reached, refreshing page');
        window.location.reload();
      }
    }, 1000);
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
  flowId: string,
): Promise<ExecutionResult> {
  const log = Log.withFlow(context.matcherId, flowId);
  log
    .info(`Starting myOffer workflow for tab ${context.tabId}`)
    .setMetadata({ tabId: context.tabId, url: context.url });
  const startTime = Date.now();
  const errors: Error[] = [];
  let processedCount = 0;

  try {
    // Check if this is a managed tab
    const isManagedResponse = await sendBackgroundCommand('tab.manage', {
      action: 'isManaged',
      tabId: context.tabId,
    });

    if (!isManagedResponse.data) {
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

        const productText = titleLink.textContent ?? '';

        log.info(`Product: ${productText}`);

        const config = context.config || {};
        const product = ProductFactory.parse(config, productText);

        if (isInvalidProduct(product)) {
          log.warn(`Invalid product format: ${product.error}`);
          return;
        }

        log.debug(`Product details: ${JSON.stringify(product)}`);

        // Product is already validated by factory
        const { allowed } = { allowed: product.allowed };

        if (!allowed) {
          log.info('Product not allowed by configuration, skipping');
          return;
        }

        const href = itemLlink.href;
        log.info(`Opening myOffer: ${href}`);

        if (!context.dryRun) {
          // Open link in new managed tab
          await sendBackgroundCommand('tab.manage', {
            action: 'open',
            url: href,
          });
          log.info(`Opened myOffer link in managed tab: ${href}`);
        } else {
          log.debug('Dry run: Would open myOffer in new tab');
        }
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
        domOperations: 0,
        networkRequests: 0,
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
        domOperations: 0,
        networkRequests: 0,
        errors: [...errors, error as Error],
      },
    };
  }
}

// Export for background script to inject
if (typeof window !== 'undefined') {
  (window as any).__myOfferExecutor = executeMyOfferWorkflow;
}
