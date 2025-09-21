import { ProductFactory, FlowUtils, ConfigService, Log } from '@extension/shared';
import { isInvalidProduct, MATCHER_IDS } from '@extension/types';
import {
  registerMatcher,
  sendBackgroundCommand,
  isValidTimeOfDay,
  waitForSelector,
  clickWithVerification,
  sleep,
} from '@src/lib';
import type {
  Matcher,
  ExecutionContext,
  ExecutionResult,
  ItemSelectors,
  ExecutionConfig,
  CommandResponse,
  Flow,
} from '@extension/types';

/**
 * Item Matcher - Detects item pages and triggers item processing
 */
class ItemMatcher implements Matcher {
  id = MATCHER_IDS.ITEM;
  name = 'Item Clicking Workflow';
  enabled = true;
  priority = 10;

  urlPatterns = ['http://localhost:8082/item/*', 'https://auktion.hansemerkur.de/item.php'];

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
    const log = Log.withFlow(MATCHER_IDS.ITEM, id);
    console.log(`Id : ${id}`);
    log.info('Item matcher activated');

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

      await this.handleBrowseItem(result.config, id, log);
    } catch (error) {
      log.error(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, { error });
      await log.write();
      console.error('[ItemMatcher] Error:', error);
    }
  }

  private async handleBrowseItem(config: any, id: string, log: Log): Promise<void> {
    // Send command to process browse item
    const response = await sendBackgroundCommand('item.clickProductLink', {
      id,
      selectors: {
        buyButton: '.buy_now a.btn',
        titleLink: 'h1.item_title',
      },
    });

    if (response.success) {
      log.info('Browse item executor triggered successfully');
    } else {
      log.error(`Browse item executor failed: ${response.error}`);
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
        console.log('[ItemMatcher] Max checks reached, refreshing page');
        window.location.reload();
      }
    }, 1000);
  }
}

// Register and run the matcher when content script loads
const itemMatcher = new ItemMatcher();

// Check if current URL matches
function checkAndRun() {
  const currentUrl = window.location.href;
  const matches = itemMatcher.urlPatterns.some(pattern => {
    // Convert simple wildcard pattern to regex
    const regex = new RegExp(pattern.replace(/\*/g, '.*'));
    return regex.test(currentUrl);
  });

  if (matches) {
    console.log('[ItemMatcher] URL matches, registering matcher');
    registerMatcher(itemMatcher);

    // Run the matcher after DOM is ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => itemMatcher.run());
    } else {
      // Small delay to ensure everything is ready
      setTimeout(() => itemMatcher.run(), 0);
    }
  }
}

// Check on initial load
checkAndRun();

/**
 * Item Executor - Processes item pages by identifying and clicking valid products
 */
export async function executeItemWorkflow(
  context: ExecutionContext,
  selectors: ItemSelectors,
  flow: Flow,
): Promise<ExecutionResult> {
  const log = Log.withFlow(context.matcherId, flow.id);
  log.info(`Starting item workflow for tab ${context.tabId}`).setMetadata({ tabId: context.tabId, url: context.url });
  const startTime = Date.now();
  const errors: Error[] = [];

  try {
    // Check if we're in operation hours
    if (!isValidTimeOfDay(context.config)) {
      log.warn('Outside operation hours, scheduling reload at next minute mark');

      // Calculate time until next minute
      const now = new Date();
      const nextMinute = new Date(now);
      nextMinute.setMinutes(now.getMinutes() + 1);
      nextMinute.setSeconds(0);
      nextMinute.setMilliseconds(0);

      const delay = nextMinute.getTime() - now.getTime();

      // Schedule reload at exact minute mark
      setTimeout(() => {
        window.location.reload();
      }, delay + 100);

      await log.write();
      return {
        success: false,
        matcherId: context.matcherId,
        executorName: 'item',
        error: 'Outside operation hours, scheduled reload',
        telemetry: {
          startTime,
          endTime: Date.now(),
          domOperations: 0,
          networkRequests: 0,
          errors,
        },
      };
    }

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
        executorName: 'item',
        error: 'Tab is not managed',
      };
    }

    await processItem();

    // Process browse item (list view)
    async function processItem(): Promise<void> {
      try {
        const buyButton = document.querySelector(selectors.buyButton) as HTMLAnchorElement;
        const titleLink = document.querySelector(selectors.titleLink) as HTMLElement;

        if (!buyButton) {
          log.info('No buy button found, skipping');
          return;
        }

        if (!titleLink) {
          log.info('No title found, skipping');
          return;
        }

        // const title = titleLink.textContent ?? '';

        // log.info(`Product: ${title}`);
        //
        // const config = context.config || {};
        // const product = ProductFactory.parse(config, title);
        //
        // if (isInvalidProduct(product)) {
        //   log.warn(`Invalid product format: ${product.error}`);
        //   return;
        // }
        //
        // log.debug(`Product details: ${JSON.stringify(product)}`);
        //
        // // Product is already validated by factory
        // const { allowed } = { allowed: product.allowed };
        //
        // if (!allowed) {
        //   log.info('Product not allowed by configuration, skipping');
        //   return;
        // }

        // Open the item
        log.info(`Opening item: ${buyButton.href}`);

        if (!context.dryRun) {
          await sendBackgroundCommand('tab.manage', {
            action: 'open',
            url: buyButton.href,
          });
        } else {
          log.debug('Dry run: Would open item in new tab');
        }
      } catch (error) {
        log.error(`Error in browse item processing: ${error}`);
        errors.push(error as Error);
      }
    }

    await log.write();

    return {
      success: true,
      matcherId: context.matcherId,
      executorName: 'item',
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
    console.error('[ItemExecutor] Fatal error:', error);

    return {
      success: false,
      matcherId: context.matcherId,
      executorName: 'item',
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
  (window as any).__itemExecutor = executeItemWorkflow;
}
