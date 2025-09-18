import {
  registerMatcher,
  sendBackgroundCommand,
  Log,
  isValidTimeOfDay,
  assertValidTimeOfDay,
  waitForSelector,
  clickWithVerification,
  sleep,
} from '@src/lib';
import { ProductFactory, FlowUtils } from '@extension/shared';
import { isInvalidProduct } from '@extension/types';
import type {
  Matcher,
  ExecutionContext,
  ExecutionResult,
  ItemSelectors,
  ExecutionConfig,
  CommandResponse,
} from '@extension/types';

import { ConfigService } from '@extension/shared';

/**
 * Item Matcher - Detects item pages and triggers item processing
 */
class ItemMatcher implements Matcher {
  id = 'item-matcher';
  name = 'Item Clicking Workflow';
  enabled = true;
  priority = 10;

  urlPatterns = ['https://auktion.hansemerkur.de/item.php'];

  domPreconditions = [
    {
      selector: 'body',
      shouldExist: true,
      timeout: 5000,
    },
  ];

  async run(): Promise<void> {
    const log = new Log('item-matcher');
    log.push('Item matcher activated');

    try {
      // Get configuration and check if enabled
      const configResponse = (await sendBackgroundCommand('extension.getConfig', {})) as CommandResponse<{
        config: ExecutionConfig;
        enabled: boolean;
      }>;
      const result = configResponse.data;
      if (!result) {
        log.push('No configuration found').write();
        return;
      }

      if (!result.enabled) {
        log.push('Extension disabled').write();
        return;
      }

      const currentUrl = window.location.href;
      const id = FlowUtils.parseIDFromHref(currentUrl);

      await this.handleBrowseItem(result.config, id, log);
    } catch (error) {
      log.push(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`).write();
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
      log.push('Browse item executor triggered successfully').write();
    } else {
      log.push(`Browse item executor failed: ${response.error}`).write();
    }
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
): Promise<ExecutionResult> {
  const log = new Log('item-executor');
  const startTime = Date.now();
  const errors: Error[] = [];

  try {
    log.push(`Starting item workflow for tab ${context.tabId}`);

    // Check if this is a managed tab
    const isManagedResponse = await sendBackgroundCommand('tab.manage', {
      action: 'isManaged',
      tabId: context.tabId,
    });

    if (!isManagedResponse.data) {
      log.push('Tab is not managed, skipping').write();
      return {
        success: false,
        matcherId: context.matcherId,
        executorName: 'item',
        error: 'Tab is not managed',
      };
    }

    const currentUrl = window.location.href;
    const id = FlowUtils.parseIDFromHref(currentUrl);
    const flow = await ConfigService.getFlow(id);

    if (!flow) {
      console.log('Flow not found');
    } else {
      await processItem();
    }

    // Process browse item (list view)
    async function processItem(): Promise<void> {
      try {
        const buyButton = document.querySelector(selectors.buyButton) as HTMLAnchorElement;
        const titleLink = document.querySelector(selectors.titleLink) as HTMLElement;

        if (!buyButton) {
          log.push('No buy button found, skipping');
          return;
        }

        if (!titleLink) {
          log.push('No title found, skipping');
          return;
        }

        const productText = titleLink.textContent ?? '';

        log.push(`Product: ${productText}`);

        const config = context.config || {};
        const product = ProductFactory.parse(config, productText);

        if (isInvalidProduct(product)) {
          log.push(`Invalid product format: ${product.error}`);
          return;
        }

        log.push(`Product details: ${JSON.stringify(product)}`);

        // Product is already validated by factory
        const { allowed } = { allowed: product.allowed };

        if (!allowed) {
          log.push('Product not allowed by configuration, skipping');
          return;
        }

        // Open the item
        log.push(`Opening item: ${buyButton.href}`);

        if (!context.dryRun) {
          await sendBackgroundCommand('tab.manage', {
            action: 'open',
            url: buyButton.href,
          });
        } else {
          log.push('Dry run: Would open item in new tab');
        }
      } catch (error) {
        log.push(`Error in browse item processing: ${error}`);
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
    log.push(`Fatal error: ${error}`).write();
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
