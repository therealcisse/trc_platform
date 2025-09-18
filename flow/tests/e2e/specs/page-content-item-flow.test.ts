import { setupItemPage, mockServices, mockConfig, mockFlow } from '../helpers/item';

describe('Item Workflow Integration', () => {
  beforeEach(async () => {
    // Navigate to a test page
    await browser.url('https://auktion.hansemerkur.de/item.php?id=123');

    // Setup mock DOM elements
    await setupItemPage(browser);

    // Setup mock service responses
    await mockServices.setupMockResponses(browser);
  });

  it('should execute complete item workflow', async () => {
    // Subscribe to console logs
    await browser.sessionSubscribe({ events: ['log.entryAdded'] });
    const logs: string[] = [];
    browser.on('log.entryAdded', (logEntry) => {
      logs.push(logEntry.text);
    });

    // Trigger content script execution
    await browser.execute(() => {
      window.dispatchEvent(new Event('load'));
    });

    // Wait for matcher activation
    await browser.waitUntil(
      () => logs.some((log) => log.includes('Item matcher activated')),
      { timeout: 5000 }
    );

    // Verify complete workflow execution
    const workflowLogs = [
      'Item matcher activated',
      'Starting item workflow',
      'Product details:',
      'Opening item:',
      'Browse item executor triggered successfully',
    ];

    workflowLogs.forEach(logText => {
      expect(logs.some(log => log.includes(logText))).toBe(true);
    });
  });

  it('should handle the complete command chain', async () => {
    // Track command execution
    const commands: string[] = [];
    await browser.execute(() => {
      const originalSendMessage = window.chrome.runtime.sendMessage;
      window.chrome.runtime.sendMessage = async (message: any) => {
        commands.push(message.type);
        return originalSendMessage(message);
      };
    });

    // Trigger content script execution
    await browser.execute(() => {
      window.dispatchEvent(new Event('load'));
    });

    // Wait for command chain completion
    await browser.pause(2000);

    // Verify command sequence
    const expectedCommands = [
      'extension.getConfig',
      'item.clickProductLink',
      'tab.manage',
    ];

    expectedCommands.forEach(command => {
      expect(commands).toContain(command);
    });
  });

  it('should maintain tab state through workflow', async () => {
    // Track tab state changes
    const tabStates: any[] = [];
    await browser.execute(() => {
      const originalSendMessage = window.chrome.runtime.sendMessage;
      window.chrome.runtime.sendMessage = async (message: any) => {
        if (message.type === 'tab.manage') {
          tabStates.push({
            action: message.payload.action,
            tabId: message.payload.tabId,
          });
        }
        return originalSendMessage(message);
      };
    });

    // Execute complete workflow
    await browser.execute(() => {
      window.dispatchEvent(new Event('load'));
    });

    // Wait for workflow completion
    await browser.pause(2000);

    // Verify tab state transitions
    expect(tabStates).toContainEqual({
      action: 'isManaged',
      tabId: expect.any(Number),
    });

    expect(tabStates).toContainEqual({
      action: 'open',
      url: expect.stringContaining('buy_now/id/'),
    });
  });

  it('should handle concurrent operations', async () => {
    // Setup buying state tracking
    const buyingStates: any[] = [];
    await browser.execute(() => {
      const originalSendMessage = window.chrome.runtime.sendMessage;
      window.chrome.runtime.sendMessage = async (message: any) => {
        if (message.type === 'state.buying') {
          buyingStates.push({
            action: message.payload.action,
            flowId: message.payload.flowId,
          });
        }
        return originalSendMessage(message);
      };
    });

    // Execute workflow twice in quick succession
    await Promise.all([
      browser.execute(() => window.dispatchEvent(new Event('load'))),
      browser.execute(() => window.dispatchEvent(new Event('load'))),
    ]);

    // Wait for operations to complete
    await browser.pause(2000);

    // Verify state management
    const buyingStateChecks = buyingStates.filter(
      state => state.action === 'check'
    );
    expect(buyingStateChecks.length).toBeGreaterThan(1);
  });
});