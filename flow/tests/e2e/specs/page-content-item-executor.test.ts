import { setupItemPage, mockServices, mockConfig, mockFlow } from '../helpers/item';

describe('Item Executor Content Script', () => {
  beforeEach(async () => {
    // Navigate to a test page
    await browser.url('https://auktion.hansemerkur.de/item.php?id=123');

    // Setup mock DOM elements
    await setupItemPage(browser);

    // Setup mock service responses
    await mockServices.setupMockResponses(browser);
  });

  it('should execute workflow for valid product', async () => {
    // Subscribe to console logs
    await browser.sessionSubscribe({ events: ['log.entryAdded'] });
    const logs: string[] = [];
    browser.on('log.entryAdded', (logEntry) => {
      logs.push(logEntry.text);
    });

    // Execute the workflow
    const result = await browser.execute((config, flow) => {
      return (window as any).__itemExecutor(
        {
          tabId: 1,
          url: window.location.href,
          matcherId: 'item-matcher',
          flowId: flow.id,
          config,
          timeout: 30000,
          dryRun: false,
        },
        {
          buyButton: '.buy_now a.btn',
          titleLink: 'h1.item_title',
        }
      );
    }, mockConfig, mockFlow);

    // Verify successful execution
    expect(result.success).toBe(true);
    expect(result.matcherId).toBe('item-matcher');
    expect(result.executorName).toBe('item');
    expect(logs).toContain('Starting item workflow');
  });

  it('should handle unmanaged tabs correctly', async () => {
    // Override mock to return unmanaged state
    await browser.execute(() => {
      window.chrome.runtime.sendMessage = async (message: any) => {
        if (message.type === 'tab.manage') {
          return {
            success: true,
            data: false,
          };
        }
        return { success: false };
      };
    });

    // Execute the workflow
    const result = await browser.execute((config, flow) => {
      return (window as any).__itemExecutor(
        {
          tabId: 1,
          url: window.location.href,
          matcherId: 'item-matcher',
          flowId: flow.id,
          config,
          timeout: 30000,
          dryRun: false,
        },
        {
          buyButton: '.buy_now a.btn',
          titleLink: 'h1.item_title',
        }
      );
    }, mockConfig, mockFlow);

    // Verify unmanaged tab handling
    expect(result.success).toBe(false);
    expect(result.error).toBe('Tab is not managed');
  });

  it('should validate product configuration', async () => {
    // Override mock config to disallow animals
    const disallowedConfig = { ...mockConfig, animals: false };

    // Execute the workflow
    const result = await browser.execute((config, flow) => {
      return (window as any).__itemExecutor(
        {
          tabId: 1,
          url: window.location.href,
          matcherId: 'item-matcher',
          flowId: flow.id,
          config,
          timeout: 30000,
          dryRun: false,
        },
        {
          buyButton: '.buy_now a.btn',
          titleLink: 'h1.item_title',
        }
      );
    }, disallowedConfig, mockFlow);

    // Verify product validation
    expect(result.success).toBe(true);
    expect(result.data.productAllowed).toBe(false);
  });

  it('should handle missing flow data', async () => {
    // Override mock to return no flow
    await browser.execute(() => {
      window.chrome.runtime.sendMessage = async (message: any) => {
        if (message.type === 'extension.getFlow') {
          return {
            success: true,
            data: null,
          };
        }
        return { success: false };
      };
    });

    // Execute the workflow
    const result = await browser.execute((config, flow) => {
      return (window as any).__itemExecutor(
        {
          tabId: 1,
          url: window.location.href,
          matcherId: 'item-matcher',
          flowId: 'invalid-id',
          config,
          timeout: 30000,
          dryRun: false,
        },
        {
          buyButton: '.buy_now a.btn',
          titleLink: 'h1.item_title',
        }
      );
    }, mockConfig, mockFlow);

    // Verify flow validation
    expect(result.success).toBe(false);
    expect(result.error).toContain('Flow not found');
  });

  it('should respect dry run mode', async () => {
    // Execute the workflow in dry run mode
    const result = await browser.execute((config, flow) => {
      return (window as any).__itemExecutor(
        {
          tabId: 1,
          url: window.location.href,
          matcherId: 'item-matcher',
          flowId: flow.id,
          config,
          timeout: 30000,
          dryRun: true,
        },
        {
          buyButton: '.buy_now a.btn',
          titleLink: 'h1.item_title',
        }
      );
    }, mockConfig, mockFlow);

    // Verify dry run execution
    expect(result.success).toBe(true);
    expect(result.data.dryRun).toBe(true);
  });
});
