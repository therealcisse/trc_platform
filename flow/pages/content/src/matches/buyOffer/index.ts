import {
  registerMatcher,
  waitForSelector,
  clickWithVerification,
  sendBackgroundCommand,
  Log,
  sleep,
  Product,
} from '@src/lib';
import type { Matcher } from '@extension/types';
import type { ExecutionContext, ExecutionResult, BuyOfferSelectors } from '@extension/types';

/**
 * Buy Offer Matcher - Detects and triggers purchase workflow for valid products
 */
class BuyOfferMatcher implements Matcher {
  id = 'buy-offer-matcher';
  name = 'Buy Offer Workflow';
  enabled = true;
  priority = 20; // Higher priority than email/offers

  urlPatterns = ['https://auktion.hansemerkur.de/buy_now/id/*'];

  domPreconditions = [
    {
      selector: '#page_buy_now h2',
      shouldExist: true,
      timeout: 5000,
    },
    {
      selector: '#buyFormBtn',
      shouldExist: true,
      timeout: 5000,
    },
  ];

  async run(): Promise<void> {
    const log = new Log('buy-offer-matcher');
    log.push('Buy offer matcher activated');

    try {
      // Check if extension is enabled
      const enabledResponse = await sendBackgroundCommand('extension.isEnabled', {});
      if (!enabledResponse.success || !enabledResponse.data) {
        log.push('Extension disabled').write();
        return;
      }

      // Get configuration
      const configResponse = await sendBackgroundCommand('extension.getConfig', {});
      const config = configResponse.data;
      if (!config) {
        log.push('No configuration found').write();
        return;
      }

      // Get product title
      const titleElement = document.querySelector('#page_buy_now h2');
      if (!titleElement) {
        log.push('Product title not found').write();
        return;
      }

      const productText = titleElement.textContent || '';
      log.push(`Found product: ${productText}`);

      // Parse and validate product
      const product = new Product(productText);
      if (!product.valid) {
        log.push('Invalid product format, ignoring').write();
        return;
      }

      log.push(`Product details: ${product.toString()}`);

      // Check if this product is already being purchased
      const buyingStateResponse = await sendBackgroundCommand('state.buying', {
        action: 'check',
        key: product.text,
      });

      if (buyingStateResponse.data?.buying) {
        log.push(`Already buying this product (ID: ${buyingStateResponse.data.id})`).write();

        // Close duplicate tab
        await sendBackgroundCommand('tab.manage', {
          action: 'close',
          tabId: window.tabId,
        });

        return;
      }

      // Validate product against configuration
      const { allowed, delay } = product.isAllowed(config);
      if (!allowed) {
        log.push('Product not allowed by configuration').write();
        return;
      }

      // Generate random ID for this purchase attempt
      const randomId = Math.random().toString(36).substring(7);

      // Calculate timeout (delay + extra headroom)
      const delaySeconds = delay || 0;
      const extraHeadroomSeconds = 30;
      const timeout = Date.now() + (delaySeconds + extraHeadroomSeconds) * 1000;

      // Mark product as being purchased
      await sendBackgroundCommand('state.buying', {
        action: 'mark',
        key: product.text,
        id: randomId,
        timeout,
      });

      log.push(`Starting purchase process (ID: ${randomId}, delay: ${delaySeconds}s)`);

      // Send command to execute purchase
      const response = await sendBackgroundCommand('buyOffer.execute', {
        productId: randomId,
        delay: delaySeconds,
        selectors: {
          productTitle: 'h1.item_title',
          buyFormButton: 'div.buy_now a[role="button"]',
        },
      });

      if (response.success) {
        log.push('Buy offer executor triggered successfully').write();
      } else {
        log.push(`Buy offer executor failed: ${response.error}`).write();

        // Clear buying state on failure
        await sendBackgroundCommand('state.buying', {
          action: 'clear',
          key: product.text,
        });
      }
    } catch (error) {
      log.push(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`).write();
      console.error('[BuyOfferMatcher] Error:', error);
    }
  }
}

// Register and run the matcher when content script loads
const buyOfferMatcher = new BuyOfferMatcher();

// Check if current URL matches
function checkAndRun() {
  const currentUrl = window.location.href;
  const matches = buyOfferMatcher.urlPatterns.some(pattern => {
    // Convert simple wildcard pattern to regex
    const regex = new RegExp(pattern.replace(/\*/g, '.*'));
    return regex.test(currentUrl);
  });

  if (matches) {
    console.log('[BuyOfferMatcher] URL matches, registering matcher');
    registerMatcher(buyOfferMatcher);

    // Run the matcher after DOM is ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => buyOfferMatcher.run());
    } else {
      // Small delay to ensure everything is ready
      setTimeout(() => buyOfferMatcher.run(), 1000);
    }
  }
}

// Check on initial load
checkAndRun();

export default buyOfferMatcher;

/**
 * Buy Offer Executor - Executes purchase workflow after validation and delay
 */
export async function executeBuyOfferWorkflow(
  context: ExecutionContext,
  selectors: BuyOfferSelectors,
): Promise<ExecutionResult> {
  const log = new Log('buy-offer-executor');
  const startTime = Date.now();
  const errors: Error[] = [];

  try {
    log.push(`Starting buy offer workflow for tab ${context.tabId}`);

    // Get product title for validation
    const titleElement = await waitForSelector(selectors.productTitle, {
      timeout: 5000,
      visible: true,
    });

    const productText = titleElement.textContent || '';
    const product = new Product(productText);

    if (!product.valid) {
      throw new Error('Invalid product format');
    }

    log.push(`Product details: ${product.toString()}`);

    // Get buy button
    const buyButton = await waitForSelector(selectors.buyFormButton, {
      timeout: 5000,
      visible: true,
    });

    if (!buyButton) {
      throw new Error('Buy button not found');
    }

    // Check buying state again (prevent race conditions)
    const buyingStateResponse = await sendBackgroundCommand('state.buying', {
      action: 'check',
      key: product.text,
    });

    // Handle if another tab started buying this product
    if (buyingStateResponse.data?.buying && buyingStateResponse.data.id !== context.productId) {
      log.push(`Another tab is buying this product (ID: ${buyingStateResponse.data.id})`);

      // Close this tab
      await sendBackgroundCommand('tab.manage', {
        action: 'close',
        tabId: context.tabId,
      });

      return {
        success: false,
        matcherId: context.matcherId,
        executorName: 'buyOffer',
        error: 'Duplicate purchase attempt',
      };
    }

    // Check configuration again
    const config = context.config || {};
    const { allowed } = product.isAllowed(config);

    if (!allowed) {
      throw new Error('Product not allowed by configuration');
    }

    // Apply delay if specified
    const delay = context.delay || 0;
    if (delay > 0) {
      log.push(`Waiting ${delay} seconds before purchase`);
      await sleep(delay * 1000);
    }

    // Execute purchase
    log.push('Executing purchase');

    if (!context.dryRun) {
      await clickWithVerification(buyButton, {
        delay: 200,
        verify: true,
        scroll: true,
      });

      // Wait for form submission
      await sleep(500);
    } else {
      log.push('Dry run: Would click buy button');
    }

    await log.write();

    return {
      success: true,
      matcherId: context.matcherId,
      executorName: 'buyOffer',
      data: {
        productId: context.productId,
        product: product.toString(),
        appliedDelay: delay,
      },
      telemetry: {
        startTime,
        endTime: Date.now(),
        domOperations: 2, // Title check and buy click
        networkRequests: 2, // State check and buy submit
        errors,
      },
    };
  } catch (error) {
    log.push(`Fatal error: ${error}`).write();
    console.error('[BuyOfferExecutor] Fatal error:', error);

    // Clear buying state on failure
    try {
      const titleElement = document.querySelector(selectors.productTitle);
      if (titleElement) {
        const product = new Product(titleElement.textContent || '');
        if (product.valid) {
          await sendBackgroundCommand('state.buying', {
            action: 'clear',
            key: product.text,
          });
        }
      }
    } catch (cleanupError) {
      console.error('[BuyOfferExecutor] Error clearing buying state:', cleanupError);
    }

    return {
      success: false,
      matcherId: context.matcherId,
      executorName: 'buyOffer',
      error: error instanceof Error ? error.message : 'Unknown error',
      telemetry: {
        startTime,
        endTime: Date.now(),
        domOperations: 1,
        networkRequests: 1,
        errors: [...errors, error as Error],
      },
    };
  }
}

// Export for background script to inject
if (typeof window !== 'undefined') {
  (window as any).__buyOfferExecutor = executeBuyOfferWorkflow;
}
