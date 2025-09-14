import {
  registerMatcher,
  sendBackgroundCommand,
  Log,
  isValidTimeOfDay,
  assertValidTimeOfDay,
  waitForSelector,
  clickWithVerification,
  sleep,
  Product,
} from '@src/lib';
import type { Matcher, ExecutionContext, ExecutionResult, OffersSelectors } from '@extension/types';

/**
 * Offers Matcher - Detects offer pages and triggers offer processing
 */
class OffersMatcher implements Matcher {
  id = 'offers-matcher';
  name = 'Offers Clicking Workflow';
  enabled = true;
  priority = 10;

  urlPatterns = [
    // 'https://auktion.hansemerkur.de/browse/search/*',
    // 'https://auktion.hansemerkur.de/karte_sofortkauf.html',
    'https://auktion.hansemerkur.de/item.php',
  ];

  domPreconditions = [
    {
      selector: 'body',
      shouldExist: true,
      timeout: 5000,
    },
  ];

  async run(): Promise<void> {
    const log = new Log('offers-matcher');
    log.push('Offers matcher activated');

    try {
      // Get configuration and check if enabled
      const configResponse = await sendBackgroundCommand('extension.getConfig', {});
      const config = configResponse.data;
      if (!config) {
        log.push('No configuration found').write();
        return;
      }

      if (!config.enabled) {
        log.push('Extension disabled').write();
        return;
      }

      // Check operational hours if not in email mode
      if (!config.emailMode) {
        await assertValidTimeOfDay(config);
      }

      const currentUrl = window.location.href;

      // Determine which type of offers page we're on
      if (currentUrl.includes('karte_sofortkauf.html')) {
        log.push('Map offers page detected');
        await this.handleMapOffers(config, log);
      } else if (currentUrl.includes('browse/search')) {
        log.push('Browse offers page detected');
        await this.handleBrowseOffers(config, log);
      } else if (currentUrl.includes('item.php')) {
        log.push('Browse offers page detected');
        await this.handleBrowseOffers(config, log);
      }
    } catch (error) {
      log.push(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`).write();
      console.error('[OffersMatcher] Error:', error);
    }
  }

  private async handleMapOffers(config: any, log: Log): Promise<void> {
    if (config.emailMode) {
      // In email mode, just set up periodic refresh
      const randomMinutes = Math.floor(Math.random() * 30) + 20; // 20-50 minutes
      log.push(`Email mode: Will refresh in ${randomMinutes} minutes`).write();

      setTimeout(
        () => {
          window.location.reload();
        },
        randomMinutes * 60 * 1000,
      );

      return;
    }

    // Send command to process map offers
    const response = await sendBackgroundCommand('offers.clickProductLink', {
      selectors: {
        offerMarkers: '.leaflet-marker-pane img[src="templates/design_version2_01/images/marker/marker-02.png"]',
        offerPopup: '.leaflet-popup-content a',
        browseList: '',
        buyButton: '',
        titleLink: '',
      },
    });

    if (response.success) {
      log.push('Map offers executor triggered successfully').write();
    } else {
      log.push(`Map offers executor failed: ${response.error}`).write();
    }

    // Set up auto-refresh
    this.setupAutoRefresh(config);
  }

  private async handleBrowseOffers(config: any, log: Log): Promise<void> {
    // Send command to process browse offers
    const response = await sendBackgroundCommand('offers.clickProductLink', {
      selectors: {
        offerMarkers: '',
        offerPopup: '',
        browseList: 'div.browse_list .row',
        buyButton: '.buy_now a.btn',
        titleLink: '.title a',
      },
    });

    if (response.success) {
      log.push('Browse offers executor triggered successfully').write();
    } else {
      log.push(`Browse offers executor failed: ${response.error}`).write();
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
        console.log('[OffersMatcher] Max checks reached, refreshing page');
        window.location.reload();
      }
    }, 1000);
  }
}

// Register and run the matcher when content script loads
const offersMatcher = new OffersMatcher();

// Check if current URL matches
function checkAndRun() {
  const currentUrl = window.location.href;
  const matches = offersMatcher.urlPatterns.some(pattern => {
    // Convert simple wildcard pattern to regex
    const regex = new RegExp(pattern.replace(/\*/g, '.*'));
    return regex.test(currentUrl);
  });

  if (matches) {
    console.log('[OffersMatcher] URL matches, registering matcher');
    registerMatcher(offersMatcher);

    // Run the matcher after DOM is ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => offersMatcher.run());
    } else {
      // Small delay to ensure everything is ready
      setTimeout(() => offersMatcher.run(), 1000);
    }
  }
}

// Check on initial load
checkAndRun();

// Monitor for dynamic content changes (for map offers)
if (window.location.href.includes('karte_sofortkauf.html')) {
  const observer = new MutationObserver(mutationList => {
    // Look for map tiles being loaded
    const hasMapTiles = mutationList.some(
      m => m.target.nodeName === 'IMG' && (m.target as HTMLElement).className === 'leaflet-tile leaflet-tile-loaded',
    );

    if (hasMapTiles) {
      console.log('[OffersMatcher] Map tiles loaded, running matcher');
      offersMatcher.run();
    }
  });

  observer.observe(document.body, {
    attributes: true,
    childList: true,
    subtree: true,
  });
}

export default offersMatcher;

/**
 * Offers Executor - Processes offer pages by identifying and clicking valid products
 */
export async function executeOffersWorkflow(
  context: ExecutionContext,
  selectors: OffersSelectors,
): Promise<ExecutionResult> {
  const log = new Log('offers-executor');
  const startTime = Date.now();
  const errors: Error[] = [];
  let processedCount = 0;
  const openedOffers: string[] = [];

  try {
    log.push(`Starting offers workflow for tab ${context.tabId}`);

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
        executorName: 'offers',
        error: 'Tab is not managed',
      };
    }

    const currentUrl = window.location.href;

    // Process based on page type
    if (currentUrl.includes('karte_sofortkauf.html')) {
      await processMapOffers();
    } else if (currentUrl.includes('browse/search')) {
      await processBrowseOffers();
    } else if (currentUrl.includes('item.php')) {
      await processBrowseOffers();
    }

    // Process map offers (with markers)
    async function processMapOffers(): Promise<void> {
      try {
        // Wait for map to load
        await sleep(2000);

        // Find all valid offer markers
        const offerMarkers = document.querySelectorAll(selectors.offerMarkers);
        log.push(`Found ${offerMarkers.length} offer markers`);

        for (const marker of offerMarkers) {
          if (!(marker instanceof HTMLElement)) continue;

          // Click the marker to open popup
          if (context.dryRun) {
            log.push('Dry run: Would click offer marker');
          } else {
            await clickWithVerification(marker, { delay: 200 });
          }

          // Wait for popup to appear
          await sleep(200);

          try {
            // Find link in popup
            const popupLink = document.querySelector(selectors.offerPopup) as HTMLAnchorElement;

            if (popupLink?.href) {
              log.push(`Opening offer: ${popupLink.href}`);
              openedOffers.push(popupLink.href);

              if (!context.dryRun) {
                // Open in new managed tab
                await sendBackgroundCommand('tab.manage', {
                  action: 'open',
                  url: popupLink.href,
                });
              } else {
                log.push('Dry run: Would open offer in new tab');
              }

              processedCount++;
            }
          } catch (error) {
            log.push(`Error processing offer popup: ${error}`);
            errors.push(error as Error);
          }
        }
      } catch (error) {
        log.push(`Error in map offers processing: ${error}`);
        errors.push(error as Error);
      }
    }

    // Process browse offers (list view)
    async function processBrowseOffers(): Promise<void> {
      try {
        // Find all offer rows
        const offerRows = document.querySelectorAll(selectors.browseList);
        log.push(`Found ${offerRows.length} offer rows`);

        for (const row of offerRows) {
          const buyButton = row.querySelector(selectors.buyButton) as HTMLAnchorElement;
          const titleLink = row.querySelector(selectors.titleLink) as HTMLElement;

          if (!buyButton) {
            log.push('No buy button found, skipping');
            continue;
          }

          if (!titleLink) {
            log.push('No title found, skipping');
            continue;
          }

          // Parse product from title
          const productText = titleLink.textContent || '';
          log.push(`Product: ${productText}`);

          const product = new Product(productText);
          if (!product.valid) {
            log.push('Invalid product format, skipping');
            continue;
          }

          log.push(`Product details: ${product.toString()}`);

          // Check if product is allowed based on config
          const config = context.config || {};
          const { allowed } = product.isAllowed(config);

          if (!allowed) {
            log.push('Product not allowed by configuration, skipping');
            continue;
          }

          // Open the offer
          log.push(`Opening offer: ${buyButton.href}`);
          openedOffers.push(buyButton.href);

          if (!context.dryRun) {
            await sendBackgroundCommand('tab.manage', {
              action: 'open',
              url: buyButton.href,
            });
          } else {
            log.push('Dry run: Would open offer in new tab');
          }

          processedCount++;
        }

        // Close current tab after processing all offers
        if (processedCount > 0 && !context.dryRun) {
          log.push('Closing current tab after processing offers');
          await sendBackgroundCommand('tab.manage', {
            action: 'close',
            tabId: context.tabId,
          });
        }
      } catch (error) {
        log.push(`Error in browse offers processing: ${error}`);
        errors.push(error as Error);
      }
    }

    await log.write();

    return {
      success: true,
      matcherId: context.matcherId,
      executorName: 'offers',
      data: {
        processedCount,
        openedOffers,
        pageType: currentUrl.includes('karte_sofortkauf.html') ? 'map' : 'browse',
      },
      telemetry: {
        startTime,
        endTime: Date.now(),
        domOperations: processedCount * 2, // Click and open
        networkRequests: processedCount,
        errors,
      },
    };
  } catch (error) {
    log.push(`Fatal error: ${error}`).write();
    console.error('[OffersExecutor] Fatal error:', error);

    return {
      success: false,
      matcherId: context.matcherId,
      executorName: 'offers',
      error: error instanceof Error ? error.message : 'Unknown error',
      telemetry: {
        startTime,
        endTime: Date.now(),
        domOperations: processedCount * 2,
        networkRequests: processedCount,
        errors: [...errors, error as Error],
      },
    };
  }
}

// Export for background script to inject
if (typeof window !== 'undefined') {
  (window as any).__offersExecutor = executeOffersWorkflow;
}
