import {
  registerMatcher,
  waitForSelector,
  clickWithVerification,
  sendBackgroundCommand,
  sleep,
  fetchImageAsBlob,
  extractNumericAnswer,
} from '@src/lib';
import { CaptchaProcessor } from '@src/lib/CaptchaProcessor';
import { Log, FlowUtils, ProductFactory, ConfigService } from '@extension/shared';
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
    const currentUrl = window.location.href;
    const flowId = FlowUtils.parseIDFromHref(currentUrl);
    const log = Log.withFlow(MATCHER_IDS.BUY_OFFER, flowId);
    log.info('🔄 Buy offer matcher activated');
    log.debug('Current URL', { url: currentUrl, flowId });

    try {
      // Get configuration and check if enabled
      log.debug('Fetching extension configuration');
      const configResponse = (await sendBackgroundCommand('extension.getConfig', {})) as CommandResponse<{
        config: ExecutionConfig;
        enabled: boolean;
      }>;
      const result = configResponse.data;
      if (!result) {
        log.warn('No configuration found - extension may not be initialized');
        await log.write();
        return;
      }

      if (!result.enabled) {
        log.info('Extension is currently disabled');
        await log.write();
        return;
      }

      log.info('Extension enabled, proceeding with buy offer detection');

      // Get product title
      log.debug('Looking for product title element');
      const titleElement = document.querySelector('#page_buy_now h2');
      if (!titleElement) {
        log.warn('Product title not found - page may not be fully loaded');
        await log.write();
        return;
      }

      const productText = titleElement.textContent || '';
      log.info(`Product detected: "${productText}"`);

      // Parse and validate product
      log.debug('Parsing product with factory');
      const product = ProductFactory.parse(result.config, productText);

      if (isInvalidProduct(product)) {
        log.warn(`Invalid product format: ${product.error}`, { productText });
        await log.write();
        return;
      }

      log.info('Product parsed successfully');
      log.debug(`Product details`, {
        name: product.name,
        type: product.type,
        allowed: product.allowed,
      });

      // flowId already extracted at the start

      // Check if this flow is already being purchased
      log.info('Checking if flow is already being purchased');
      const buyingStateResponse = await sendBackgroundCommand('state.buying', {
        action: 'check',
        flowId,
      });

      if (buyingStateResponse.data?.buying) {
        log.info(`Flow ${flowId} is already being purchased by another tab`);
        log.debug('Closing this duplicate tab');
        await log.write();

        // Close duplicate tab
        await sendBackgroundCommand('tab.manage', {
          action: 'close',
          tabId: window.tabId,
        });

        return;
      }

      // Product is already validated by factory
      const { allowed } = { allowed: product.allowed };
      if (!allowed) {
        log.info('Product not allowed by current configuration', { product: product.name });
        await log.write();
        return;
      }

      // Calculate timeout (delay + extra headroom)
      const delaySeconds = 0;
      const extraHeadroomSeconds = 30;
      const timeout = Date.now() + (delaySeconds + extraHeadroomSeconds) * 1000;

      // Mark flow as being purchased
      log.info('Marking flow as being purchased to prevent duplicates');
      await sendBackgroundCommand('state.buying', {
        action: 'mark',
        flowId,
        timeout,
      });

      log.info(`🎯 Starting purchase process for flow ${flowId}`);
      log.debug(`Timeout set to: ${new Date(timeout).toISOString()}`);

      // Send command to execute purchase
      log.info('Triggering buy offer executor');
      const response = await sendBackgroundCommand('buyOffer.execute', {
        id: flowId,
        selectors: {
          input: '#captcha_code',
          img: '#page_buy_now_captcha label img',
          productTitle: '.col-sm-9 h2',
          buyFormButton: 'button[role="action"]',
        },
      });

      if (response.success) {
        log.info('✅ Buy offer executor triggered successfully');
        log.debug('Executor response', { data: response.data });
      } else {
        log.error(`❌ Buy offer executor failed: ${response.error}`);
        log.debug('Clearing buying state after executor failure');

        // Clear buying state on failure
        await sendBackgroundCommand('state.buying', {
          action: 'clear',
          flowId,
        });
        log.info('Buying state cleared');
      }

      await log.write();
    } catch (error) {
      log.error(`❌ Critical error in buy offer matcher: ${error instanceof Error ? error.message : 'Unknown error'}`, {
        error,
        stack: error instanceof Error ? error.stack : undefined,
      });
      await log.write();
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

export async function executeBuyOfferWorkflow(
  context: ExecutionContext,
  selectors: BuyOfferSelectors,
  flowId: string,
): Promise<ExecutionResult> {
  const log = Log.withFlow(context.matcherId, flowId);
  log
    .info(`Starting buy offer workflow for tab ${context.tabId}`)
    .setMetadata({ tabId: context.tabId, url: context.url });
  const startTime = Date.now();
  const errors: Error[] = [];

  try {
    log.info('Validating preconditions for buy offer workflow');

    // Wait for and focus captcha input first
    log.debug('Waiting for captcha input element');
    const inputElement = (await waitForSelector(selectors.input, {
      timeout: 5000,
      visible: true,
    })) as HTMLInputElement;

    if (!inputElement) {
      throw new Error('Captcha input not found');
    }
    log.info('Captcha input element found and ready');

    // Focus the input
    inputElement.focus();
    log.debug('Captcha input focused');

    // Get product title for validation
    log.debug('Retrieving product title for validation');
    const titleElement = await waitForSelector(selectors.productTitle, {
      timeout: 5000,
      visible: true,
    });

    const productText = titleElement.textContent || '';
    log.info(`Product found: "${productText}"`);

    const product = ProductFactory.parse(context.config || {}, productText);

    if (isInvalidProduct(product)) {
      log.error(`Invalid product format: ${product.error}`, { productText });
      throw new Error(product.error);
    }

    log.info('Product validated successfully');
    log.debug(`Product details: ${JSON.stringify(product)}`);

    // Get buy button
    log.debug('Locating buy button');
    const buyButton = await waitForSelector(selectors.buyFormButton, {
      timeout: 5000,
      visible: true,
    });

    if (!buyButton) {
      throw new Error('Buy button not found');
    }
    log.info('Buy button found and ready');

    // Check buying state (prevent race conditions)
    log.info('Checking buying state to prevent race conditions');
    const buyingStateResponse = await sendBackgroundCommand('state.buying', {
      action: 'check',
      flowId: flowId,
    });

    // Handle if another tab started buying this flow
    if (buyingStateResponse.data?.buying) {
      log.warn('Another tab is already buying this flow');
      log.info('Closing duplicate tab to prevent double purchase');

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
    const { allowed } = { allowed: product.allowed };

    if (!allowed) {
      log.warn('Product not allowed by configuration', { product: product.name });
      throw new Error('Product not allowed by configuration');
    }

    const currentUrl = window.location.href;

    const flow = await ConfigService.getFlow(flowId);
    if (!flow) {
      log.error('Flow not found', { flowId: flowId });
      throw new Error('Flow not found');
    }
    log.info('Flow validation successful');

    // Process captcha
    log.info('Starting captcha processing');
    const imgElement = (await waitForSelector(selectors.img, {
      timeout: 5000,
      visible: true,
    })) as HTMLImageElement;

    if (!imgElement || !imgElement.src) {
      log.error('Captcha image not found or invalid');
      throw new Error('Captcha image not found or invalid');
    }
    log.debug(`Captcha image source: ${imgElement.src.substring(0, 50)}...`);

    // Convert image to data URL once
    log.info('Converting captcha image to data URL for processing');
    const reader = new FileReader();
    const imageDataUrl = await new Promise<string>(async (resolve, reject) => {
      reader.onloadend = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsDataURL(await fetchImageAsBlob(imgElement.src));
    });

    const captchaProcessor = CaptchaProcessor.getInstance();
    const answer = await captchaProcessor.solveCaptcha(imgElement.src, imageDataUrl, flowId);

    log.debug('Image conversion successful');

    log.info(`Captcha solved successfully: ${answer}`);

    inputElement.value = answer;
    inputElement.dispatchEvent(new Event('input', { bubbles: true }));
    log.debug('Answer entered into captcha field');

    // Calculate remaining time
    const remainingTime = ProductFactory.getRemainingProcessingTimeSeconds(
      product,
      flow.requestTimestamp,
      context.config || {},
    );

    if (remainingTime > 0) {
      log.info(`Waiting ${remainingTime} seconds for remaining processing time`);
      await sleep(remainingTime * 1000 - 100);
      log.debug('Processing time wait completed');
    }

    // Execute purchase
    log.info('EXECUTING FINAL PURCHASE');

    if (!context.dryRun) {
      log.info('Clicking buy button to complete purchase');
      await clickWithVerification(buyButton, {
        verify: true,
        scroll: true,
      });

      // Wait for form submission
      log.debug('Waiting for form submission to complete');
      await sleep(500);

      // Mark flow as done
      log.info('Purchase completed successfully, marking flow as done');
      await ConfigService.doneFlow(context.flowId);
      log.info(`Flow ${context.flowId} marked as completed`);

      // Clear buying state on success
      log.debug('Clearing buying state');
      await sendBackgroundCommand('state.buying', {
        action: 'clear',
        flowId: context.flowId,
      });
      log.info('Buying state cleared successfully');
    } else {
      log.debug('Dry run: Would click buy button');
      log.info('Dry run: Would mark flow as done');
    }

    log.info(`✅ Buy offer workflow completed successfully for flow ${context.flowId}`);
    await log.write();

    return {
      success: true,
      matcherId: context.matcherId,
      executorName: 'buyOffer',
      data: {
        flowId: context.flowId,
        product: product.toString(),
        captchaProcessed: true,
        answer,
        completedAt: Date.now(),
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
    log.error(`❌ Fatal error in buy offer workflow: ${error}`, {
      stack: error instanceof Error ? error.stack : undefined,
      flowId: context.flowId,
      url: context.url,
    });
    await log.write();
    console.error('[BuyOfferExecutor] Fatal error:', error);

    // Track specific error types for better debugging
    if (error instanceof Error) {
      errors.push(error);
      if (error.message.includes('captcha')) {
        log.error('Captcha processing failure - may need manual intervention');
      } else if (error.message.includes('flow')) {
        log.error('Flow validation failure - flow may have expired or been processed');
      } else if (error.message.includes('button')) {
        log.error('UI interaction failure - page structure may have changed');
      }
    }

    // Clear buying state on failure
    try {
      log.debug('Attempting to clear buying state after error');
      await sendBackgroundCommand('state.buying', {
        action: 'clear',
        flowId: context.flowId,
      });
      log.info('Buying state cleared after error');
    } catch (cleanupError) {
      console.error('[BuyOfferExecutor] Error clearing buying state:', cleanupError);
      log.error('Failed to clear buying state', { error: cleanupError });
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
