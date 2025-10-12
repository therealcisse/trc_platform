import {
  FlowUtils,
  Log,
  BackgroundUtils,
  installGlobalErrorHandlers,
  startPreciseSecondTicker,
} from '@extension/shared';
import { MATCHER_IDS } from '@extension/types';
import { isValidTimeOfDay, sleep } from '@src/lib';
import type { ExecutionConfig, Matcher, ExecutionContext, ExecutionResult, InboxSelectors } from '@extension/types';

/**
 * Inbox Matcher - Monitors HanseMerkur inbox for new messages
 */
// Install global error handlers early
installGlobalErrorHandlers({ matcherId: MATCHER_IDS.INBOX });

class InboxMatcher implements Matcher {
  id = MATCHER_IDS.INBOX;
  name = 'Inbox Link Monitor';
  enabled = true;
  priority = 10;

  urlPatterns = ['http://localhost:8082/inbox.html', 'https://auktion.hansemerkur.de/my_message_center_inbox.html*'];

  domPreconditions = [
    {
      selector: 'table',
      shouldExist: true,
      timeout: 5000,
    },
  ];

  // private schedulerInterval: NodeJS.Timeout | null = null;

  async run(): Promise<void> {
    const log = new Log(MATCHER_IDS.INBOX);
    log.info('Inbox matcher activated');

    try {
      // Get configuration
      const { config, enabled } = await BackgroundUtils.getExtensionConfig();

      if (!enabled) {
        log.info('Extension disabled');
        await log.write();
        return;
      }

      if (!config.inboxMode) {
        log.info('Inbox mode disabled');
        await log.write();
        return;
      }
      const timeAllowed = () => isValidTimeOfDay(config);

      // Check if we need to handle a scheduled reload
      const shouldScanAfterReload = sessionStorage.getItem('inbox_scan_after_reload') === '1';
      if (shouldScanAfterReload) {
        sessionStorage.removeItem('inbox_scan_after_reload');
        log.info('Performing post-reload scan');

        if (timeAllowed()) {
          // Wait for configured delay
          config.inboxPostReloadDelayMs > 0 && (await sleep(config.inboxPostReloadDelayMs));

          // Trigger scan
          await this.scanAndOpenLinks(config);
        } else {
          log.warn('Outside operational hours, skipping initial scan');
        }
      } else {
        if (timeAllowed()) {
          // Initial scan on page load
          await this.scanAndOpenLinks(config);
        } else {
          log.warn('Outside operational hours, skipping initial scan');
        }
      }

      // Start reload scheduler
      await this.startReloadScheduler(config, timeAllowed);

      await log.write();
    } catch (error) {
      log.error(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, { error });
      await log.write();
      console.error('[InboxMatcher] Error:', error);
    }
  }

  private async startReloadScheduler(config: ExecutionConfig, timeAllowed: () => boolean): Promise<void> {
    const reloadSeconds = config.inboxReloadSeconds;
    const log = new Log(MATCHER_IDS.INBOX);

    await startPreciseSecondTicker(
      ({ scheduledWallTimeMs, receivedWallTimeMs, driftMs, workerId, seq, startCount }) => {
        if (!timeAllowed()) {
          return;
        }

        const now = new Date();
        const currentSecond = now.getSeconds();

        if (reloadSeconds.includes(currentSecond)) {
          // log.info(`Scheduled reload at second ${currentSecond}`);

          // Mark for post-reload scan
          sessionStorage.setItem('inbox_scan_after_reload', '1');

          // Reload the page
          window.location.reload();
        }
      },
    );

    log.info(`Reload scheduler started for seconds: ${reloadSeconds.join(', ')}`);
  }

  private async scanAndOpenLinks(config: ExecutionConfig): Promise<void> {
    const log = new Log(MATCHER_IDS.INBOX);

    try {
      log.info('Scanning for new links');

      // Execute inbox workflow directly in-page
      try {
        const context: ExecutionContext = {
          matcherId: MATCHER_IDS.INBOX,
          url: window.location.href,
          config,
          dryRun: false,
        };
        const data = await executeInboxWorkflow(context, {
          rows: 'table.browse_list tr',
          titleLinks: 'table.browse_list tr td:nth-child(3) a',
          requestTimestampElement: 'td:nth-child(4)', // Erhalten column
        });
        log.info('Link scan completed successfully', data);
      } catch (e: any) {
        log.error(`Link scan failed: ${e?.message || String(e)}`);
      }
    } catch (error) {
      log.error(`Scan error: ${error}`);
    }

    await log.write();
  }
}

// Helper to resolve the base URL for building Buy Offer links
function getBaseUrl(): string {
  return window.location.origin;
}

// Register and run matcher
const inboxMatcher = new InboxMatcher();

// Keep the extension's service worker active from the inbox content script.
// - Connect a long-lived port named 'keepAlive'.
// - Send a lightweight ping every 15s for observability.
// - Auto-reconnect on disconnect (Chrome will force-close ports ~5 minutes after connect).
// - Clean up on page unload.
(function setupInboxKeepAlive() {
  const KEEPALIVE_PORT_NAME = 'keepAlive';
  const PING_INTERVAL_MS = 15_000;
  const RECONNECT_BASE_DELAY_MS = 500;
  const RECONNECT_MAX_DELAY_MS = 30_000;
  const nowTs = () => new Date().toISOString();

  interface KeepAliveWindow extends Window {
    __INBOX_KEEPALIVE_STARTED__?: boolean;
    __INBOX_KEEPALIVE_STOPPING__?: boolean;
    __INBOX_KEEPALIVE_PORT__?: chrome.runtime.Port;
    __INBOX_KEEPALIVE_PING_TIMER__?: number;
    __INBOX_KEEPALIVE_RECONNECT_TIMER__?: number;
    __INBOX_KEEPALIVE_RECONNECT_DELAY__?: number;
  }
  const w = window as unknown as KeepAliveWindow;

  function startPingLoop() {
    if (w.__INBOX_KEEPALIVE_PING_TIMER__) return;
    console.log(`[${nowTs()}][KeepAlive][Inbox] - Ping loop started (${PING_INTERVAL_MS}ms)`);
    w.__INBOX_KEEPALIVE_PING_TIMER__ = window.setInterval(() => {
      try {
        w.__INBOX_KEEPALIVE_PORT__?.postMessage({ type: 'keepAlive.ping', ts: Date.now() });
      } catch {
        // ignore; reconnect logic will handle when port is gone
      }
    }, PING_INTERVAL_MS);
  }

  function stopPingLoop() {
    if (w.__INBOX_KEEPALIVE_PING_TIMER__) {
      clearInterval(w.__INBOX_KEEPALIVE_PING_TIMER__);
      w.__INBOX_KEEPALIVE_PING_TIMER__ = undefined;
      console.log(`[${nowTs()}][KeepAlive][Inbox] - Ping loop stopped`);
    }
  }

  function scheduleReconnect() {
    if (w.__INBOX_KEEPALIVE_STOPPING__) return;

    const delay = w.__INBOX_KEEPALIVE_RECONNECT_DELAY__ ?? RECONNECT_BASE_DELAY_MS;
    if (w.__INBOX_KEEPALIVE_RECONNECT_TIMER__) return; // already scheduled

    console.log(`[${nowTs()}][KeepAlive][Inbox] - Scheduling reconnect in ${delay}ms`);
    w.__INBOX_KEEPALIVE_RECONNECT_TIMER__ = window.setTimeout(() => {
      w.__INBOX_KEEPALIVE_RECONNECT_TIMER__ = undefined;
      connectKeepAlivePort();
    }, delay);

    // exponential backoff with cap
    w.__INBOX_KEEPALIVE_RECONNECT_DELAY__ = Math.min(delay * 2, RECONNECT_MAX_DELAY_MS);
  }

  function connectKeepAlivePort() {
    if (w.__INBOX_KEEPALIVE_STOPPING__) return;
    try {
      const port = chrome.runtime.connect({ name: KEEPALIVE_PORT_NAME });
      w.__INBOX_KEEPALIVE_PORT__ = port;
      w.__INBOX_KEEPALIVE_RECONNECT_DELAY__ = RECONNECT_BASE_DELAY_MS; // reset backoff

      console.log(`[${nowTs()}][KeepAlive][Inbox] - Port connected`);
      startPingLoop();

      port.onDisconnect.addListener(() => {
        console.warn(`[${nowTs()}][KeepAlive][Inbox] - Port disconnected`);
        stopPingLoop();
        w.__INBOX_KEEPALIVE_PORT__ = undefined;
        if (!w.__INBOX_KEEPALIVE_STOPPING__) {
          scheduleReconnect();
        }
      });

      // Optional: handle messages from background if needed
      port.onMessage.addListener(_msg => {
        // no-op
      });
    } catch {
      console.warn(`[${nowTs()}][KeepAlive][Inbox] - Connect failed; scheduling reconnect`);
      scheduleReconnect();
    }
  }

  function startInboxKeepAlive() {
    if (w.__INBOX_KEEPALIVE_STARTED__) return;
    w.__INBOX_KEEPALIVE_STARTED__ = true;
    w.__INBOX_KEEPALIVE_STOPPING__ = false;
    console.log(`[${nowTs()}][KeepAlive][Inbox] - Initializing keep-alive (ping every ${PING_INTERVAL_MS}ms)`);
    connectKeepAlivePort();
  }

  function stopInboxKeepAlive() {
    w.__INBOX_KEEPALIVE_STOPPING__ = true;
    console.log(`[${nowTs()}][KeepAlive][Inbox] - Stopping keep-alive`);
    try {
      w.__INBOX_KEEPALIVE_PORT__?.disconnect();
    } catch {}
    w.__INBOX_KEEPALIVE_PORT__ = undefined;
    stopPingLoop();
    if (w.__INBOX_KEEPALIVE_RECONNECT_TIMER__) {
      clearTimeout(w.__INBOX_KEEPALIVE_RECONNECT_TIMER__);
      w.__INBOX_KEEPALIVE_RECONNECT_TIMER__ = undefined;
    }
    w.__INBOX_KEEPALIVE_RECONNECT_DELAY__ = undefined;
    w.__INBOX_KEEPALIVE_STARTED__ = false;
  }

  // start now and cleanup on unload
  startInboxKeepAlive();
  window.addEventListener('beforeunload', stopInboxKeepAlive);
})();

function checkAndRun() {
  const currentUrl = window.location.href;
  const matches = inboxMatcher.urlPatterns.some(pattern => {
    const regex = new RegExp(pattern.replace(/\*/g, '.*'));
    return regex.test(currentUrl);
  });

  if (matches) {
    console.log('[InboxMatcher] URL matches, registering matcher');

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => inboxMatcher.run());
    } else {
      setTimeout(() => inboxMatcher.run(), 0);
    }
  }
}

// Check on initial load
checkAndRun();

/**
 * Inbox Executor - Extracts links with timestamps and returns them
 */
export async function executeInboxWorkflow(
  context: ExecutionContext,
  selectors: InboxSelectors,
): Promise<ExecutionResult> {
  const log = new Log(context.matcherId);
  log.info(`Extracting inbox links`);
  const startTime = Date.now();

  try {
    // Parse links from the page
    const links = await parseInboxLinks(selectors);
    log.info(`Found ${links.length} total links`);

    async function parseInboxLinks(
      selectors: InboxSelectors,
    ): Promise<Array<{ id: string; href: string; requestTimestamp: number; isLead: boolean }>> {
      const links: Array<{ id: string; href: string; requestTimestamp: number; isLead: boolean }> = [];
      const rows = document.querySelectorAll(selectors.rows);

      for (const row of rows) {
        // Find the title link in this row
        const anchor = row.querySelector(selectors.titleLinks) as HTMLAnchorElement;
        if (!anchor || !anchor.href) continue;

        const title = anchor.textContent?.trim() || '';

        // Use FlowUtils to parse ID from title
        let id: string;
        try {
          id = FlowUtils.parseIDFromTitle(title);
        } catch (e) {
          log.warn(`Failed to parse ID from title: ${title}`);
          continue;
        }

        // Get request timestamp from Erhalten column (3rd column)
        const timestampCell = row.querySelector(selectors.requestTimestampElement) as HTMLElement;
        if (!timestampCell) {
          log.warn(`No timestamp cell found for row with title: ${title}`);
          continue;
        }

        const timestampText = timestampCell.textContent?.trim() || '';
        let requestTimestamp: number;
        try {
          requestTimestamp = FlowUtils.parseDateToEpoch(timestampText);
        } catch (e) {
          log.warn(`Failed to parse timestamp: ${timestampText}`);
          continue;
        }

        const isLead = FlowUtils.isLead(title);

        links.push({
          id: isLead ? `${id}-pdf` : id,
          href: anchor.href,
          requestTimestamp,
          isLead,
        });
      }

      return links;
    }

    // Sort links by requestTimestamp in descending order (newest first)
    links.sort((a, b) => b.requestTimestamp - a.requestTimestamp);
    log.info(`Sorted ${links.length} links by timestamp (newest first)`);

    let openedCount = 0;
    let skippedCount = 0;

    const maxLinks = context.config.inboxMaxLinksPerScan;

    // Process up to maxLinks concurrently for minimal latency
    const linksToProcess = links.slice(0, maxLinks);
    log.info(`Processing up to ${linksToProcess.length} links from ${links.length} total (newest first)`);

    const tasks = linksToProcess.map(async function (link) {
      // Create flow-specific log for this link
      const flowLog = Log.withFlow(MATCHER_IDS.INBOX, link.id);

      // Determine target URL: if configured, go directly to Buy Offer for non-leads
      const targetHref = (() => {
        try {
          if (!link.isLead && context.config.inboxBuysImmediately) {
            const base = getBaseUrl();
            return `${base.replace(/\/+$/, '')}/buy_now/id/${link.id}.html`;
          }
        } catch {
          // fall back to original link on any error
        }
        return link.href;
      })();

      try {
        if (!context.dryRun) {
          const id = link.id;
          const { existed } = await BackgroundUtils.startInboxFlowAndOpen({
            id,
            requestTimestamp: link.requestTimestamp,
            url: targetHref,
          });

          if (existed) {
            flowLog.info(`Flow already exists, skipping`);
            skippedCount++;
          } else {
            flowLog.info(`Processing new inbox flow: ${id}`);
            openedCount++;
          }
        } else {
          flowLog.debug('Dry run: Would start flow');
        }

        await flowLog.write();
      } catch (error) {
        const errorMsg = `Error processing link: ${error}`;
        flowLog.error(errorMsg);
        await flowLog.write();
      }
    });

    await Promise.allSettled(tasks);
    await log.write();

    return {
      success: true,
      matcherId: context.matcherId,
      executorName: 'inbox',
      data: {
        links, // Return links with timestamps to background for processing
      },
      telemetry: {
        startTime,
        endTime: Date.now(),
        errors: [],
      },
    };
  } catch (error) {
    log.error(`Fatal error: ${error}`, { stack: error instanceof Error ? error.stack : undefined });
    await log.write();

    return {
      success: false,
      matcherId: context.matcherId,
      executorName: 'inbox',
      error: error instanceof Error ? error.message : 'Unknown error',
      telemetry: {
        startTime,
        endTime: Date.now(),
        errors: [error as Error],
      },
    };
  }
}
