import { executeOffersWorkflow } from '../executors/offers';
import {
  createTestContext,
  setupTestDOM,
  createTestOffersDOM,
  MockChromeRuntime,
  waitForPromises
} from './utils/testHelpers';

describe('Offers Workflow', () => {
  let mockRuntime: MockChromeRuntime;
  
  beforeEach(() => {
    mockRuntime = new MockChromeRuntime();
    (global as any).chrome = {
      runtime: mockRuntime
    };
  });
  
  afterEach(() => {
    jest.clearAllMocks();
    document.body.innerHTML = '';
  });
  
  describe('Map Offers', () => {
    beforeEach(() => {
      setupTestDOM(createTestOffersDOM('map'));
    });
    
    it('should process map offers and open links', async () => {
      const context = createTestContext({
        tabId: 1,
        url: 'https://auktion.hansemerkur.de/karte_sofortkauf.html',
        matcherId: 'offers-matcher'
      });
      
      const selectors = {
        offerMarkers: '.leaflet-marker-pane img[src="templates/design_version2_01/images/marker/marker-02.png"]',
        offerPopup: '.leaflet-popup-content a',
        browseList: '',
        buyButton: '',
        titleLink: ''
      };
      
      // Mock background communication
      mockRuntime.addListener((message, sender, sendResponse) => {
        if (message.type === 'tab.manage') {
          sendResponse({ success: true, data: { tabId: 2 } });
        }
      });
      
      const result = await executeOffersWorkflow(context, selectors);
      
      expect(result.success).toBe(true);
      expect(result.data?.processedCount).toBe(1);
      expect(result.data?.openedOffers).toContain('https://auktion.hansemerkur.de/buy_now/id/123');
    });
    
    it('should handle missing popup links', async () => {
      // Remove popup content
      setupTestDOM(`
        <div class="leaflet-marker-pane">
          <img src="templates/design_version2_01/images/marker/marker-02.png" />
        </div>
      `);
      
      const context = createTestContext({
        tabId: 1,
        url: 'https://auktion.hansemerkur.de/karte_sofortkauf.html',
        matcherId: 'offers-matcher'
      });
      
      const selectors = {
        offerMarkers: '.leaflet-marker-pane img[src="templates/design_version2_01/images/marker/marker-02.png"]',
        offerPopup: '.leaflet-popup-content a',
        browseList: '',
        buyButton: '',
        titleLink: ''
      };
      
      const result = await executeOffersWorkflow(context, selectors);
      
      expect(result.success).toBe(true);
      expect(result.data?.processedCount).toBe(0);
      expect(result.telemetry?.errors.length).toBeGreaterThan(0);
    });
  });
  
  describe('Browse Offers', () => {
    beforeEach(() => {
      setupTestDOM(createTestOffersDOM('browse'));
    });
    
    it('should process browse offers and validate products', async () => {
      const context = createTestContext({
        tabId: 1,
        url: 'https://auktion.hansemerkur.de/browse/search',
        matcherId: 'offers-matcher',
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
        offerMarkers: '',
        offerPopup: '',
        browseList: 'div.browse_list .row',
        buyButton: '.buy_now a.btn',
        titleLink: '.title a'
      };
      
      // Mock background communication
      mockRuntime.addListener((message, sender, sendResponse) => {
        if (message.type === 'tab.manage') {
          sendResponse({ success: true, data: { tabId: 2 } });
        }
      });
      
      const result = await executeOffersWorkflow(context, selectors);
      
      expect(result.success).toBe(true);
      expect(result.data?.processedCount).toBe(1);
      expect(result.data?.openedOffers).toContain('https://auktion.hansemerkur.de/buy_now/id/123');
    });
    
    it('should skip invalid products', async () => {
      // Invalid product title
      setupTestDOM(`
        <div class="browse_list">
          <div class="row">
            <div class="title">
              <a href="#">Invalid Product Title</a>
            </div>
            <div class="buy_now">
              <a href="https://auktion.hansemerkur.de/buy_now/id/123" class="btn">Buy</a>
            </div>
          </div>
        </div>
      `);
      
      const context = createTestContext({
        tabId: 1,
        url: 'https://auktion.hansemerkur.de/browse/search',
        matcherId: 'offers-matcher'
      });
      
      const selectors = {
        offerMarkers: '',
        offerPopup: '',
        browseList: 'div.browse_list .row',
        buyButton: '.buy_now a.btn',
        titleLink: '.title a'
      };
      
      const result = await executeOffersWorkflow(context, selectors);
      
      expect(result.success).toBe(true);
      expect(result.data?.processedCount).toBe(0);
    });
    
    it('should handle missing buy buttons', async () => {
      // Remove buy button
      setupTestDOM(`
        <div class="browse_list">
          <div class="row">
            <div class="title">
              <a href="#">TestProduct (TestType, 30 Jahre)</a>
            </div>
          </div>
        </div>
      `);
      
      const context = createTestContext({
        tabId: 1,
        url: 'https://auktion.hansemerkur.de/browse/search',
        matcherId: 'offers-matcher'
      });
      
      const selectors = {
        offerMarkers: '',
        offerPopup: '',
        browseList: 'div.browse_list .row',
        buyButton: '.buy_now a.btn',
        titleLink: '.title a'
      };
      
      const result = await executeOffersWorkflow(context, selectors);
      
      expect(result.success).toBe(true);
      expect(result.data?.processedCount).toBe(0);
    });
  });
  
  it('should handle unmanaged tabs', async () => {
    setupTestDOM(createTestOffersDOM('map'));
    
    const context = createTestContext({
      tabId: 1,
      url: 'https://auktion.hansemerkur.de/karte_sofortkauf.html',
      matcherId: 'offers-matcher'
    });
    
    const selectors = {
      offerMarkers: '.leaflet-marker-pane img[src="templates/design_version2_01/images/marker/marker-02.png"]',
      offerPopup: '.leaflet-popup-content a',
      browseList: '',
      buyButton: '',
      titleLink: ''
    };
    
    // Mock tab management check
    mockRuntime.addListener((message, sender, sendResponse) => {
      if (message.type === 'tab.manage' && message.payload.action === 'isManaged') {
        sendResponse({ success: true, data: false });
      }
    });
    
    const result = await executeOffersWorkflow(context, selectors);
    
    expect(result.success).toBe(false);
    expect(result.error).toBe('Tab is not managed');
  });
  
  it('should handle background communication errors', async () => {
    setupTestDOM(createTestOffersDOM('map'));
    
    const context = createTestContext({
      tabId: 1,
      url: 'https://auktion.hansemerkur.de/karte_sofortkauf.html',
      matcherId: 'offers-matcher'
    });
    
    const selectors = {
      offerMarkers: '.leaflet-marker-pane img[src="templates/design_version2_01/images/marker/marker-02.png"]',
      offerPopup: '.leaflet-popup-content a',
      browseList: '',
      buyButton: '',
      titleLink: ''
    };
    
    // Mock communication error
    mockRuntime.addListener((message, sender, sendResponse) => {
      sendResponse({ success: false, error: 'Communication error' });
    });
    
    const result = await executeOffersWorkflow(context, selectors);
    
    expect(result.success).toBe(false);
    expect(result.error).toBeDefined();
    expect(result.telemetry?.errors.length).toBeGreaterThan(0);
  });
});