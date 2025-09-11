import 'webextension-polyfill';
import { exampleThemeStorage } from '@extension/storage';

exampleThemeStorage.get().then(theme => {
  console.log('theme', theme);
});

console.log('Background loaded');
console.log("Edit 'chrome-extension/src/background/index.ts' and save to reload.");

/**
 * Process an image by sending it to the TRC backend API
 */
async function processImageAPI(imageData: string): Promise<{ result: string }> {
  const backendUrl = process.env['CEB_TRC_BACKEND_URL'];
  const backendToken = process.env['CEB_TRC_BACKEND_TOKEN'];

  if (!backendUrl || !backendToken) {
    throw new Error('Missing required environment variables: CEB_TRC_BACKEND_URL or CEB_TRC_BACKEND_TOKEN');
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
      'Authorization': `Bearer ${backendToken}`,
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
chrome.runtime.onMessage.addListener((request: any, sender: chrome.runtime.MessageSender, sendResponse) => {
  console.log('[Background] Received message:', request.type, 'from tab:', sender.tab?.id);

  if (request.type === 'PROCESS_IMAGE') {
    // Process the image asynchronously
    processImageAPI(request.imageData)
      .then(result => {
        console.log('[Background] Successfully processed image');
        sendResponse({ success: true, result: result.result });
      })
      .catch(error => {
        console.error('[Background] Error processing image:', error);
        sendResponse({
          success: false,
          error: error instanceof Error ? error.message : 'Unknown error'
        });
      });

    // Return true to indicate we'll send a response asynchronously
    return true;
  }

  return false;
});
