import 'webextension-polyfill';
import { ConfigService } from '@extension/shared';
import { emailCommandHandler } from './commands/email';
import { itemCommandHandler } from './commands/item';
import { buyOfferCommandHandler } from './commands/buyOffer';
import {
    FlowUtils,
} from '@extension/types';
import type {
    FlowPayload,
    BackgroundCommands,
    CommandResponse,
} from '@extension/types';
import { extensionConfigStorage } from '@extension/storage';
import { TabManagementService, BuyingStateService } from '@extension/shared';

// Service instances
const tabService = new TabManagementService(extensionConfigStorage);
const buyingService = new BuyingStateService(extensionConfigStorage);

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

      case 'item.clickProductLink':
        return itemCommandHandler(message.payload, sender);

      case 'buyOffer.execute':
        return buyOfferCommandHandler(message.payload, sender);

      case 'tab.manage':
        return handleTabManagement(message.payload, sender);

      case 'state.buying':
        return handleBuyingState(message.payload);

      case 'image.solve':
        const requestId = `state-${Date.now()}`;
        return processImageAPI(message.payload.imageData)
                    .then(result => {
                        console.log('[Background] Successfully processed image');
                        return ({ success: true, result: result.result, requestId });
                    })
                    .catch(error => {
                        console.error('[Background] Error processing image:', error);
                        return ({
                            success: false,
                            requestId,
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

      case 'extension.getConfig':
        return {
          success: true,
          data: {
            config: await ConfigService.getConfig(),
            enabled: await ConfigService.isEnabled(),
          },
          requestId: `config-${Date.now()}`
        };

      case 'extension.startFlow': {
        const payload = message.payload as FlowPayload;
        const flow =
          payload.type === 'email'
            ? FlowUtils.email(payload.id, payload.title, payload.href)
            : FlowUtils.inbox(payload.id, payload.requestTimestamp, payload.title, payload.href);

        const existed = await ConfigService.startFlow(flow);
        return {
          success: true,
          data: existed,
          requestId: `flow-start-${Date.now()}`,
        };
      }

      case 'extension.getFlow': {
        const { id } = message.payload as { id: string };
        const flow = await ConfigService.getFlow(id);
        return {
          success: true,
          data: flow,
          requestId: `flow-get-${Date.now()}`,
        };
      }

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
        const tab = await tabService.openTab(payload.url, payload.action === 'manage');
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
        await tabService.closeTab(tabId);
        return {
          success: true,
          requestId
        };

      case 'reload':
        if (!payload.tabId) {
          throw new Error('Tab ID required for reload action');
        }
        await tabService.reloadTab(payload.tabId);
        return {
          success: true,
          requestId
        };

      case 'manage':
        if (!payload.tabId) {
          throw new Error('Tab ID required for manage action');
        }
        await tabService.markManaged(payload.tabId);
        return {
          success: true,
          requestId
        };

      case 'unmanage':
        if (!payload.tabId) {
          throw new Error('Tab ID required for unmanage action');
        }
        await tabService.unmarkManaged(payload.tabId);
        return {
          success: true,
          requestId
        };

      case 'isManaged':
        if (!payload.tabId) {
          throw new Error('Tab ID required for isManaged action');
        }
        const isManaged = await tabService.isManaged(payload.tabId);
        return {
          success: true,
          data: { isManaged },
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
    switch (payload.action) {
      case 'mark':
        if (!payload.id || !payload.timeout) {
          throw new Error('ID and timeout required for mark action');
        }
        await buyingService.markBuying(payload.key, payload.id, payload.timeout);
        return {
          success: true,
          requestId
        };

      case 'check':
        const buyingState = await buyingService.isBuying(payload.key);
        return {
          success: true,
          data: buyingState,
          requestId
        };

      case 'clear':
        await buyingService.clearBuying(payload.key);
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

