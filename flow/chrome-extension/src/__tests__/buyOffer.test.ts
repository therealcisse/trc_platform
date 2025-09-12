import { executeBuyOfferWorkflow } from '../../executors/buyOffer';
import {
  createTestContext,
  setupTestDOM,
  createTestBuyOfferDOM,
  MockChromeRuntime,
  waitForPromises
} from './utils/testHelpers';

describe('Buy Offer Workflow', () => {
  let mockRuntime: MockChromeRuntime;

  beforeEach(() => {
    mockRuntime = new MockChromeRuntime();
    (global as any).chrome = {
      runtime: mockRuntime
    };

    // Setup test DOM
    setupTestDOM(createTestBuyOfferDOM());
  });

  afterEach(() => {
    jest.clearAllMocks();
    document.body.innerHTML = '';
  });

  it('should execute purchase workflow', async () => {
    const context = createTestContext({
      tabId: 1,
      url: 'https://auktion.hansemerkur.de/buy_now/id/123',
      matcherId: 'buy-offer-matcher',
      productId: 'test-id',
      config: {
        ...createTestContext().config,
        products: [{
          text: 'TestProduct',
          insuredType: 'TestType',
          insuredAge: { min: 20, max: 40 }
        }]
      }
    });

    const selectors = {
      productTitle: '#page_buy_now h2',
      buyFormButton: '#buyFormBtn'
    };

    // Mock buying state check
    mockRuntime.addListener((message, sender, sendResponse) => {
      if (message.type === 'state.buying') {
        sendResponse({
          success: true,
          data: { buying: true, id: 'test-id' }
        });
      }
    });

    const result = await executeBuyOfferWorkflow(context, selectors);

    expect(result.success).toBe(true);
    expect(result.data?.productId).toBe('test-id');
    expect(result.telemetry?.domOperations).toBe(2);
  });

  it('should handle dry run mode', async () => {
    const context = createTestContext({
      tabId: 1,
      url: 'https://auktion.hansemerkur.de/buy_now/id/123',
      matcherId: 'buy-offer-matcher',
      productId: 'test-id',
      dryRun: true
    });

    const selectors = {
      productTitle: '#page_buy_now h2',
      buyFormButton: '#buyFormBtn'
    };

    const clickSpy = jest.spyOn(HTMLElement.prototype, 'click');

    const result = await executeBuyOfferWorkflow(context, selectors);

    expect(result.success).toBe(true);
    expect(clickSpy).not.toHaveBeenCalled();
  });

  it('should apply configured delay', async () => {
    const context = createTestContext({
      tabId: 1,
      url: 'https://auktion.hansemerkur.de/buy_now/id/123',
      matcherId: 'buy-offer-matcher',
      productId: 'test-id',
      delay: 2
    });

    const selectors = {
      productTitle: '#page_buy_now h2',
      buyFormButton: '#buyFormBtn'
    };

    const startTime = Date.now();

    const result = await executeBuyOfferWorkflow(context, selectors);

    const duration = Date.now() - startTime;

    expect(result.success).toBe(true);
    expect(duration).toBeGreaterThanOrEqual(2000);
    expect(result.data?.appliedDelay).toBe(2);
  });

  it('should handle invalid product format', async () => {
    // Set invalid product title
    setupTestDOM(`
      <div id="page_buy_now">
        <h2>Invalid Product Title</h2>
        <button id="buyFormBtn">Buy Now</button>
      </div>
    `);

    const context = createTestContext({
      tabId: 1,
      url: 'https://auktion.hansemerkur.de/buy_now/id/123',
      matcherId: 'buy-offer-matcher',
      productId: 'test-id'
    });

    const selectors = {
      productTitle: '#page_buy_now h2',
      buyFormButton: '#buyFormBtn'
    };

    const result = await executeBuyOfferWorkflow(context, selectors);

    expect(result.success).toBe(false);
    expect(result.error).toBe('Invalid product format');
  });

  it('should handle duplicate purchase attempts', async () => {
    const context = createTestContext({
      tabId: 1,
      url: 'https://auktion.hansemerkur.de/buy_now/id/123',
      matcherId: 'buy-offer-matcher',
      productId: 'test-id'
    });

    const selectors = {
      productTitle: '#page_buy_now h2',
      buyFormButton: '#buyFormBtn'
    };

    // Mock buying state check showing another tab is buying
    mockRuntime.addListener((message, sender, sendResponse) => {
      if (message.type === 'state.buying') {
        sendResponse({
          success: true,
          data: { buying: true, id: 'other-id' }
        });
      }
    });

    const result = await executeBuyOfferWorkflow(context, selectors);

    expect(result.success).toBe(false);
    expect(result.error).toBe('Duplicate purchase attempt');
  });

  it('should handle missing buy button', async () => {
    // Remove buy button
    setupTestDOM(`
      <div id="page_buy_now">
        <h2>TestProduct (TestType, 30 Jahre)</h2>
      </div>
    `);

    const context = createTestContext({
      tabId: 1,
      url: 'https://auktion.hansemerkur.de/buy_now/id/123',
      matcherId: 'buy-offer-matcher',
      productId: 'test-id'
    });

    const selectors = {
      productTitle: '#page_buy_now h2',
      buyFormButton: '#buyFormBtn'
    };

    const result = await executeBuyOfferWorkflow(context, selectors);

    expect(result.success).toBe(false);
    expect(result.error).toBe('Buy button not found');
  });

  it('should clean up buying state on failure', async () => {
    const context = createTestContext({
      tabId: 1,
      url: 'https://auktion.hansemerkur.de/buy_now/id/123',
      matcherId: 'buy-offer-matcher',
      productId: 'test-id'
    });

    const selectors = {
      productTitle: '#page_buy_now h2',
      buyFormButton: '#buyFormBtn'
    };

    // Mock state management
    const stateCalls: string[] = [];
    mockRuntime.addListener((message, sender, sendResponse) => {
      if (message.type === 'state.buying') {
        stateCalls.push(message.payload.action);
        if (message.payload.action === 'check') {
          sendResponse({
            success: true,
            data: { buying: true, id: 'test-id' }
          });
        } else {
          sendResponse({ success: true });
        }
      } else if (message.type === 'tab.manage') {
        // Simulate error
        sendResponse({ success: false, error: 'Test error' });
      }
    });

    const result = await executeBuyOfferWorkflow(context, selectors);

    expect(result.success).toBe(false);
    expect(stateCalls).toContain('clear');
  });
});
