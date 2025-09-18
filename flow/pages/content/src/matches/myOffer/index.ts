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
  MyOfferSelectors,
  ExecutionConfig,
  CommandResponse,
} from '@extension/types';

import { ConfigService } from '@extension/shared';

/**
 * MyOffer Matcher - Detects myOffer pages and triggers myOffer processing
 */
class MyOfferMatcher implements Matcher {
  id = 'myOffer-matcher';
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
    const log = new Log('myOffer-matcher');
    log.push('MyOffer matcher activated');

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

      await this.handleBrowseMyOffer(result.config, id, log);
    } catch (error) {
      log.push(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`).write();
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
      },
    });

    if (response.success) {
      log.push('Browse myOffer executor triggered successfully').write();
    } else {
      log.push(`Browse myOffer executor failed: ${response.error}`).write();
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
): Promise<ExecutionResult> {
  const log = new Log('myOffer-executor');
  const startTime = Date.now();
  const errors: Error[] = [];
  let processedCount = 0;

  try {
    log.push(`Starting myOffer workflow for tab ${context.tabId}`);

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
        executorName: 'myOffer',
        error: 'Tab is not managed',
      };
    }

    const currentUrl = window.location.href;
    const id = FlowUtils.parseIDFromHref(currentUrl);
    const flow = await ConfigService.getFlow(id);

    if (!flow) {
      console.log('Flow not found');
    } else {
      await processMyOffer();
    }

    // Process browse myOffer (list view)
    async function processMyOffer(): Promise<void> {
      try {
        const itemLlink = document.querySelector(selectors.itemLink) as HTMLAnchorElement;
        const titleLink = document.querySelector(selectors.titleLink) as HTMLElement;

        if (!itemLlink) {
          log.push('No item link found, skipping');
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

        // Open the myOffer
        log.push(`Opening myOffer: ${itemLlink.href}`);

        if (!context.dryRun) {
          let id: string;
          const href = itemLlink.href;

          try {
            // Parse ID from path as per requirement
            id = FlowUtils.parseIDFromPath(href);
          } catch (e) {
            const errorMsg = `[Flow] Failed to parse ID from ${href}: ${e}`;
            log.push(errorMsg);
            await sendBackgroundCommand('extension.log', { text: errorMsg });
          }

          let requestTimestamp: number = Date.now() / 1000;

          // Start flow and check if it already exists
          const startFlowResult = await sendBackgroundCommand('extension.startFlow', {
            type: 'inbox',
            id: id,
            title: productText,
            requestTimestamp: requestTimestamp,
            href,
          });

          if (startFlowResult.success && startFlowResult.data === true) {
            // Flow already exists, skip this link
            const skipMsg = `[Flow] Skipping email with existing flow: ${id}`;
            log.push(skipMsg);
            await sendBackgroundCommand('extension.log', { text: skipMsg });
          }
        } else {
          log.push('Dry run: Would open myOffer in new tab');
        }
      } catch (error) {
        log.push(`Error in browse myOffer processing: ${error}`);
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
    log.push(`Fatal error: ${error}`).write();
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
