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
import type { ExecutionContext, ExecutionResult, InboxSelectors } from '@extension/types';
import { FlowUtils, Log } from '@extension/shared';

/**
 * Inbox Matcher - Detects Outlook inbox pages and triggers inbox processing
 */
class InboxMatcher implements Matcher {
  id = MATCHER_IDS.INBOX;
  name = 'Inbox Clicking Workflow';
  enabled = true;
  priority = 10;

  urlPatterns = ['https://auktion.hansemerkur.de/my_message_center_inbox.html'];

  domPreconditions = [
    {
      selector: '[aria-label*="HanseMerkur"]',
      shouldExist: true,
      timeout: 5000,
    },
  ];

  async run(): Promise<void> {
    // Inbox doesn't have flowId initially
    const log = new Log(MATCHER_IDS.EMAIL);
    log.info('Inbox matcher activated');

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

      if (!result.config.inboxMode) {
        log.info('Inbox mode disabled');
        await log.write();
        return;
      }

      log.info('Triggering inbox executor');
      await log.write();

      // Send command to background to run inbox executor
      const response = await sendBackgroundCommand('inbox.openMyOfferLink', {
        selectors: {},
      });

      if (response.success) {
        log.info('Inbox executor triggered successfully');
        await log.write();
      } else {
        log.error(`Inbox executor failed: ${response.error}`);
        await log.write();
      }
    } catch (error) {
      log.error(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, { error });
      await log.write();
      console.error('[InboxMatcher] Error:', error);
    }
  }
}

// Register and run the matcher when content script loads
const inboxMatcher = new InboxMatcher();

// Check if current URL matches
function checkAndRun() {
  const currentUrl = window.location.href;
  const matches = inboxMatcher.urlPatterns.some(pattern => {
    // Convert simple wildcard pattern to regex
    const regex = new RegExp(pattern.replace(/\*/g, '.*'));
    return regex.test(currentUrl);
  });

  if (matches) {
    console.log('[InboxMatcher] URL matches, registering matcher');
    registerMatcher(inboxMatcher);

    // Run the matcher after DOM is ready
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
 * Inbox Executor - Processes unread inboxs by opening them and clicking links
 */
export async function executeInboxWorkflow(
  context: ExecutionContext,
  selectors: InboxSelectors,
): Promise<ExecutionResult> {
  // Inbox executor doesn't have flowId initially
  const log = new Log(context.matcherId);
  log.info(`Starting inbox workflow for tab ${context.tabId}`);
  const startTime = Date.now();
  const errors: Error[] = [];

  try {
    // Get configuration
    const config = context.config || {};

    // Process inboxs
    await processInbox();

    async function processInbox(): Promise<void> {
      // todo
    }

    // Mark inbox as read

    await log.write();

    return {
      success: true,
      matcherId: context.matcherId,
      executorName: 'inbox',
      data: {},
      telemetry: {
        startTime,
        endTime: Date.now(),
        domOperations: 0,
        networkRequests: 0,
        errors,
      },
    };
  } catch (error) {
    log.error(`Fatal error: ${error}`, { stack: error instanceof Error ? error.stack : undefined });
    await log.write();
    console.error('[InboxExecutor] Fatal error:', error);

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
        errors: [...errors, error as Error],
      },
    };
  }
}

// Export for background script to inject
if (typeof window !== 'undefined') {
  (window as any).__inboxExecutor = executeInboxWorkflow;
}
