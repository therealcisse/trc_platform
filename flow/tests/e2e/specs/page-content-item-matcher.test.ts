import { setupItemPage, mockServices } from '../helpers/item';

describe('Item Matcher Content Script', () => {
  beforeEach(async () => {
    // Navigate to a test page
    await browser.url('https://auktion.hansemerkur.de/item.php?id=123');

    // Setup mock DOM elements
    await setupItemPage(browser);

    // Setup mock service responses
    await mockServices.setupMockResponses(browser);
  });

  it('should detect and process valid item pages', async () => {
    // Subscribe to console logs
    await browser.sessionSubscribe({ events: ['log.entryAdded'] });
    const logs: string[] = [];
    browser.on('log.entryAdded', (logEntry) => {
      logs.push(logEntry.text);
    });

    // Trigger content script
    await browser.execute(() => {
      // Content script is injected automatically for matching URLs
      window.dispatchEvent(new Event('load'));
    });

    // Wait for matcher activation log
    await browser.waitUntil(
      () => logs.some((log) => log.includes('Item matcher activated')),
      { timeout: 5000 }
    );

    // Verify logs indicating successful processing
    expect(logs).toContain('[ItemMatcher] URL matches, registering matcher');
    expect(logs).toContain('Item matcher activated');
    expect(logs).toContain('Browse item executor triggered successfully');
  });

  it('should handle disabled extension state', async () => {
    // Override mock to return disabled state
    await browser.execute(() => {
      window.chrome.runtime.sendMessage = async (message: any) => {
        if (message.type === 'extension.getConfig') {
          return {
            success: true,
            data: {
              config: {},
              enabled: false,
            },
          };
        }
        return { success: false };
      };
    });

    // Subscribe to console logs
    await browser.sessionSubscribe({ events: ['log.entryAdded'] });
    const logs: string[] = [];
    browser.on('log.entryAdded', (logEntry) => {
      logs.push(logEntry.text);
    });

    // Trigger content script
    await browser.execute(() => {
      window.dispatchEvent(new Event('load'));
    });

    // Verify extension disabled message
    await browser.waitUntil(
      () => logs.some((log) => log.includes('Extension disabled')),
      { timeout: 5000 }
    );
  });

  it('should validate URL patterns correctly', async () => {
    // Test invalid URL
    await browser.url('https://example.com');

    // Subscribe to console logs
    await browser.sessionSubscribe({ events: ['log.entryAdded'] });
    const logs: string[] = [];
    browser.on('log.entryAdded', (logEntry) => {
      logs.push(logEntry.text);
    });

    // Trigger content script
    await browser.execute(() => {
      window.dispatchEvent(new Event('load'));
    });

    // Verify matcher not activated for invalid URL
    await browser.pause(1000);
    expect(logs).not.toContain('[ItemMatcher] URL matches, registering matcher');
  });

  it('should handle missing DOM elements gracefully', async () => {
    // Clear the DOM
    await browser.execute(() => {
      document.body.innerHTML = '';
    });

    // Subscribe to console logs
    await browser.sessionSubscribe({ events: ['log.entryAdded'] });
    const logs: string[] = [];
    browser.on('log.entryAdded', (logEntry) => {
      logs.push(logEntry.text);
    });

    // Trigger content script
    await browser.execute(() => {
      window.dispatchEvent(new Event('load'));
    });

    // Verify error handling
    await browser.waitUntil(
      () => logs.some((log) => log.includes('No buy button found') || log.includes('No title found')),
      { timeout: 5000 }
    );
  });
});