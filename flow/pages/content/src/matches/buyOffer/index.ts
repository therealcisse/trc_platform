import { Log, FlowUtils, ProductFactory, ConfigService } from '@extension/shared';
import { isInvalidProduct, MATCHER_IDS } from '@extension/types';
import { registerMatcher, waitForSelector, clickWithVerification, sleep, fetchImageAsBlob } from '@src/lib';
import { sendBackgroundCommand } from '@extension/shared';
import { CaptchaProcessor } from '@src/lib/CaptchaProcessor';
import type {
  CommandResponse,
  ExecutionConfig,
  Matcher,
  ExecutionContext,
  ExecutionResult,
  BuyOfferSelectors,
  Flow,
} from '@extension/types';
import { TabManager } from '@extension/shared';

/**
 * Buy Offer Matcher - Detects and triggers purchase workflow for valid products
 */
class BuyOfferMatcher implements Matcher {
  id = MATCHER_IDS.BUY_OFFER;
  name = 'Buy Offer Workflow';
  enabled = true;
  priority = 20; // Higher priority than email/offers

  urlPatterns = ['http://localhost:8082/buy_now/id/*', 'https://auktion.hansemerkur.de/buy_now/id/*'];

  domPreconditions = [
    {
      selector: '.col-sm-9 h2',
      shouldExist: true,
      timeout: 5000,
    },
    {
      selector: 'button[name="action"]',
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
    const flowId = FlowUtils.parseIDFromPath(currentUrl);
    const log = Log.withFlow(MATCHER_IDS.BUY_OFFER, flowId);
    log.info('🔄 Buy offer matcher activated');
    log.debug('Current URL', { url: currentUrl, flowId });
    const tabManager = TabManager.getInstance();

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
        await tabManager.closeTab(window.tabId);
        return;
      }

      // Calculate timeout (delay + extra headroom)
      const delaySeconds = 0;
      const extraHeadroomSeconds = 300;
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
          buyFormButton: 'button[name="action"]',
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
  flow: Flow,
): Promise<ExecutionResult> {
  const log = Log.withFlow(context.matcherId, flow.id);
  log
    .info(`Starting buy offer workflow for tab ${context.tabId}`)
    .setMetadata({ tabId: context.tabId, url: context.url });
  const startTime = Date.now();
  const errors: Error[] = [];
  const tabManager = TabManager.getInstance();
  const captchaProcessor = CaptchaProcessor.getInstance();

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

  if (flow.status === 'done' || flow.status === 'failed') {
    log.info('❌ Flow is already done, closing all tabs');
    await tabManager.closeAllTabs(flow.id);
  }

  try {
    log.info('Validating preconditions for buy offer workflow');

    const titleLink = (await waitForSelector(selectors.productTitle, {
      timeout: 5000,
      visible: true,
    })) as HTMLImageElement;

    if (!titleLink) {
      log.info('No title found, skipping');

      log.info('❌ Purchase completed unsuccessfully, marking flow as done');
      await ConfigService.failedFlow(flow.id);
      log.info(`Flow ${flow.id} marked as completed`);

      log.info(`Closing all tabs for flow: ${flow.id}`);
      setTimeout(async function () {
        await tabManager.closeAllTabs(flow.id);
      }, 100);

      return {
        success: true,
        matcherId: context.matcherId,
        executorName: 'buyOffer',
        data: {
          flowId: flow.id,
          completedAt: Date.now(),
        },
        telemetry: {
          startTime,
          endTime: Date.now(),
          errors,
        },
      };
    }

    const title = titleLink.textContent ?? '';

    log.info(`Product: ${title}`);

    const config = context.config;
    const product = ProductFactory.parse(config, title);

    if (isInvalidProduct(product)) {
      log.warn(`Invalid product format: ${product.name} ${product.error}`);

      log.info('❌ Purchase completed unsuccessfully, marking flow as done');
      await ConfigService.failedFlow(flow.id);
      log.info(`Flow ${flow.id} marked as completed`);

      log.info(`Closing all tabs for flow: ${flow.id}`);
      setTimeout(async function () {
        await tabManager.closeAllTabs(flow.id);
      }, 100);

      return {
        success: true,
        matcherId: context.matcherId,
        executorName: 'buyOffer',
        data: {
          flowId: flow.id,
          product: product,
          completedAt: Date.now(),
        },
        telemetry: {
          startTime,
          endTime: Date.now(),
          errors,
        },
      };
    }

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

    const answer = await captchaProcessor.solveCaptcha(imgElement.src, imageDataUrl, flow.id);

    log.debug('Image conversion successful');

    log.info(`Captcha solved successfully: ${answer}`);

    inputElement.value = answer;
    inputElement.dispatchEvent(new Event('input', { bubbles: true }));
    log.debug('Answer entered into captcha field');

    // Execute purchase
    log.info('EXECUTING FINAL PURCHASE');

    if (!context.dryRun) {
      log.info('Clicking buy button to complete purchase');

      log.info(`Flow ${flow.id} marked as completed`);
      // Clear buying state on success
      log.debug('Clearing buying state');
      await sendBackgroundCommand('state.buying', {
        action: 'clear',
        flowId: flow.id,
      });

      // Calculate remaining time
      const remainingTime = ProductFactory.getRemainingProcessingTimeSeconds(
        product,
        flow.requestTimestamp,
        context.config,
      );

      const timeoutMs = remainingTime * 1000 + 5000;
      log.info(`Closing all tabs for flow: ${flow.id} after ${timeoutMs}ms`);
      await sendBackgroundCommand('flows.scheduleCloseAfterNavigation', {
        flowId: flow.id,
        timeoutMs: timeoutMs,
      });

      if (remainingTime > 0) {
        log.info(`Waiting ${remainingTime} seconds for remaining processing time`);
        await sleep(remainingTime - 100);
        log.debug('Processing time wait completed');
      } else {
        log.info(`Buying immediately ${flow.requestTimestamp}`);
      }

      // Mark flow as done
      log.info('Purchase completed successfully, marking flow as done');
      await ConfigService.doneFlow(flow.id);

      log.info('Clicking on buyButton');

      log.info(`✅ Buy offer workflow completed successfully for flow ${flow.id}`);
      await log.write();

      await clickWithVerification(buyButton, {
        verify: false,
        scroll: false,
      });

      log.info('Buying state cleared successfully');
    } else {
      log.debug('Dry run: Would click buy button');
      log.info('Dry run: Would mark flow as done');
    }

    return {
      success: true,
      matcherId: context.matcherId,
      executorName: 'buyOffer',
      data: {
        flowId: flow.id,
        product: product,
        captchaProcessed: true,
        answer,
        completedAt: Date.now(),
      },
      telemetry: {
        startTime,
        endTime: Date.now(),
        errors,
      },
    };
  } catch (error) {
    log.error(`❌ Fatal error in buy offer workflow: ${error}`, {
      stack: error instanceof Error ? error.stack : undefined,
      flowId: flow.id,
      url: context.url,
    });
    await log.write();
    console.error('[BuyOfferExecutor] Fatal error:', error);

    log.info('Purchase completed unsuccessfully, marking flow as done');
    await ConfigService.failedFlow(flow.id);
    log.info(`Flow ${flow.id} marked as completed`);

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
        flowId: flow.id,
      });
      log.info('Buying state cleared after error');
    } catch (cleanupError) {
      console.error('[BuyOfferExecutor] Error clearing buying state:', cleanupError);
      log.error('Failed to clear buying state', { error: cleanupError });
      if (cleanupError instanceof Error) {
        errors.push(cleanupError);
      }
    }

    log.info(`Closing all tabs for flow: ${flow.id}`);
    setTimeout(async function () {
      await tabManager.closeAllTabs(flow.id);
    }, 100);

    return {
      success: false,
      matcherId: context.matcherId,
      executorName: 'buyOffer',
      error: error instanceof Error ? error.message : 'Unknown error',
      telemetry: {
        startTime,
        endTime: Date.now(),
        errors,
      },
    };
  }
}
// Export for background script to inject
if (typeof window !== 'undefined') {
  (window as any).__buyOfferExecutor = executeBuyOfferWorkflow;
}
