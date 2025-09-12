import type { ExtensionStorage, ExecutionContext } from '@extension/content/types';

/**
 * Mock chrome storage for testing
 */
export class MockChromeStorage {
  private storage: { [key: string]: any } = {};
  
  async get(keys?: string[] | null): Promise<any> {
    if (!keys) {
      return this.storage;
    }
    
    const result: { [key: string]: any } = {};
    for (const key of keys) {
      if (key in this.storage) {
        result[key] = this.storage[key];
      }
    }
    return result;
  }
  
  async set(items: { [key: string]: any }): Promise<void> {
    Object.assign(this.storage, items);
  }
  
  async remove(keys: string[]): Promise<void> {
    for (const key of keys) {
      delete this.storage[key];
    }
  }
  
  async clear(): Promise<void> {
    this.storage = {};
  }
}

/**
 * Mock chrome tabs for testing
 */
export class MockChromeTabs {
  private tabs: Map<number, chrome.tabs.Tab> = new Map();
  private nextTabId = 1;
  
  async create(createProperties: chrome.tabs.CreateProperties): Promise<chrome.tabs.Tab> {
    const tab: chrome.tabs.Tab = {
      id: this.nextTabId++,
      index: this.tabs.size,
      url: createProperties.url,
      active: createProperties.active ?? false,
      pinned: false,
      highlighted: false,
      windowId: 1,
      status: 'complete'
    };
    this.tabs.set(tab.id!, tab);
    return tab;
  }
  
  async remove(tabIds: number | number[]): Promise<void> {
    const ids = Array.isArray(tabIds) ? tabIds : [tabIds];
    for (const id of ids) {
      this.tabs.delete(id);
    }
  }
  
  async reload(tabId: number): Promise<void> {
    // No-op for testing
  }
  
  getTab(tabId: number): chrome.tabs.Tab | undefined {
    return this.tabs.get(tabId);
  }
}

/**
 * Create test execution context
 */
export function createTestContext(
  partial?: Partial<ExecutionContext>
): ExecutionContext {
  return {
    tabId: 1,
    url: 'https://test.com',
    matcherId: 'test-matcher',
    config: {
      operationalHours: {
        1: { enabled: true, min: 8, max: 17 }
      },
      emailMode: true,
      emailRefreshMin: 30,
      emailRefreshMax: 60,
      timerMode: false,
      randomDelay: { min: 5, max: 30 }
    },
    timeout: 30000,
    dryRun: true,
    ...partial
  };
}

/**
 * Create a mock DOM environment for testing
 */
export function setupTestDOM(html: string): void {
  document.body.innerHTML = html;
}

/**
 * Helper to create test product metadata
 */
export function createTestProduct(text: string = 'TestProduct (TestType, 30 Jahre)'): string {
  return text;
}

/**
 * Helper to create test email data
 */
export function createTestEmailDOM(): string {
  return `
    <div>
      <div aria-label="Ungelesen HanseMerkur AuktionsPlattform">Test Email</div>
      <div id="x_body">
        <a href="https://auktion.hansemerkur.de/test">Test Link</a>
      </div>
      <span>Gelesen/Ungelesen</span>
    </div>
  `;
}

/**
 * Helper to create test offers DOM
 */
export function createTestOffersDOM(type: 'map' | 'browse'): string {
  if (type === 'map') {
    return `
      <div class="leaflet-marker-pane">
        <img src="templates/design_version2_01/images/marker/marker-02.png" />
      </div>
      <div class="leaflet-popup-content">
        <a href="https://auktion.hansemerkur.de/buy_now/id/123">Test Offer</a>
      </div>
    `;
  }
  
  return `
    <div class="browse_list">
      <div class="row">
        <div class="title">
          <a href="#">TestProduct (TestType, 30 Jahre)</a>
        </div>
        <div class="buy_now">
          <a href="https://auktion.hansemerkur.de/buy_now/id/123" class="btn">Buy</a>
        </div>
      </div>
    </div>
  `;
}

/**
 * Helper to create test buy offer DOM
 */
export function createTestBuyOfferDOM(): string {
  return `
    <div id="page_buy_now">
      <h2>TestProduct (TestType, 30 Jahre)</h2>
      <button id="buyFormBtn">Buy Now</button>
    </div>
  `;
}

/**
 * Helper to wait for promises to resolve
 */
export function waitForPromises(): Promise<void> {
  return new Promise(resolve => setImmediate(resolve));
}

/**
 * Helper to mock chrome runtime messaging
 */
export class MockChromeRuntime {
  private messageHandlers: ((
    message: any,
    sender: chrome.runtime.MessageSender,
    sendResponse: (response: any) => void
  ) => void)[] = [];
  
  addListener(
    handler: (
      message: any,
      sender: chrome.runtime.MessageSender,
      sendResponse: (response: any) => void
    ) => void
  ): void {
    this.messageHandlers.push(handler);
  }
  
  async sendMessage(message: any): Promise<any> {
    return new Promise((resolve) => {
      const sender: chrome.runtime.MessageSender = {
        id: 'test-extension',
        tab: { id: 1, url: 'https://test.com' }
      };
      
      for (const handler of this.messageHandlers) {
        handler(message, sender, resolve);
      }
    });
  }
}

/**
 * Utility to create test extension storage
 */
export function createTestStorage(): ExtensionStorage {
  return {
    enabled: true,
    config: {
      operationalHours: {
        0: { enabled: false, min: 0, max: 0 },
        1: { enabled: true, min: 8, max: 17 },
        2: { enabled: true, min: 8, max: 17 },
        3: { enabled: true, min: 8, max: 17 },
        4: { enabled: true, min: 8, max: 17 },
        5: { enabled: true, min: 8, max: 17 },
        6: { enabled: false, min: 0, max: 0 }
      },
      emailMode: true,
      emailRefreshMin: 30,
      emailRefreshMax: 60,
      timerMode: false,
      randomDelay: {
        min: 5,
        max: 30
      }
    },
    logs: [],
    managedTabs: {},
    buyingOffers: {},
    productStrategies: []
  };
}