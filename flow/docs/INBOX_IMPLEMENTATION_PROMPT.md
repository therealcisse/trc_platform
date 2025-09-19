# Inbox Link Monitoring Implementation Prompt

## Context and Requirements

You are implementing an inbox monitoring feature for a Chrome extension that tracks and opens new auction links on the HanseMerkur platform. The feature must:

1. **Monitor the inbox page** at `https://auktion.hansemerkur.de/my_message_center_inbox.html`
2. **Track new auction messages** that appear during the first 10 seconds of every minute
3. **Open only unopened links** while maintaining state across page reloads
4. **Reload the page strategically** during the first 10 seconds to catch all new items
5. **Integrate seamlessly** with the existing extension architecture

## Implementation Tasks

### Task 1: Update Type Definitions

Update the type definitions to support inbox monitoring configuration and selectors.

**File: `/Users/therealcisse/Developer/trc_platform/flow/packages/types/lib/app/types.ts`**

1. Update `ExecutionConfig` interface to add inbox-specific configuration:
```typescript
export interface ExecutionConfig {
  // ... existing fields ...
  
  // Inbox mode configuration
  inboxMode?: boolean;
  inboxReloadSeconds?: number[]; // [0, 5] means reload at 0 and 5 seconds of each minute
  inboxPostReloadDelayMs?: number; // Delay after reload before scanning
  inboxMaxLinksPerScan?: number; // Max links to open per scan
  inboxInterOpenDelayMs?: number; // Delay between opening links
}
```

2. Update `InboxSelectors` interface:
```typescript
export interface InboxSelectors {
  titleLinks?: string; // Selector for title column links
  messageRow?: string; // Selector for message rows
  requestTimestampElement?: string; // Selector for request timestamp (Erhalten column)
}
```
3. Update `InboxCommand` interface:
```typescript
export interface InboxCommand {
  selectors?: InboxSelectors;
  forceRefresh?: boolean; // Force immediate refresh
}
```

### Task 2: Update Storage Validation

**File: `/Users/therealcisse/Developer/trc_platform/flow/packages/storage/lib/validation/storage.ts`**

Add validation for new inbox configuration fields:
```typescript
export const ExecutionConfigSchema = z.object({
  // ... existing fields ...
  
  inboxMode: z.boolean().optional(),
  inboxReloadSeconds: z.array(z.number()).optional().default([0, 5]),
  inboxPostReloadDelayMs: z.number().optional().default(2000),
  inboxMaxLinksPerScan: z.number().optional().default(10),
  inboxInterOpenDelayMs: z.number().optional().default(400),
});
```

### Task 3: Flow Management (No Separate Storage Needed)

Since the flow system already tracks processed inbox messages, we don't need a separate storage service. The flow system acts as our persistence layer:

- `extension.startFlow` returns `true` if a flow already exists (duplicate prevention)
- Flows are persisted in chrome.storage automatically
- Each flow has a unique ID, timestamp, and source type

No additional implementation needed for this task.

### Task 3: Implement Inbox Content Script (Minimal)

**File: `/Users/therealcisse/Developer/trc_platform/flow/pages/content/src/matches/inbox/index.ts`**

Replace the existing skeleton with a minimal implementation that just collects links and sends them to background:

```typescript
import {
  registerMatcher,
  sendBackgroundCommand,
  sleep,
} from '@src/lib';
import type { CommandResponse, ExecutionConfig, Matcher } from '@extension/types';
import { MATCHER_IDS } from '@extension/types';
import type { ExecutionContext, ExecutionResult, InboxSelectors } from '@extension/types';
import { FlowUtils, Log } from '@extension/shared';

/**
 * Inbox Matcher - Monitors HanseMerkur inbox for new messages
 */
class InboxMatcher implements Matcher {
  id = MATCHER_IDS.INBOX;
  name = 'Inbox Link Monitor';
  enabled = true;
  priority = 10;

  urlPatterns = [
    'https://auktion.hansemerkur.de/my_message_center_inbox.html'
  ];

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
          titleLinks: 'table a[href*="show_message"]',
          messageRow: 'tr',
          requestTimestampElement: 'td:nth-child(3)', // Erhalten column
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

  try {
    // Parse links from the page
    const links = await parseInboxLinks(selectors);
    log.info(`Found ${links.length} total links`);

    async function parseInboxLinks(selectors: InboxSelectors): Promise<Array<{id: string, href: string, title: string, requestTimestamp: number}>> {
      const links: Array<{id: string, href: string, title: string, requestTimestamp: number}> = [];
      const rows = document.querySelectorAll('tr');
      
      for (const row of rows) {
        // Find the title link in this row
        const anchor = row.querySelector<HTMLAnchorElement>(selectors.titleLinks || 'a[href*="show_message"]');
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
        const timestampCell = row.querySelector<HTMLElement>('td:nth-child(3)');
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
```

### Task 4: Update Background Command Handler (Process Everything in Background)

**File: `/Users/therealcisse/Developer/trc_platform/flow/chrome-extension/src/background/commands/inbox.ts`**

Implement the main processing logic in the background script:

```typescript
import type {
  InboxCommand,
  CommandResponse,
  ExecutionContext
} from '@extension/types';
import type { MessageHandler } from '@extension/types';
import { ConfigService, Log, sendBackgroundCommand } from '@extension/shared';
import { MATCHER_IDS } from '@extension/types';

/**
 * Main inbox command handler - processes all links in background
 */
export const inboxCommandHandler: MessageHandler<'inbox.openMyOfferLink'> = async (
  payload: InboxCommand,
  sender: chrome.runtime.MessageSender
): Promise<CommandResponse> => {
  console.log('[Background] Inbox command received from tab:', sender.tab?.id);
  const log = new Log(MATCHER_IDS.INBOX);

  try {
    if (!sender.tab?.id) {
      throw new Error('No tab ID in sender');
    }

    const tabId = sender.tab.id;

    const [config, enabled] = await Promise.all([
      ConfigService.getConfig(),
      ConfigService.isEnabled()
    ]);

    if (!enabled || !config.inboxMode) {
      return {
        success: false,
        error: 'Inbox mode is disabled',
        requestId: `inbox-${Date.now()}`
      };
    }

    const context: Record<string, any> = {
      tabId,
      url: sender.tab.url || '',
      matcherId: MATCHER_IDS.INBOX,
      config,
      timeout: 30000,
    };

    // Execute script to extract links from the page
    const result = await chrome.scripting.executeScript({
      target: { tabId },
      func: async (contextJson: string, selectorsJson: string) => {
        const context = JSON.parse(contextJson);
        const selectors = JSON.parse(selectorsJson);

        if (typeof (window as any).__inboxExecutor === 'function') {
          return await (window as any).__inboxExecutor(context, selectors);
        }

        return {
          success: false,
          error: 'Inbox executor not loaded',
          matcherId: context.matcherId,
          executorName: 'inbox'
        };
      },
      args: [
        JSON.stringify(context),
        JSON.stringify(payload.selectors || {})
      ]
    });

    const executionResult = result[0]?.result;

    if (!executionResult || !executionResult.success) {
      throw new Error(executionResult?.error || 'No result from inbox executor');
    }

    // Process the links in the background
    const links = executionResult.data?.links || [];
    log.info(`Processing ${links.length} links from inbox`);

    let openedCount = 0;
    let skippedCount = 0;
    const errors: string[] = [];

    const dryRun = false;
    const maxLinks = config.inboxMaxLinksPerScan || 10;
    const interOpenDelay = config.inboxInterOpenDelayMs || 400;

    // Process links up to the limit
    // The flow system will handle duplicate detection
    const linksToProcess = links.slice(0, maxLinks);
    log.info(`Processing up to ${linksToProcess.length} links from ${links.length} total`);
    
    for (const link of linksToProcess) {
      // Create flow-specific log for this link
      const flowLog = Log.withFlow(MATCHER_IDS.INBOX, link.id);
      
      try {
        flowLog.info(`Processing inbox message: ${link.title}`, { 
          href: link.href, 
          requestTimestamp: link.requestTimestamp 
        });

        if (!dryRun) {
          // Start flow for this link
          const startFlowResponse = await sendBackgroundCommand('extension.startFlow', {
            type: 'inbox',
            id: link.id,
            title: link.title,
            requestTimestamp: link.requestTimestamp,
            href: link.href,
          });

          if (startFlowResponse.success && startFlowResponse.data === true) {
            // Flow already exists - this is our duplicate detection
            flowLog.info(`Flow already exists, skipping`);
            skippedCount++;
            await flowLog.write();
            continue;
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

    const resultData = {
      openedCount,
      skippedCount,
      totalFound: links.length,
      errors
    };

    console.log('[Background] Inbox processing complete:', resultData);

    return {
      success: true,
      data: resultData,
      requestId: `inbox-${Date.now()}`
    };

  } catch (error) {
    console.error('[Background] Error handling inbox command:', error);
    log.error(`Fatal error: ${error}`);
    await log.write();

    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
      requestId: `inbox-${Date.now()}`
    };
  }
};

// Register the handler in background.ts
export function registerInboxHandlers(registry: any) {
  registry.register('inbox.openMyOfferLink', inboxCommandHandler);
}
```

### Task 5: Update Popup Component

**File: `/Users/therealcisse/Developer/trc_platform/flow/pages/popup/src/Popup.tsx`**

Add inbox configuration section to the popup (after the Email section):

```typescript
// Add this after the existing configuration sections (around line 250)

{/* Inbox Configuration */}
<div className="border-b pb-3">
  <h3 className="text-sm font-semibold mb-2">Inbox Monitor</h3>
  
  <div className="space-y-2">
    <div className="flex items-center justify-between">
      <span className="text-xs text-gray-600">Inbox Mode</span>
      <Switch
        checked={config.inboxMode || false}
        onChange={(checked) => updateConfig({ inboxMode: checked })}
        size="small"
      />
    </div>
    
    {config.inboxMode && (
      <>
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-600">Reload Seconds</span>
          <input
            type="text"
            value={(config.inboxReloadSeconds || [0, 5]).join(', ')}
            onChange={(e) => {
              const seconds = e.target.value
                .split(',')
                .map(s => parseInt(s.trim()))
                .filter(n => !isNaN(n) && n >= 0 && n < 60);
              updateConfig({ inboxReloadSeconds: seconds });
            }}
            className="w-20 px-2 py-1 text-xs border rounded"
            placeholder="0, 5"
          />
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-600">Max Links</span>
          <input
            type="number"
            value={config.inboxMaxLinksPerScan || 10}
            onChange={(e) => updateConfig({ 
              inboxMaxLinksPerScan: parseInt(e.target.value) || 10 
            })}
            className="w-16 px-2 py-1 text-xs border rounded"
            min="1"
            max="50"
          />
        </div>
        
      </>
    )}
  </div>
</div>
```

### Task 6: Add Background Command Types

Update the BackgroundCommands interface in types.ts to include the inbox command:

```typescript
export interface BackgroundCommands {
  // ... existing commands ...
  
  'inbox.openMyOfferLink': InboxCommand;
}
```

### Task 7: Testing Plan

1. **Unit Tests**: Test flow creation and duplicate detection
2. **Integration Tests**: Test the full flow from detection to flow creation
3. **Manual Testing**:
   - Enable dry run mode
   - Monitor console logs
   - Verify reload timing at minute boundaries
   - Check that opened links are not reopened
   - Test storage persistence across browser restarts

### Task 8: Configuration Defaults

Add sensible defaults to the ConfigService:

```typescript
const DEFAULT_INBOX_CONFIG = {
  inboxMode: false,
  inboxReloadSeconds: [0, 5], // Reload at 0 and 5 seconds
  inboxPostReloadDelayMs: 2000, // 2 second delay after reload
  inboxMaxLinksPerScan: 10, // Open max 10 links per scan
  inboxInterOpenDelayMs: 400, // 400ms between opens
};
```

## Implementation Order

1. **Phase 1**: Update type definitions and storage validation
2. **Phase 2**: Update content script with link extraction
3. **Phase 3**: Update background command handlers with flow creation
4. **Phase 4**: Add popup configuration UI
5. **Phase 5**: Implement reload scheduler
6. **Phase 6**: Test and refine

## Key Design Decisions

1. **Flow-based Duplicate Prevention**: Rely on flow system's built-in duplicate detection
2. **No Separate State Management**: Flows serve as the single source of truth
3. **ID Parsing**: Use FlowUtils.parseIDFromTitle for consistent ID extraction
4. **Timestamp Parsing**: Extract request timestamp from Erhalten column using FlowUtils.parseDateToEpoch
5. **Reload Strategy**: Use sessionStorage to coordinate reloads
6. **Background Processing**: All link processing and flow creation happens in background script
7. **Flow Creation**: Create inbox flows with proper timestamps, no tab opening
8. **Logging**: Flow-specific logging for complete audit trail
9. **Error Handling**: Graceful degradation, continue on individual failures

## Success Criteria

- Flows created only once per unique inbox message
- Duplicate flows prevented by the flow system
- New messages detected within 10 seconds of appearing
- Configuration persists and is editable from popup
- Dry run mode works for testing
- Flow-specific logs provide complete audit trail
- No performance impact on other extension features
- Simplified architecture without redundant storage
