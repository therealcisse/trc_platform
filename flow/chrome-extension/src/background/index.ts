import 'webextension-polyfill';
import { ConfigService } from '@extension/shared';
import { emailCommandHandler } from './commands/email';
import { offersCommandHandler } from './commands/offers';
import { buyOfferCommandHandler } from './commands/buyOffer';
import type { BackgroundCommands, CommandResponse } from '@extension/shared';

// Initialize background service
async function init() {
  try {
    // Initialize configuration with defaults
    await ConfigService.init();
    console.log('[Background] Configuration initialized');

    // Setup message handlers
    setupMessageHandlers();
    console.log('[Background] Message handlers registered');

  } catch (error) {
    console.error('[Background] Initialization error:', error);
  }
}

// Setup message handlers for content scripts
function setupMessageHandlers() {
  chrome.runtime.onMessage.addListener(
    (message: { type: keyof BackgroundCommands; payload: any }, sender, sendResponse) => {
      // Handle the message asynchronously
      handleMessage(message, sender)
        .then(sendResponse)
        .catch(error => {
          console.error('[Background] Message handler error:', error);
          sendResponse({
            success: false,
            error: error instanceof Error ? error.message : 'Unknown error',
            requestId: `error-${Date.now()}`
          });
        });

      // Return true to indicate we'll send response asynchronously
      return true;
    }
  );
}

// Handle incoming messages
async function handleMessage(
  message: { type: keyof BackgroundCommands; payload: any },
  sender: chrome.runtime.MessageSender
): Promise<CommandResponse> {
  console.log('[Background] Received message:', message.type);

  try {
    // Route message to appropriate handler
    switch (message.type) {
      case 'email.openUnreadAndClickLink':
        return emailCommandHandler(message.payload, sender);

      case 'offers.clickProductLink':
        return offersCommandHandler(message.payload, sender);

      case 'buyOffer.execute':
        return buyOfferCommandHandler(message.payload, sender);

      case 'tab.manage':
        return handleTabManagement(message.payload, sender);

      case 'state.buying':
        return handleBuyingState(message.payload);

      case 'image.solve':
        return processImageAPI(message.payload.imageData)
                    .then(result => {
                        console.log('[Background] Successfully processed image');
                        return ({ success: true, result: result.result });
                    })
                    .catch(error => {
                        console.error('[Background] Error processing image:', error);
                        return ({
                            success: false,
                            error: error instanceof Error ? error.message : 'Unknown error'
                        });
                    });

      case 'extension.log':
        console.log(`[Extension] ${message.payload.text}`);
        return { success: true, requestId: `log-${Date.now()}` };

      case 'extension.telemetry':
        // Store telemetry events
        const { events } = message.payload;
        events.forEach(event => {
          console.log(`[Telemetry] ${event.eventName}:`, event);
        });
        return { success: true, requestId: `telemetry-${Date.now()}` };

      case 'extension.isEnabled':
        return {
          success: true,
          data: await ConfigService.isEnabled(),
          requestId: `enabled-${Date.now()}`
        };

      case 'extension.getConfig':
        return {
          success: true,
          data: await ConfigService.getConfig(),
          requestId: `config-${Date.now()}`
        };

      default:
        throw new Error(`Unknown command type: ${String(message.type)}`);
    }
  } catch (error) {
    console.error('[Background] Error handling message:', error);
    throw error;
  }
}

// Handle tab management commands
async function handleTabManagement(
  payload: { action: string; tabId?: number; url?: string },
  sender: chrome.runtime.MessageSender
): Promise<CommandResponse> {
  const requestId = `tab-${Date.now()}`;

  try {
    switch (payload.action) {
      case 'open':
        if (!payload.url) {
          throw new Error('URL required for open action');
        }
        const tab = await chrome.tabs.create({ url: payload.url });
        return {
          success: true,
          data: { tabId: tab.id },
          requestId
        };

      case 'close':
        const tabId = payload.tabId || sender.tab?.id;
        if (!tabId) {
          throw new Error('Tab ID required for close action');
        }
        await chrome.tabs.remove(tabId);
        return {
          success: true,
          requestId
        };

      case 'reload':
        if (!payload.tabId) {
          throw new Error('Tab ID required for reload action');
        }
        await chrome.tabs.reload(payload.tabId);
        return {
          success: true,
          requestId
        };

      default:
        throw new Error(`Unknown tab action: ${payload.action}`);
    }
  } catch (error) {
    console.error('[Background] Tab management error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
      requestId
    };
  }
}

// Handle buying state commands
async function handleBuyingState(
  payload: { action: string; key: string; id?: string; timeout?: number }
): Promise<CommandResponse> {
  const requestId = `state-${Date.now()}`;

  try {
    const storage = await chrome.storage.local.get(['buyingOffers']);
    const buyingOffers = storage.buyingOffers || {};

    switch (payload.action) {
      case 'mark':
        if (!payload.id || !payload.timeout) {
          throw new Error('ID and timeout required for mark action');
        }
        buyingOffers[payload.key] = {
          id: payload.id,
          timeout: payload.timeout
        };
        await chrome.storage.local.set({ buyingOffers });
        return {
          success: true,
          requestId
        };

      case 'check':
        const entry = buyingOffers[payload.key];
        if (!entry || Date.now() > entry.timeout) {
          // Remove expired entry
          if (entry) {
            delete buyingOffers[payload.key];
            await chrome.storage.local.set({ buyingOffers });
          }
          return {
            success: true,
            data: { buying: false },
            requestId
          };
        }
        return {
          success: true,
          data: { buying: true, id: entry.id },
          requestId
        };

      case 'clear':
        delete buyingOffers[payload.key];
        await chrome.storage.local.set({ buyingOffers });
        return {
          success: true,
          requestId
        };

      default:
        throw new Error(`Unknown buying state action: ${payload.action}`);
    }
  } catch (error) {
    console.error('[Background] Buying state error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
      requestId
    };
  }
}

// Initialize background service
init();

/**
 * Process an image by sending it to the TRC backend API
 */
async function processImageAPI(imageData: string): Promise<{ result: string }> {
  const backendUrl = process.env['CEB_TRC_BACKEND_URL'];
  const config = await ConfigService.getConfig();

  if (!backendUrl) {
    throw new Error('Missing required environment variable: CEB_TRC_BACKEND_URL');
  } else {
            console.log('[CEB] sending requests to backend:', backendUrl);

        }

  if (!config.token) {
    throw new Error('API token not configured. Please set your API token in the extension options.');
  }

  console.log('[Background] Processing image via API...');

  // Convert base64 to blob
  const base64Response = await fetch(imageData);
  const blob = await base64Response.blob();

  // Prepare form data for API
  const formData = new FormData();
  formData.append('file', blob, 'image.png');

  // Send to API - No CORS restrictions in background script!
  const response = await fetch(`${backendUrl}/api/core/solve`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${config.token}`,
    },
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API request failed (${response.status}): ${errorText}`);
  }

  const data = await response.json();
  console.log('[Background] API response received:', data);

  if (!data.result) {
    throw new Error('No result in API response');
  }

  return data;
}

/**
 * Listen for messages from content scripts
 */
// chrome.runtime.onMessage.addListener((request: any, sender: chrome.runtime.MessageSender, sendResponse) => {
//   console.log('[Background] Received message:', request.type, 'from tab:', sender.tab?.id);
//
//   if (request.type === 'PROCESS_IMAGE') {
//     // Process the image asynchronously
//     processImageAPI(request.imageData)
//       .then(result => {
//         console.log('[Background] Successfully processed image');
//         sendResponse({ success: true, result: result.result });
//       })
//       .catch(error => {
//         console.error('[Background] Error processing image:', error);
//         sendResponse({
//           success: false,
//           error: error instanceof Error ? error.message : 'Unknown error'
//         });
//       });
//
//     // Return true to indicate we'll send a response asynchronously
//     return true;
//   }
//
//   return false;
// });
