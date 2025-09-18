import type { MockBrowser } from '@wdio/types';
import type { Product, Flow, ExecutionConfig } from '@extension/types';

/**
 * Mock item page elements and content
 */
export async function setupItemPage(browser: MockBrowser) {
  await browser.execute(() => {
    // Create title element
    const title = document.createElement('h1');
    title.className = 'item_title';
    title.textContent = 'Tier KV KW: Hund Alter: 2';
    document.body.appendChild(title);

    // Create buy button
    const buyButton = document.createElement('a');
    buyButton.className = 'btn';
    buyButton.href = 'https://auktion.hansemerkur.de/buy_now/id/123';
    buyButton.textContent = 'Buy Now';
    
    const buyContainer = document.createElement('div');
    buyContainer.className = 'buy_now';
    buyContainer.appendChild(buyButton);
    document.body.appendChild(buyContainer);
  });
}

/**
 * Mock product test data
 */
export const mockProduct: Product = {
  type: 'ANIMAL',
  name: 'Tier KV KW',
  insuredType: 'Hund',
  insuredAge: 2,
  allowed: true,
  delay: 0,
};

/**
 * Mock flow test data
 */
export const mockFlow: Flow = {
  id: '123',
  type: 'inbox',
  title: 'Test Flow',
  href: 'https://auktion.hansemerkur.de/item.php?id=123',
  requestTimestamp: Date.now() / 1000,
};

/**
 * Mock configuration
 */
export const mockConfig: ExecutionConfig = {
  enabled: true,
  token: 'test-token',
  animals: true,
  animalTimerMin: 0,
  animalTimerMax: 5,
  animalProcessingTimeSeconds: 30,
};

/**
 * Mock service responses
 */
export const mockServices = {
  async setupMockResponses(browser: MockBrowser) {
    await browser.execute(() => {
      // Mock ConfigService
      window.chrome.runtime.sendMessage = async (message: any) => {
        if (message.type === 'extension.getConfig') {
          return {
            success: true,
            data: {
              config: mockConfig,
              enabled: true,
            },
          };
        }
        if (message.type === 'state.buying') {
          return {
            success: true,
            data: {
              buying: false,
            },
          };
        }
        return { success: false };
      };
    });
  },
};