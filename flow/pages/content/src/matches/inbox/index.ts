import { FlowUtils, Log } from '@extension/shared';
import { MATCHER_IDS } from '@extension/types';
import { sendBackgroundCommand, TabManager } from '@extension/shared';
import { registerMatcher, sleep } from '@src/lib';
import type {
  CommandResponse,
  ExecutionConfig,
  Matcher,
  ExecutionContext,
  ExecutionResult,
  InboxSelectors,
} from '@extension/types';

/**
 * Inbox Matcher - Monitors HanseMerkur inbox for new messages
 */
class InboxMatcher implements Matcher {
  id = MATCHER_IDS.INBOX;
  name = 'Inbox Link Monitor';
  enabled = true;
  priority = 10;

  urlPatterns = ['http://localhost:8082/inbox.html', 'https://auktion.hansemerkur.de/my_message_center_inbox.html'];

  domPreconditions = [
    {
      selector: 'table',
      shouldExist: true,
      timeout: 5000,
    },
  ];

  private schedulerInterval: NodeJS.Timeout | null = null;

  async run(): Promise<void> {
    const log = new Log(MATCHER_IDS.INBOX);
    log.info('Inbox matcher activated');

    try {
      // Get configuration
      const configResponse = (await sendBackgroundCommand('extension.getConfig', {})) as CommandResponse<{
        config: ExecutionConfig;
        enabled: boolean;
      }>;

      const result = configResponse.data;
      if (!result?.enabled || !result.config.inboxMode) {
        log.info('Inbox monitoring disabled');
        await log.write();
        return;
      }

      const config = result.config;

      // Check if we need to handle a scheduled reload
      const shouldScanAfterReload = sessionStorage.getItem('inbox_scan_after_reload') === '1';
      if (shouldScanAfterReload) {
        sessionStorage.removeItem('inbox_scan_after_reload');
        log.info('Performing post-reload scan');

        // Wait for configured delay
        await sleep(config.inboxPostReloadDelayMs || 2000);

        // Trigger scan
        await this.scanAndOpenLinks();
      } else {
        // Initial scan on page load
        await this.scanAndOpenLinks();
      }

      // Start reload scheduler
      this.startReloadScheduler(config);

      await log.write();
    } catch (error) {
      log.error(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, { error });
      await log.write();
      console.error('[InboxMatcher] Error:', error);
    }
  }

  private startReloadScheduler(config: ExecutionConfig): void {
    const reloadSeconds = config.inboxReloadSeconds || [0, 5];
    const log = new Log(MATCHER_IDS.INBOX);

    // Clear any existing scheduler
    if (this.schedulerInterval) {
      clearInterval(this.schedulerInterval);
    }

    // Check every second
    this.schedulerInterval = setInterval(() => {
      const now = new Date();
      const currentSecond = now.getSeconds();

      if (reloadSeconds.includes(currentSecond)) {
        log.info(`Scheduled reload at second ${currentSecond}`);

        // Mark for post-reload scan
        sessionStorage.setItem('inbox_scan_after_reload', '1');

        // Reload the page
        window.location.reload();
      }
    }, 1000);

    log.info(`Reload scheduler started for seconds: ${reloadSeconds.join(', ')}`);
  }

  private async scanAndOpenLinks(): Promise<void> {
    const log = new Log(MATCHER_IDS.INBOX);

    try {
      log.info('Scanning for new links');

      // Just send the command to background - all processing happens there
      const response = await sendBackgroundCommand('inbox.openMyOfferLink', {
        selectors: {
          rows: 'table.browse_list tr',
          titleLinks: 'table.browse_list tr td:nth-child(3) a',
          requestTimestampElement: 'td:nth-child(4)', // Erhalten column
        },
      });

      if (response.success) {
        log.info('Link scan completed successfully', response.data);
      } else {
        log.error(`Link scan failed: ${response.error}`);
      }
    } catch (error) {
      log.error(`Scan error: ${error}`);
    }

    await log.write();
  }
}

// Register and run matcher
const inboxMatcher = new InboxMatcher();

function checkAndRun() {
  const currentUrl = window.location.href;
  const matches = inboxMatcher.urlPatterns.some(pattern => {
    const regex = new RegExp(pattern.replace(/\*/g, '.*'));
    return regex.test(currentUrl);
  });

  if (matches) {
    console.log('[InboxMatcher] URL matches, registering matcher');
    registerMatcher(inboxMatcher);

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
  log.info(`Extracting inbox links for tab ${context.tabId}`);
  const startTime = Date.now();
  const visitedUrls: Record<string, boolean> = {}; // local url tracking for this scan
  const tabManager = TabManager.getInstance();

  try {
    // Parse links from the page
    const links = await parseInboxLinks(selectors);
    log.info(`Found ${links.length} total links`);

    async function parseInboxLinks(
      selectors: InboxSelectors,
    ): Promise<Array<{ id: string; href: string; title: string; requestTimestamp: number }>> {
      const links: Array<{ id: string; href: string; title: string; requestTimestamp: number }> = [];
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

        links.push({
          id,
          href: anchor.href,
          title,
          requestTimestamp,
        });
      }

      return links;
    }

    // Sort links by requestTimestamp in descending order (newest first)
    links.sort((a, b) => b.requestTimestamp - a.requestTimestamp);
    log.info(`Sorted ${links.length} links by timestamp (newest first)`);

    let openedCount = 0;
    let skippedCount = 0;
    const errors: string[] = [];

    const maxLinks = context.config?.inboxMaxLinksPerScan || 10;
    const interOpenDelay = context.config?.inboxInterOpenDelayMs || 400;

    const linksToProcess = links.slice(0, maxLinks);
    log.info(`Processing up to ${linksToProcess.length} links from ${links.length} total (newest first)`);

    for (const link of linksToProcess) {
      // Create flow-specific log for this link
      const flowLog = Log.withFlow(MATCHER_IDS.INBOX, link.id);

      try {
        if (!context.dryRun) {
          // Start flow for this link
          const startFlowResponse = await sendBackgroundCommand('extension.startFlow', {
            type: 'inbox',
            id: link.id,
            title: link.title,
            requestTimestamp: link.requestTimestamp,
          });

          if (startFlowResponse.success && startFlowResponse.data === true) {
            // Flow already exists - this is our duplicate detection
            flowLog.info(`Flow already exists, skipping`);
            skippedCount++;
            await flowLog.write();
            continue;
          }

          flowLog.info(`Processing new inbox flow: ${link.title}`, { link: link.title });

          // Check if we've already visited this URL
          if (!visitedUrls[link.href]) {
            visitedUrls[link.href] = true;

            flowLog.info(`Opening link: ${link.href}`);

            if (!context.dryRun) {
              tabManager.openTab(link.href, link.id);
            } else {
              flowLog.debug(`Dry run: Would open link ${link.href} in new tab`);
            }
          } else {
            flowLog.info('Link already visited, skipping');
          }

          // Flow created successfully - no need for separate tracking
          openedCount++;
          flowLog.info(`Flow started successfully`);
        } else {
          flowLog.debug('Dry run: Would start flow');
        }

        await flowLog.write();

        // Delay between processing
        if (interOpenDelay > 0 && linksToProcess.indexOf(link) < linksToProcess.length - 1) {
          await new Promise(resolve => setTimeout(resolve, interOpenDelay));
        }
      } catch (error) {
        const errorMsg = `Error processing link: ${error}`;
        flowLog.error(errorMsg);
        await flowLog.write();
        errors.push(errorMsg);
      }
    }

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
        domOperations: links.length,
        networkRequests: 0,
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
        domOperations: 0,
        networkRequests: 0,
        errors: [error as Error],
      },
    };
  }
}

// Export for background script
if (typeof window !== 'undefined') {
  (window as any).__inboxExecutor = executeInboxWorkflow;
}
