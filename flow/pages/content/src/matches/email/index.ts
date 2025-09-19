import {
  registerMatcher,
  sendBackgroundCommand,
  waitForSelector,
  clickWithVerification,
  safeNavigate,
  random,
  sleep,
} from '@src/lib';
import type { CommandResponse, ExecutionConfig, Matcher } from '@extension/types';
import { MATCHER_IDS } from '@extension/types';
import type { ExecutionContext, ExecutionResult, EmailSelectors } from '@extension/types';
import { FlowUtils, Log } from '@extension/shared';

/**
 * Email Matcher - Detects Outlook email pages and triggers email processing
 */
class EmailMatcher implements Matcher {
  id = MATCHER_IDS.EMAIL;
  name = 'Email Clicking Workflow';
  enabled = true;
  priority = 10;

  urlPatterns = ['https://outlook.office.com/mail/*', 'https://outlook.office.com.mcas.ms/mail/*'];

  domPreconditions = [
    {
      selector: '[aria-label*="HanseMerkur"]',
      shouldExist: true,
      timeout: 5000,
    },
  ];

  async run(): Promise<void> {
    // Email doesn't have flowId initially
    const log = new Log(MATCHER_IDS.EMAIL);
    log.info('Email matcher activated');

    try {
      // Get configuration and check if enabled
      const configResponse = (await sendBackgroundCommand('extension.getConfig', {})) as CommandResponse<{
        config: ExecutionConfig;
        enabled: boolean;
      }>;

      const result = configResponse.data;
      if (!result) {
        log.warn('No configuration found');
        await log.write();
        return;
      }

      if (!result.enabled) {
        log.info('Extension disabled');
        await log.write();
        return;
      }

      if (!result.config.emailMode) {
        log.info('Email mode disabled');
        await log.write();
        return;
      }

      log.info('Triggering email executor');
      await log.write();

      // Send command to background to run email executor
      const response = await sendBackgroundCommand('email.openUnreadAndClickLink', {
        selectors: {
          unreadEmail: '[aria-label^="Ungelesen HanseMerkur AuktionsPlattform"]',
          emailBody: '#x_body a',
          markAsReadButton: 'span',
        },
      });

      if (response.success) {
        log.info('Email executor triggered successfully');
        await log.write();
      } else {
        log.error(`Email executor failed: ${response.error}`);
        await log.write();
      }
    } catch (error) {
      log.error(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, { error });
      await log.write();
      console.error('[EmailMatcher] Error:', error);
    }
  }
}

// Register and run the matcher when content script loads
const emailMatcher = new EmailMatcher();

// Check if current URL matches
function checkAndRun() {
  const currentUrl = window.location.href;
  const matches = emailMatcher.urlPatterns.some(pattern => {
    // Convert simple wildcard pattern to regex
    const regex = new RegExp(pattern.replace(/\*/g, '.*'));
    return regex.test(currentUrl);
  });

  if (matches) {
    console.log('[EmailMatcher] URL matches, registering matcher');
    registerMatcher(emailMatcher);

    // Run the matcher after DOM is ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => emailMatcher.run());
    } else {
      setTimeout(() => emailMatcher.run(), 0);
    }
  }
}

// Check on initial load
checkAndRun();

// Also check on navigation changes (for SPAs)
let lastUrl = window.location.href;
new MutationObserver(() => {
  const currentUrl = window.location.href;
  if (currentUrl !== lastUrl) {
    lastUrl = currentUrl;
    checkAndRun();
  }
}).observe(document, { subtree: true, childList: true });

/**
 * Email Executor - Processes unread emails by opening them and clicking links
 */
export async function executeEmailWorkflow(
  context: ExecutionContext,
  selectors: EmailSelectors,
): Promise<ExecutionResult> {
  // Email executor doesn't have flowId initially
  const log = new Log(context.matcherId);
  log.info(`Starting email workflow for tab ${context.tabId}`);
  const startTime = Date.now();
  const errors: Error[] = [];
  let processedCount = 0;
  const visitedUrls: Record<string, boolean> = {};

  try {
    // Get configuration
    const config = context.config || {};
    const refreshMin = config.emailRefreshMin || 30;
    const refreshMax = config.emailRefreshMax || 60;

    // Setup refresh timer
    const randomRefreshSeconds = random(refreshMin, refreshMax);
    log.info(`Will refresh in ${randomRefreshSeconds}s`);

    setTimeout(async () => {
      if (!context.dryRun) {
        window.location.reload();
      } else {
        log.debug('Dry run: Would reload page');
        await log.write();
      }
    }, randomRefreshSeconds * 1000);

    // Process emails
    await processEmails();

    async function processEmails(): Promise<void> {
      try {
        // Find all unread emails
        const emails = document.querySelectorAll(selectors.unreadEmail);
        log.info(`Found ${emails.length} unread emails`);

        if (emails.length === 0) {
          // Wait and check again
          await sleep(500);
          const retriedEmails = document.querySelectorAll(selectors.unreadEmail);
          if (retriedEmails.length === 0) {
            log.info('No unread emails found after retry');
            await log.write();
            return;
          }
        }

        // Process each email
        for (const email of emails) {
          if (!(email instanceof HTMLElement)) continue;

          log.info(`Processing email ${processedCount + 1}`);

          // Click to open the email
          if (context.dryRun) {
            log.debug('Dry run: Would click email');
          } else {
            await clickWithVerification(email, {});
          }

          // Wait for email content to load
          await sleep(1000);

          try {
            // Find link in email body
            const linkElement = await waitForSelector(selectors.emailBody, {
              timeout: 3000,
              visible: true,
            });

            if (linkElement instanceof HTMLAnchorElement) {
              const href = linkElement.href;
              const title = linkElement.textContent ?? '';
              let id: string;

              try {
                // Parse ID from path as per requirement
                id = FlowUtils.parseIDFromPath(href);
              } catch (e) {
                const errorMsg = `Failed to parse ID from ${href}: ${e}`;
                log.error(errorMsg);
                continue;
              }

              // Start flow and check if it already exists
              const startFlowResult = await sendBackgroundCommand('extension.startFlow', {
                type: 'email',
                id,
                title,
                href,
              });

              if (startFlowResult.success && startFlowResult.data === true) {
                // Flow already exists, skip this link
                // Create a new log with flowId for this specific email
                const flowLog = Log.withFlow(context.matcherId, id);
                flowLog.info(`Skipping email with existing flow: ${id}`);
                await flowLog.write();
                continue;
              }

              // Create a new log with flowId for this specific email flow
              const flowLog = Log.withFlow(context.matcherId, id);
              flowLog.info(`Processing new email flow`, { href, title });

              // Check if we've already visited this URL
              if (!visitedUrls[href]) {
                visitedUrls[href] = true;

                // Mark email as read
                await markEmailAsRead(selectors.markAsReadButton);

                flowLog.info(`Opening link: ${href}`);

                if (!context.dryRun) {
                  // Open link in new managed tab
                  await sendBackgroundCommand('tab.manage', {
                    action: 'open',
                    url: href,
                  });
                } else {
                  flowLog.debug('Dry run: Would open link in new tab');
                }

                await flowLog.write();
                processedCount++;
              } else {
                flowLog.info('Link already visited, skipping');
                await flowLog.write();
              }
            }
          } catch (error) {
            log.error(`Error processing email content: ${error}`);
            errors.push(error as Error);
          }

          // Small delay between emails
          // await sleep(500);
        }
      } catch (error) {
        log.error(`Error in email processing: ${error}`);
        errors.push(error as Error);
      }
    }

    // Mark email as read
    async function markEmailAsRead(selector: string): Promise<void> {
      try {
        // Find the mark as read button (contains specific text)
        const buttons = Array.from(document.querySelectorAll(selector));
        const markAsReadBtn = buttons.find(btn => btn.textContent?.includes('Gelesen/Ungelesen'));

        if (markAsReadBtn instanceof HTMLElement) {
          if (!context.dryRun) {
            await clickWithVerification(markAsReadBtn, {});
            log.info('Marked email as read');
          } else {
            log.debug('Dry run: Would mark email as read');
          }
        }
      } catch (error) {
        log.warn(`Error marking email as read: ${error}`);
        // Non-critical error, continue
      }
    }

    await log.write();

    return {
      success: true,
      matcherId: context.matcherId,
      executorName: 'email',
      data: {
        processedCount,
        visitedUrls: Object.keys(visitedUrls),
        refreshSeconds: randomRefreshSeconds,
      },
      telemetry: {
        startTime,
        endTime: Date.now(),
        domOperations: processedCount * 3, // Open, read link, mark as read
        networkRequests: processedCount,
        errors,
      },
    };
  } catch (error) {
    log.error(`Fatal error: ${error}`, { stack: error instanceof Error ? error.stack : undefined });
    await log.write();
    console.error('[EmailExecutor] Fatal error:', error);

    return {
      success: false,
      matcherId: context.matcherId,
      executorName: 'email',
      error: error instanceof Error ? error.message : 'Unknown error',
      telemetry: {
        startTime,
        endTime: Date.now(),
        domOperations: processedCount * 3,
        networkRequests: processedCount,
        errors: [...errors, error as Error],
      },
    };
  }
}

// Export for background script to inject
if (typeof window !== 'undefined') {
  (window as any).__emailExecutor = executeEmailWorkflow;
}
