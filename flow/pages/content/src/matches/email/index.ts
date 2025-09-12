import {
  registerMatcher,
  sendBackgroundCommand,
  Log,
  waitForSelector,
  clickWithVerification,
  safeNavigate,
  random,
  sleep,
} from '@src/lib';
import type { Matcher } from '@src/types';
import type { ExecutionContext, ExecutionResult, EmailSelectors } from '@src/types';

/**
 * Email Matcher - Detects Outlook email pages and triggers email processing
 */
class EmailMatcher implements Matcher {
  id = 'email-matcher';
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
    const log = new Log('email-matcher');
    log.push('Email matcher activated');

    try {
      // Check if extension is enabled
      const enabledResponse = await chrome.runtime.sendMessage({ action: 'isEnabled' });
      if (!enabledResponse) {
        log.push('Extension disabled').write();
        return;
      }

      // Get configuration
      const config = await chrome.runtime.sendMessage({ action: 'config' });
      if (!config?.emailMode) {
        log.push('Email mode disabled').write();
        return;
      }

      log.push('Triggering email executor').write();

      // Send command to background to run email executor
      const response = await sendBackgroundCommand('email.openUnreadAndClickLink', {
        selectors: {
          unreadEmail: '[aria-label^="Ungelesen HanseMerkur AuktionsPlattform"]',
          emailBody: '#x_body a',
          markAsReadButton: 'span',
        },
      });

      if (response.success) {
        log.push('Email executor triggered successfully').write();
      } else {
        log.push(`Email executor failed: ${response.error}`).write();
      }
    } catch (error) {
      log.push(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`).write();
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
      // Small delay to ensure everything is ready
      setTimeout(() => emailMatcher.run(), 1000);
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

export default emailMatcher;

/**
 * Email Executor - Processes unread emails by opening them and clicking links
 */
export async function executeEmailWorkflow(
  context: ExecutionContext,
  selectors: EmailSelectors,
): Promise<ExecutionResult> {
  const log = new Log('email-executor');
  const startTime = Date.now();
  const errors: Error[] = [];
  let processedCount = 0;
  const visitedUrls: Record<string, boolean> = {};

  try {
    log.push(`Starting email workflow for tab ${context.tabId}`);

    // Get configuration
    const config = context.config || {};
    const refreshMin = config.emailRefreshMin || 30;
    const refreshMax = config.emailRefreshMax || 60;

    // Setup refresh timer
    const randomRefreshSeconds = random(refreshMin, refreshMax);
    log.push(`Will refresh in ${randomRefreshSeconds}s`);

    setTimeout(() => {
      if (!context.dryRun) {
        window.location.reload();
      } else {
        log.push('Dry run: Would reload page').write();
      }
    }, randomRefreshSeconds * 1000);

    // Process emails
    await processEmails();

    async function processEmails(): Promise<void> {
      try {
        // Find all unread emails
        const emails = document.querySelectorAll(selectors.unreadEmail);
        log.push(`Found ${emails.length} unread emails`);

        if (emails.length === 0) {
          // Wait and check again
          await sleep(500);
          const retriedEmails = document.querySelectorAll(selectors.unreadEmail);
          if (retriedEmails.length === 0) {
            log.push('No unread emails found after retry').write();
            return;
          }
        }

        // Process each email
        for (const email of emails) {
          if (!(email instanceof HTMLElement)) continue;

          log.push(`Processing email ${processedCount + 1}`);

          // Click to open the email
          if (context.dryRun) {
            log.push('Dry run: Would click email');
          } else {
            await clickWithVerification(email, { delay: 100 });
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

              // Check if we've already visited this URL
              if (!visitedUrls[href]) {
                visitedUrls[href] = true;

                // Mark email as read
                await markEmailAsRead(selectors.markAsReadButton);

                log.push(`Opening link: ${href}`);

                if (!context.dryRun) {
                  // Open link in new managed tab
                  await sendBackgroundCommand('tab.manage', {
                    action: 'open',
                    url: href,
                  });
                } else {
                  log.push('Dry run: Would open link in new tab');
                }

                processedCount++;
              } else {
                log.push('Link already visited, skipping');
              }
            }
          } catch (error) {
            log.push(`Error processing email content: ${error}`);
            errors.push(error as Error);
          }

          // Small delay between emails
          await sleep(500);
        }
      } catch (error) {
        log.push(`Error in email processing: ${error}`);
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
            await clickWithVerification(markAsReadBtn, { delay: 100 });
            log.push('Marked email as read');
          } else {
            log.push('Dry run: Would mark email as read');
          }
        }
      } catch (error) {
        log.push(`Error marking email as read: ${error}`);
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
    log.push(`Fatal error: ${error}`).write();
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
