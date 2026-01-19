import {
  Log,
  FlowUtils,
  ProductFactory,
  ConfigService,
  BackgroundUtils,
  installGlobalErrorHandlers,
  TabManager,
} from '@extension/shared';
import { isInvalidProduct, isProductNotAllowed as isProductNotAllowed, MATCHER_IDS } from '@extension/types';
import { clickWithVerification, sleep, ensureFocus } from '@src/lib';
import { CaptchaSolver } from '@src/lib/CaptchaSolver';
import type { Matcher, ExecutionContext, ExecutionResult, BuyOfferSelectors, Flow } from '@extension/types';

// Helper to convert an image element into a data URL, DPI-aware
function getImageToDataURL(img: HTMLImageElement, type: string = 'image/png', quality?: number): string {
  if (!img.complete || img.naturalWidth === 0) {
    throw new Error('Image not loaded yet');
  }
  const dpr = window.devicePixelRatio || 1;
  const w = img.naturalWidth;
  const h = img.naturalHeight;

  const canvas = document.createElement('canvas');
  canvas.width = Math.round(w * dpr);
  canvas.height = Math.round(h * dpr);

  const ctx = canvas.getContext('2d');
  if (!ctx) throw new Error('2D context not available');

  ctx.scale(dpr, dpr);
  ctx.drawImage(img, 0, 0, w, h);

  return canvas.toDataURL(type, quality);
}

/**
 * Buy Offer Matcher - Detects and triggers purchase workflow for valid products
 */
// Install global error handlers early
installGlobalErrorHandlers({
  matcherId: MATCHER_IDS.BUY_OFFER,
  getFlowId: () => {
    try {
      return FlowUtils.parseIDFromPath(window.location.href);
    } catch {
      return undefined;
    }
  },
});

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
    log.info('🔄 Buy offer matcher activated').setMetadata({ url: currentUrl, flowId });
    const tabManager = TabManager.getInstance();

    try {
      // Get configuration and check if enabled
      const { config, enabled } = await BackgroundUtils.getExtensionConfig();

      if (!enabled) {
        log.info('Extension is currently disabled');
        await log.write();
        return;
      }

      try {
        const flow = await ConfigService.getFlow(flowId);
        if (!flow) {
          log.error('Flow not found, aborting buy offer execution');
        } else {
          const managed = flow.source !== 'manual';

          const context: ExecutionContext = {
            matcherId: MATCHER_IDS.BUY_OFFER,
            url: currentUrl,
            config,
            dryRun: false,
          };
          const result = await executeBuyOfferWorkflow(
            context,
            {
              input: '#captcha_code',
              img: '#page_buy_now_captcha label img',
              productTitle: '.col-sm-9 h2',
              buyFormButton: 'button[name="action"]',
            },
            flow,
            managed,
          );
          log.info(`✅ Buy offer executor completed: ${result.success ? 'success' : 'failure'}, result: ${result}`);
        }
      } catch (e: any) {
        log.error(`❌ Buy offer executor failed: ${e?.message || String(e)}`);
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

    // Run the matcher after DOM is ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => buyOfferMatcher.run());
    } else {
      // Small delay to ensure everything is ready
      setTimeout(() => buyOfferMatcher.run(), 0);
    }
  }
}

// Check on initial load
checkAndRun();

export async function executeBuyOfferWorkflow(
  context: ExecutionContext,
  selectors: BuyOfferSelectors,
  flow: Flow,
  managed: boolean,
): Promise<ExecutionResult> {
  const log = Log.withFlow(context.matcherId, flow.id);
  log.info(`Starting buy offer workflow`).setMetadata({ url: context.url });
  const startTime = Date.now();
  const errors: Error[] = [];
  const tabManager = TabManager.getInstance();
  const captchaSolver = CaptchaSolver.getInstance();

  // Wait for and focus captcha input first
  const inputElement = document.querySelector(selectors.input) as HTMLInputElement;

  if (!inputElement) {
    throw new Error('Captcha input not found');
  }
  try {
    // Focus the input with verification and retries
    await ensureFocus(inputElement);
  } catch {}

  // Begin captcha image fetch and solve as early as possible, in parallel with other checks
  const imgElement = document.querySelector(selectors.img) as HTMLImageElement;
  if (!imgElement || !imgElement.src) {
    log.error('Captcha image not found or invalid');
    throw new Error('Captcha image not found or invalid');
  }
  if (!imgElement.complete || imgElement.naturalWidth === 0) {
    await new Promise<void>(resolve => imgElement.addEventListener('load', () => resolve(), { once: true }));
  }
  const earlyDataUrl = getImageToDataURL(imgElement);

  if (flow.status === 'done' || flow.status === 'failed') {
    log.info('❌ Flow is already completed, closing all tabs');
    if (managed) {
      await tabManager.closeAllTabs(flow.id);
    } else {
      await tabManager.closeCurrentTab();
    }

    return {
      success: false,
      matcherId: context.matcherId,
      executorName: 'buyOffer',
      data: {},
      telemetry: {
        startTime,
        endTime: Date.now(),
        errors,
      },
    };
  }

  try {
    const titleLink = document.querySelector(selectors.productTitle) as HTMLImageElement;

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

    if (isProductNotAllowed(product)) {
      log.warn(`Unallowed product format: ${product.name}`);

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

    // Get buy button
    const buyButton = document.querySelector(selectors.buyFormButton);

    if (!buyButton) {
      throw new Error('Buy button not found');
    }

    log.info('Starting captcha processing');
    const answer = await captchaSolver.solveCaptcha(
      imgElement.src,
      earlyDataUrl,
      flow.id,
      context.config.captchaSolver,
    );

    log.info(`Captcha solved successfully: ${answer}`);

    inputElement.value = answer;
    inputElement.dispatchEvent(new Event('input', { bubbles: true }));
    log.debug('Answer entered into captcha field');

    // Execute purchase
    if (!context.dryRun) {
      log.info(`Flow ${flow.id} marked as completed`);

      // Calculate remaining time
      const remainingTime = ProductFactory.getRemainingProcessingTimeSeconds(product, flow.timestamp, context.config);

      const timeoutMs = remainingTime * 1000 + 5000;
      managed &&
        (await BackgroundUtils.scheduleCloseAfterNavigation({
          flowId: flow.id,
          timeoutMs: timeoutMs,
        }));

      if (remainingTime > 0) {
        log.info(`Waiting ${remainingTime} seconds for remaining processing time`);
        await sleep(remainingTime * 1000 - 100);
      } else {
        log.info(`Buying immediately ${flow.requestTimestamp}`);
      }

      // Mark flow as done
      ConfigService.doneFlow(flow.id);

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
