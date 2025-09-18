import {
  registerMatcher,
  waitForSelector,
  clickWithVerification,
  sendBackgroundCommand,
  Log,
  sleep,
  fetchImageAsBlob,
  extractNumericAnswer,
} from '@src/lib';
import { FlowUtils, ProductFactory, ConfigService } from '@extension/shared';
import { isInvalidProduct } from '@extension/types';
import { type CommandResponse, type ExecutionConfig, type Matcher } from '@extension/types';
import { MATCHER_IDS } from '@extension/types';
import type { ExecutionContext, ExecutionResult, BuyOfferSelectors, Flow } from '@extension/types';

/**
 * Buy Offer Matcher - Detects and triggers purchase workflow for valid products
 */
class BuyOfferMatcher implements Matcher {
  id = MATCHER_IDS.BUY_OFFER;
  name = 'Buy Offer Workflow';
  enabled = true;
  priority = 20; // Higher priority than email/offers

  urlPatterns = ['https://auktion.hansemerkur.de/buy_now/id/*'];

  domPreconditions = [
    {
      selector: '.col-sm-9 h2',
      shouldExist: true,
      timeout: 5000,
    },
    {
      selector: 'button[role="action"]',
      shouldExist: true,
      timeout: 5000,
    },
    {
      selector: '#captcha_code',
      shouldExist: true,
      timeout: 5000,
    },
    {
      selector: '#page_buy_now_captcha label img',
      shouldExist: true,
      timeout: 5000,
    },
  ];

  async run(): Promise<void> {
    const log = new Log('buy-offer-matcher');
    log.push('Buy offer matcher activated');

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

      // Get product title
      const titleElement = document.querySelector('#page_buy_now h2');
      if (!titleElement) {
        log.push('Product title not found').write();
        return;
      }

      const productText = titleElement.textContent || '';
      log.push(`Found product: ${productText}`);

      // Parse and validate product
      const product = ProductFactory.parse(result.config, productText);

      if (isInvalidProduct(product)) {
        log.push(`Invalid product format: ${product.error}`).write();
        return;
      }

      log.push(`Product details: ${JSON.stringify(product)}`);

      const currentUrl = window.location.href;
      const flowId = FlowUtils.parseIDFromHref(currentUrl);

      // Check if this flow is already being purchased
      const buyingStateResponse = await sendBackgroundCommand('state.buying', {
        action: 'check',
        flowId,
      });

      if (buyingStateResponse.data?.buying) {
        log.push(`Already buying this flow (ID: ${flowId})`).write();

        // Close duplicate tab
        await sendBackgroundCommand('tab.manage', {
          action: 'close',
          tabId: window.tabId,
        });

        return;
      }

      // Product is already validated by factory
      const { allowed, delay } = { allowed: product.allowed, delay: product.delay };
      if (!allowed) {
        log.push('Product not allowed by configuration').write();
        return;
      }

      // Calculate timeout (delay + extra headroom)
      const delaySeconds = delay || 0;
      const extraHeadroomSeconds = 30;
      const timeout = Date.now() + (delaySeconds + extraHeadroomSeconds) * 1000;

      // Mark flow as being purchased
      await sendBackgroundCommand('state.buying', {
        action: 'mark',
        flowId,
        timeout,
      });

      log.push(`Starting purchase process (Flow ID: ${flowId}, delay: ${delaySeconds}s)`);

      // Send command to execute purchase
      const response = await sendBackgroundCommand('buyOffer.execute', {
        id: flowId,
        delay: delaySeconds,
        selectors: {
          input: '#captcha_code',
          img: '#page_buy_now_captcha label img',
          productTitle: '.col-sm-9 h2',
          buyFormButton: 'button[role="action"]',
        },
      });

      if (response.success) {
        log.push('Buy offer executor triggered successfully').write();
      } else {
        log.push(`Buy offer executor failed: ${response.error}`).write();

        // Clear buying state on failure
        await sendBackgroundCommand('state.buying', {
          action: 'clear',
          flowId,
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

    // Wait for and focus captcha input first
    const inputElement = (await waitForSelector(selectors.input, {
      timeout: 5000,
      visible: true,
    })) as HTMLInputElement;

    if (!inputElement) {
      throw new Error('Captcha input not found');
    }

    // Focus the input
    inputElement.focus();

    // Get product title for validation
    const titleElement = await waitForSelector(selectors.productTitle, {
      timeout: 5000,
      visible: true,
    });

    const productText = titleElement.textContent || '';
    const product = ProductFactory.parse(context.config || {}, productText);

    if (isInvalidProduct(product)) {
      throw new Error(product.error);
    }

    log.push(`Product details: ${JSON.stringify(product)}`);

    // Get buy button
    const buyButton = await waitForSelector(selectors.buyFormButton, {
      timeout: 5000,
      visible: true,
    });

    if (!buyButton) {
      throw new Error('Buy button not found');
    }

    // Check buying state (prevent race conditions)
    const buyingStateResponse = await sendBackgroundCommand('state.buying', {
      action: 'check',
      flowId: context.flowId,
    });

    // Handle if another tab started buying this flow
    if (buyingStateResponse.data?.buying) {
      log.push('Another tab is already buying this flow');

      // Close this tab
      await sendBackgroundCommand('tab.manage', {
        action: 'close',
        tabId: context.tabId,
      });

      return {
        success: false,
        matcherId: context.matcherId,
        executorName: 'buyOffer',
        error: 'Duplicate purchase attempt for flow',
      };
    }

    // Product is already validated by factory
    const { allowed, delay } = { allowed: product.allowed, delay: product.delay };

    if (!allowed) {
      throw new Error('Product not allowed by configuration');
    }

    if (delay > 0) {
      log.push(`Waiting ${delay} seconds before purchase`);
      await sleep(delay * 1000);
    }

    const currentUrl = window.location.href;

    // After delay, validate flow
    const id = FlowUtils.parseIDFromPath(currentUrl);
    const flow = await ConfigService.getFlow(id);
    if (!flow) {
      throw new Error('Flow not found');
    }

    // Process captcha
    log.push('Processing captcha image');
    const imgElement = (await waitForSelector(selectors.img, {
      timeout: 5000,
      visible: true,
    })) as HTMLImageElement;

    if (!imgElement || !imgElement.src) {
      throw new Error('Captcha image not found or invalid');
    }

    // Convert image to blob
    const imageBlob = await fetchImageAsBlob(imgElement.src);
    const reader = new FileReader();
    const imageDataUrl = await new Promise<string>((resolve, reject) => {
      reader.onloadend = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsDataURL(imageBlob);
    });

    // Send to API for processing
    const imageResponse = await sendBackgroundCommand('image.solve', {
      imageData: imageDataUrl,
    });

    if (!imageResponse.success || !imageResponse.data?.result) {
      throw new Error(imageResponse.error || 'Failed to process captcha');
    }

    // Extract and input the answer
    const answer = extractNumericAnswer(imageResponse.data.result);
    inputElement.value = answer;
    inputElement.dispatchEvent(new Event('input', { bubbles: true }));

    // Calculate remaining time
    const remainingTime = ProductFactory.getRemainingProcessingTimeSeconds(
      product,
      flow.requestTimestamp,
      context.config || {},
    );

    if (remainingTime > 0) {
      log.push(`Waiting ${remainingTime} seconds for remaining processing time`);
      await sleep(remainingTime * 1000);
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
        flowId: context.flowId,
        product: product.toString(),
        appliedDelay: delay,
        captchaProcessed: true,
        answer,
      },
      telemetry: {
        startTime,
        endTime: Date.now(),
        domOperations: 4, // Input, title, image, and buy click
        networkRequests: 3, // State check, image processing, and buy submit
        errors,
      },
    };
  } catch (error) {
    log.push(`Fatal error: ${error}`).write();
    console.error('[BuyOfferExecutor] Fatal error:', error);

    // Track specific error types
    if (error instanceof Error) {
      errors.push(error);
      if (error.message.includes('captcha')) {
        log.push('Captcha processing failed');
      } else if (error.message.includes('flow')) {
        log.push('Flow validation failed');
      }
    }

    // Clear buying state on failure
    try {
      await sendBackgroundCommand('state.buying', {
        action: 'clear',
        flowId: context.flowId,
      });
    } catch (cleanupError) {
      console.error('[BuyOfferExecutor] Error clearing buying state:', cleanupError);
      if (cleanupError instanceof Error) {
        errors.push(cleanupError);
      }
    }

    return {
      success: false,
      matcherId: context.matcherId,
      executorName: 'buyOffer',
      error: error instanceof Error ? error.message : 'Unknown error',
      telemetry: {
        startTime,
        endTime: Date.now(),
        domOperations: errors.some(e => e.message.includes('not found')) ? 1 : 2,
        networkRequests: errors.some(e => e.message.includes('API')) ? 1 : 2,
        errors,
      },
    };
  }
}

// Export for background script to inject
if (typeof window !== 'undefined') {
  (window as any).__buyOfferExecutor = executeBuyOfferWorkflow;
}
