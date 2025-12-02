import 'webextension-polyfill';
import { pdfCommandHandler } from './commands/pdf';
import { BackgroundLoggerService } from './services/logger-service';
import { BACKEND_URL } from '@extension/env';
import { ConfigService, FlowUtils, TabManagementService, sleep } from '@extension/shared';
import {
  extensionConfigStorage,
  extensionRuntimeStorage,
  ensureMigrated,
  DEFAULT_CONFIG,
  DEFAULT_LOCAL_MODEL,
} from '@extension/storage';
import type { FlowPayload, BackgroundCommands, CommandResponse, Flow } from '@extension/types';

// Service instances
const tabService = new TabManagementService(extensionRuntimeStorage);

const MATH_SOLVER_PROMPT = `You are a mathematical problem solver. Your task is to:
1. Identify the mathematical problem or expression in the image
2. Solve it step by step
3. Return ONLY the final numerical answer

Rules:
- If the image contains a math problem, return only the numerical answer
- For expressions like "2+2", return "4"
- For equations like "x=5+3", return "8"
- If there are multiple problems, solve all and return answers separated by commas
- If you cannot identify a math problem, return "ERROR: No math problem found"
- Do not include units, explanations, or any other text, just the number(s)

Examples:
- Image shows "3 + 5" -> Return: "8"
- Image shows "12 × 4" -> Return: "48"
- Image shows "100 ÷ 5" -> Return: "20"
- Image shows "7 - 3" -> Return: "4"
- Image shows "2³" -> Return: "8"
- Image shows "√16" -> Return: "4"
- Image shows "What is 15% of 200?" -> Return: "30"
- Image shows multiple: "2+2" and "3×3" -> Return: "4, 9"`;

// Initialize background service
async function init() {
  try {
    // Migrate storage to latest schema and initialize configuration with defaults
    await ensureMigrated(extensionConfigStorage, DEFAULT_CONFIG, msg => extensionRuntimeStorage.logs.addLog(msg));
    await ConfigService.init();
    console.log(`[${timeNow()}][Background] - Configuration initialized`);

    // Setup message handlers
    setupMessageHandlers();
    console.log(`[${timeNow()}][Background] - Message handlers registered`);
  } catch (error) {
    console.error(`[${timeNow()}][Background] - Initialization error:`, error);
  }
}

function createMutex() {
  let tail = Promise.resolve<void>(undefined);
  return async function runExclusive<T>(fn: () => Promise<T>): Promise<T> {
    // capture previous tail and create a new one
    const prev = tail;
    let release!: () => void;
    tail = new Promise<void>(resolve => (release = resolve));
    // wait for previous task to finish
    await prev;
    try {
      return await fn();
    } finally {
      // let the next task run
      release();
    }
  };
}

const runStartFlowAndOpenExclusive = createMutex();

// Setup message handlers for content scripts
function setupMessageHandlers() {
  chrome.runtime.onMessage.addListener(
    (message: { type: keyof BackgroundCommands; payload: any }, sender, sendResponse) => {
      // Handle the message asynchronously
      handleMessage(message, sender)
        .then(sendResponse)
        .catch(error => {
          console.error(`[${timeNow()}][Background] - Message handler error:`, error);
          sendResponse({
            success: false,
            error: error instanceof Error ? error.message : 'Unknown error',
            requestId: 'error',
          });
        });

      // Return true to indicate we'll send response asynchronously
      return true;
    },
  );
}

// Keep-alive support: accept long-lived 'keepAlive' port connections from inbox content script.
// The active connection keeps the service worker running. We don't force-disconnect here;
// the content script will auto-reconnect when Chrome closes the port ~5 minutes after connect.
const KEEPALIVE_PORT_NAME = 'keepAlive';
const timeNow = () => new Date().toISOString();
chrome.runtime.onConnect.addListener(port => {
  if (port.name !== KEEPALIVE_PORT_NAME) return;

  console.log(
    `[${timeNow()}][KeepAlive][Background] - keepAlive port connected from tab ${port.sender?.tab?.id ?? 'unknown'}`,
  );

  // Optional: observe pings, suppressed to avoid noise
  port.onMessage.addListener(_msg => {
    // no-op
  });

  port.onDisconnect.addListener(() => {
    console.log(`[${timeNow()}][KeepAlive][Background] - keepAlive port disconnected`);
  });
});

// Handle incoming messages
async function handleMessage(
  message: { type: keyof BackgroundCommands; payload: any },
  sender: chrome.runtime.MessageSender,
): Promise<CommandResponse> {
  console.log(`[${timeNow()}][Background] - Received message: ${message.type}`, message.payload);

  try {
    // Route message to appropriate handler
    switch (message.type) {
      case 'item.printProductConfirmation':
        return pdfCommandHandler(message.payload, sender);

      case 'tab.manage':
        return handleTabManagement(message.payload, sender);

      case 'flows.scheduleCloseAfterNavigation':
        handleFlowDone(message.payload, sender);
        return {
          success: true,
          requestId: 'scheduleCloseAfterNavigation',
        };

      case 'image.solve':
        return processImageAPI(message.payload.imageData, message.payload.flowId)
          .then(result => {
            console.log(`[${timeNow()}][Background] - Successfully processed image`);
            return { success: true, data: result, requestId: 'image' };
          })
          .catch(error => {
            console.error(`[${timeNow()}][Background] - Error processing image:`, error);
            return {
              success: false,
              requestId: 'image',
              error: error instanceof Error ? error.message : 'Unknown error',
            };
          });

      case 'image.solve.local':
        return processImageLocal(message.payload.imageData, message.payload.flowId)
          .then(result => {
            console.log(`[${timeNow()}][Background] - Successfully processed image via local OpenAI`);
            return { success: true, data: result, requestId: 'image.local' };
          })
          .catch(error => {
            console.error(`[${timeNow()}][Background] - Error processing image via local OpenAI:`, error);
            return {
              success: false,
              requestId: 'image.local',
              error: error instanceof Error ? error.message : 'Unknown error',
            };
          });

      case 'extension.log':
        // Store logs in background LogManager
        BackgroundLoggerService.handleLogMessage(message.payload);
        return { success: true, requestId: 'log' };

      case 'extension.error':
        // Receive error reports from content scripts and log them
        BackgroundLoggerService.handleErrorReport(message.payload, sender);
        return { success: true, requestId: 'error' };

      case 'extension.telemetry':
        // Store telemetry events
        const { events } = message.payload;
        events.forEach((event: any) => {
          console.log(`[${timeNow()}][Background][Telemetry] - ${event.eventName}:`, event);
        });
        return { success: true, requestId: 'telemetry' };

      case 'extension.getConfig':
        return {
          success: true,
          data: {
            config: await ConfigService.getConfig(),
            enabled: await ConfigService.isEnabled(),
          },
          requestId: 'config',
        };

      case 'extension.toggleEnabled':
        await ConfigService.toggleEnabled();
        return { success: true, requestId: 'toggle-enabled' };

      case 'extension.startFlow': {
        const payload = message.payload as FlowPayload;

        let flow: Flow;

        if (payload.type === 'email') {
          flow = FlowUtils.email(payload.id);
        } else if (payload.type === 'inbox') {
          flow = FlowUtils.inbox(payload.id, payload.requestTimestamp);
        } else if (payload.type === 'manual') {
          flow = FlowUtils.manual(payload.id);
        } else {
          throw Error(`Invalid payload type`);
        }

        const existed = await ConfigService.startFlow(flow);
        return {
          success: true,
          data: existed,
          requestId: payload.id,
        };
      }

      case 'extension.startFlowAndOpen':
        const payload = message.payload as FlowPayload & { url: string };
        return runStartFlowAndOpenExclusive(async () => {
          let flow: Flow;
          if (payload.type === 'email') {
            flow = FlowUtils.email(payload.id);
          } else if (payload.type === 'inbox') {
            flow = FlowUtils.inbox(payload.id, payload.requestTimestamp);
          } else if (payload.type === 'manual') {
            flow = FlowUtils.manual(payload.id);
          } else {
            throw Error(`Invalid payload type`);
          }

          const existed = await ConfigService.startFlow(flow);
          if (existed) {
            return {
              success: true,
              data: { existed: true },
              requestId: payload.id,
            };
          }

          const tab = await tabService.openTab(payload.url, true, payload.id);
          return {
            success: true,
            data: { existed: false, tabId: tab.id },
            requestId: payload.id,
          };
        });

      case 'extension.getFlow': {
        const { id } = message.payload as { id: string };
        const flow = await ConfigService.getFlow(id);
        return {
          success: true,
          data: flow,
          requestId: id,
        };
      }

      case 'extension.getAllFlows': {
        const flows = await ConfigService.getAllFlows();
        return {
          success: true,
          data: flows,
          requestId: 'get-all-flows',
        };
      }

      case 'logs.query':
        // Handle log queries from content scripts or popup
        try {
          const result = BackgroundLoggerService.queryLogs(message.payload);
          return {
            success: true,
            data: result,
            requestId: 'logs-query',
          };
        } catch (error) {
          return {
            success: false,
            error: error instanceof Error ? error.message : 'Unknown error',
            requestId: 'logs-query',
          };
        }

      case 'logs.stats':
        // Get log statistics
        return {
          success: true,
          data: BackgroundLoggerService.getLogStats(),
          requestId: 'logs-stats',
        };

      default:
        throw new Error(`Unknown command type: ${String(message.type)}`);
    }
  } catch (error) {
    console.error(`[${timeNow()}][Background] - Error handling message:`, error);
    throw error;
  }
}

// Handle tab management commands
async function handleTabManagement(
  payload: { action: string; tabId?: number; url?: string; flowId?: string },
  sender: chrome.runtime.MessageSender,
): Promise<CommandResponse> {
  const requestId = 'tab';

  try {
    switch (payload.action) {
      case 'open':
        if (!payload.url) {
          throw new Error('URL required for open action');
        }
        const tab = await tabService.openTab(payload.url, true, payload.flowId);
        return {
          success: true,
          data: { tabId: tab.id },
          requestId,
        };

      case 'close':
        const tabId = payload.tabId || sender.tab?.id;
        if (!tabId) {
          throw new Error('Tab ID required for close action');
        }
        await tabService.closeTab(tabId);
        return {
          success: true,
          requestId,
        };

      case 'reload':
        if (!payload.tabId) {
          throw new Error('Tab ID required for reload action');
        }
        await tabService.reloadTab(payload.tabId);
        return {
          success: true,
          requestId,
        };

      case 'manage':
        if (!payload.tabId || !payload.flowId) {
          throw new Error('Tab ID and Flow ID required for manage action');
        }
        await tabService.markManaged(payload.tabId, payload.flowId);
        return {
          success: true,
          requestId,
        };

      case 'unmanage':
        if (!payload.tabId) {
          throw new Error('Tab ID required for unmanage action');
        }
        await tabService.unmarkManaged(payload.tabId);
        return {
          success: true,
          requestId,
        };

      case 'isManaged':
        const isManagedTabId = sender.tab?.id;
        if (!isManagedTabId) {
          throw new Error('Tab ID required for isManaged action');
        }
        const isManaged = await tabService.isManaged(isManagedTabId);
        return {
          success: true,
          data: { isManaged },
          requestId,
        };

      case 'addManagedTab':
        if (!payload.tabId || !payload.flowId) {
          throw new Error('Tab ID and Flow ID required for addManagedTab action');
        }
        await tabService.markManaged(payload.tabId, payload.flowId);
        return {
          success: true,
          requestId,
        };

      case 'updateActivity':
        if (!payload.tabId) {
          throw new Error('Tab ID required for updateActivity action');
        }
        await tabService.updateActivity(payload.tabId);
        return {
          success: true,
          requestId,
        };

      case 'getTabCount':
        const count = await tabService.getTabCount();
        return {
          success: true,
          data: { count },
          requestId,
        };

      case 'closeAllTabs':
        if (!payload.flowId) {
          throw new Error('Flow ID required for closeAllTabs action');
        }
        await tabService.closeAllTabsForFlow(payload.flowId);
        return {
          success: true,
          requestId,
        };

      case 'cleanupStale':
        const cleanedCount = await tabService.cleanupStaleTabs();
        return {
          success: true,
          data: { cleanedCount },
          requestId,
        };

      default:
        throw new Error(`Unknown tab action: ${payload.action}`);
    }
  } catch (error) {
    console.error(`[${timeNow()}][Background] - Tab management error:`, error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
      requestId,
    };
  }
}

async function handleFlowDone(
  payload: {
    flowId: string;
    timeoutMs: number;
  },
  sender: chrome.runtime.MessageSender,
): Promise<void> {
  console.log(`[${timeNow()}][Background] - Closing all tabs for flow: ${payload.flowId} after ${payload.timeoutMs}ms`);

  setTimeout(async function () {
    console.info(`[${timeNow()}][Background] - Closing all tabs: ${payload.flowId}:`);
    await tabService.closeAllTabsForFlow(payload.flowId);
  }, payload.timeoutMs);
}

// Initialize background service
init();

async function dataUrlToBlobFetch(dataUrl: string): Promise<Blob> {
  const res = await fetch(dataUrl);
  return res.blob();
}

/**
 * Process an image by sending it directly to OpenAI using the local solver configuration.
 */
async function processImageLocal(imageData: string, flowId: string) {
  const config = await ConfigService.getConfig();

  if (!config.token) {
    throw new Error('OpenAI API token not configured. Please set your API token in the extension options.');
  }

  const model = config.localModel || DEFAULT_LOCAL_MODEL;
  const apiKey = config.token;

  console.log(`[${timeNow()}][Background] - Processing image via local OpenAI solver with model ${model}...`);

  const controller = new AbortController();
  const timeoutMs = 60000;
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const payload = {
      model,
      messages: [
        {
          role: 'system',
          content: MATH_SOLVER_PROMPT,
        },
        {
          role: 'user',
          content: [
            {
              type: 'text',
              text: 'Solve and return only the number.',
            },
            {
              type: 'image_url',
              image_url: {
                url: imageData,
                detail: 'low',
              },
            },
          ],
        },
      ],
      temperature: 1,
    } as const;

    const startTime = performance.now();
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    const duration = performance.now() - startTime;
    console.log(`[${timeNow()}][Background] - OpenAI request completed in ${duration.toFixed(0)}ms`);

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`OpenAI request failed (${response.status}): ${text || response.statusText}`);
    }

    const data = await response.json();
    const content = data?.choices?.[0]?.message?.content;
    if (!content || typeof content !== 'string') {
      throw new Error('No result in OpenAI response');
    }

    return {
      result: content,
    };
  } finally {
    clearTimeout(timeout);
  }
}

/**
 * Process an image by sending it to the TRC backend API
 */
async function processImageAPI(imageData: string, flowId: string) {
  const backendUrl = BACKEND_URL;
  const config = await ConfigService.getConfig();

  console.log(`[${timeNow()}][Background][CEB] - sending requests to backend:`, backendUrl);

  if (!config.token) {
    throw new Error('API token not configured. Please set your API token in the extension options.');
  }

  console.log(`[${timeNow()}][Background] - Processing image via API...`);

  const blob = await dataUrlToBlobFetch(imageData);

  const filename = `${flowId}.image.png`;

  const formData = new FormData();
  formData.append('file', blob, filename);
  formData.append('flow_id', flowId);

  const response = await fetch(`${backendUrl}/api/core/solve`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${config.token}` },
    body: formData,
  });
  if (!response.ok) throw new Error(`API request failed (${response.status}): ${await response.text()}`);

  const data = await response.json();
  if (!data.result) throw new Error('No result in API response');
  return data;
}
