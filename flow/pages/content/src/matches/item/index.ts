import { ProductFactory, FlowUtils, ConfigService, Log, BackgroundUtils, TabManager } from '@extension/shared';
import { isInvalidProduct, MATCHER_IDS } from '@extension/types';
import { registerMatcher, isValidTimeOfDay, waitForSelector, clickWithVerification, sleep } from '@src/lib';
import type { Matcher, ExecutionContext, ExecutionResult, ItemSelectors, Flow } from '@extension/types';

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
    log.info('Item matcher activated');

    try {
      // Get configuration and check if enabled
      const { config, enabled } = await BackgroundUtils.getExtensionConfig();

      if (!enabled) {
        log.info('Extension disabled');
        await log.write();
        return;
      }

      await this.handleBrowseItem(config, id, log);
    } catch (error) {
      log.error(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, { error });
      await log.write();
      console.error('[ItemMatcher] Error:', error);
    }
  }

  private async handleBrowseItem(config: any, id: string, log: Log): Promise<void> {
    // Send command to process browse item
    try {
      await BackgroundUtils.clickItemBuyButton({
        id,
        selectors: {
          buyButton: '.buy_now a.btn',
        },
      });
      log.info('Browse item executor triggered successfully');
    } catch (e: any) {
      log.error(`Browse item executor failed: ${e?.message || String(e)}`);
    }
    await log.write();
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
        executorName: 'item',
        error: 'Tab is not managed',
      };
    }

    if (flow.status === 'done' || flow.status === 'failed') {
      log.info('❌ Flow is already completed, closing all tabs');
      await tabManager.closeAllTabs(flow.id);
    }

    await processItem();

    // Process browse item (list view)
    async function processItem(): Promise<void> {
      try {
        const buyButton = document.querySelector(selectors.buyButton) as HTMLAnchorElement;

        if (!buyButton) {
          log.info('No buy button found, skipping');
          return;
        }

        const href = buyButton.href;

        // Open the item
        log.info(`Opening item: ${href}`);

        if (!context.dryRun) {
          tabManager.openTab(href, flow.id);
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
        errors: [...errors, error as Error],
      },
    };
  }
}

// Export for background script to inject
if (typeof window !== 'undefined') {
  (window as any).__itemExecutor = executeItemWorkflow;
}
