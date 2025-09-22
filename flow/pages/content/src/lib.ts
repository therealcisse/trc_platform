import type {
  Matcher,
  WaitOptions,
  ClickOptions,
  TelemetryEvent,
  LocalDate as LocalDateType,
  ExecutionConfig,
} from '@extension/types';

import { sendBackgroundCommand } from '@extension/shared';

// LocalDate utility class
export class LocalDate implements LocalDateType {
  private localDate: Date;

  constructor() {
    // Simply use the current Date - it already provides local time correctly
    this.localDate = new Date();
  }

  toString(): string {
    // Return local date/time string in ISO format (without timezone info)
    const year = this.localDate.getFullYear();
    const month = String(this.localDate.getMonth() + 1).padStart(2, '0');
    const day = String(this.localDate.getDate()).padStart(2, '0');
    const hours = String(this.localDate.getHours()).padStart(2, '0');
    const minutes = String(this.localDate.getMinutes()).padStart(2, '0');
    const seconds = String(this.localDate.getSeconds()).padStart(2, '0');
    const milliseconds = String(this.localDate.getMilliseconds()).padStart(3, '0');

    return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}.${milliseconds}`;
  }

  getHours(): number {
    return this.localDate.getHours();
  }

  getMinutes(): number {
    return this.localDate.getMinutes();
  }

  getDay(): number {
    return this.localDate.getDay();
  }
}

// Matcher registry
const matcherRegistry = new Map<string, Matcher>();

export function registerMatcher(matcher: Matcher): void {
  console.log(`[Extension] Registering matcher: ${matcher.name}`);
  matcherRegistry.set(matcher.id, matcher);
}

export function unregisterMatcher(matcherId: string): void {
  console.log(`[Extension] Unregistering matcher: ${matcherId}`);
  matcherRegistry.delete(matcherId);
}

export function getActiveMatchers(): Matcher[] {
  return Array.from(matcherRegistry.values()).filter(m => m.enabled);
}

// DOM utilities
export async function waitForSelector(selector: string, options: WaitOptions = {}): Promise<Element> {
  const { timeout = 10000, interval = 100, visible = false } = options;
  const startTime = Date.now();

  return new Promise((resolve, reject) => {
    const check = () => {
      const element = document.querySelector(selector);

      if (element) {
        if (!visible || isElementVisible(element)) {
          resolve(element);
          return;
        }
      }

      if (Date.now() - startTime > timeout) {
        reject(new Error(`Timeout waiting for selector: ${selector}`));
        return;
      }

      setTimeout(check, interval);
    };

    check();
  });
}

export async function clickWithVerification(element: Element, options: ClickOptions = {}): Promise<boolean> {
  const { verify = true, scroll = true } = options;

  try {
    if (!(element instanceof HTMLElement)) {
      throw new Error('Element is not clickable');
    }

    // Scroll into view if needed
    if (scroll) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
      await sleep(200); // Wait for scroll
    }

    // Click the element
    element.click();

    // Verify click if needed
    if (verify) {
      // Check if element is still in DOM (might be removed after click)
      await sleep(100);
      return !document.contains(element) || element.getAttribute('data-clicked') === 'true';
    }

    return true;
  } catch (error) {
    console.error('[Extension] Error clicking element:', error);
    return false;
  }
}

export async function safeNavigate(url: string): Promise<void> {
  try {
    await sendBackgroundCommand('tab.manage', {
      action: 'open',
      url,
    });
  } catch (error) {
    console.error('[Extension] Error navigating to URL:', error);
    throw error;
  }
}

// Telemetry
const telemetryQueue: TelemetryEvent[] = [];
let telemetryTimer: ReturnType<typeof setTimeout> | null = null;

export function logEvent(event: TelemetryEvent): void {
  telemetryQueue.push(event);

  // Batch send telemetry events
  if (!telemetryTimer) {
    telemetryTimer = setTimeout(async () => {
      if (telemetryQueue.length > 0) {
        const events = [...telemetryQueue];
        telemetryQueue.length = 0;

        try {
          await sendBackgroundCommand('extension.telemetry', { events });
        } catch (error) {
          console.error('[Extension] Error sending telemetry:', error);
        }
      }
      telemetryTimer = null;
    }, 1000);
  }
}

export function trackError(error: Error, context?: any): void {
  console.error('[Extension] Tracked error:', error, context);

  logEvent({
    eventName: 'error',
    metadata: {
      message: error.message,
      stack: error.stack,
      context,
    },
    timestamp: Date.now(),
  });
}

// Helper functions
function isElementVisible(element: Element): boolean {
  if (!(element instanceof HTMLElement)) return false;

  const rect = element.getBoundingClientRect();
  const style = window.getComputedStyle(element);

  return (
    rect.width > 0 &&
    rect.height > 0 &&
    style.display !== 'none' &&
    style.visibility !== 'hidden' &&
    style.opacity !== '0'
  );
}

export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export function random(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1) + min);
}

// Check if current time is within operational hours
export function isValidTimeOfDay(config: ExecutionConfig): boolean {
  const now = new LocalDate();
  const hh = now.getHours();
  const day = now.getDay();

  const operationalHours = config.operationalHours[day];
  if (!operationalHours.enabled) {
    return false;
  }

  const { min, max } = operationalHours;

  // Handle midnight crossover case (e.g., 22:00 to 06:00)
  if (min > max) {
    // Time range crosses midnight: valid if hour >= min OR hour < max
    return hh >= min || hh < max;
  }

  // Normal case: valid if hour is within range (inclusive of min, exclusive of max)
  return hh >= min && hh < max;
}

/**
 * Opens all simulation links found on the page in new tabs
 */
export function openAllSimulationLinks(): void {
  console.log('[CEB] Looking for simulation links to open...');

  // Function to extract and open links
  const processLinks = () => {
    // Find all links in the list items
    const links = document.querySelectorAll('ul li a');

    if (links.length === 0) {
      console.log('[CEB] No simulation links found');
      return;
    }

    console.log(`[CEB] Found ${links.length} simulation links`);

    // Collect all valid hrefs
    const hrefs: string[] = [];

    links.forEach(link => {
      if (link instanceof HTMLAnchorElement) {
        const href = link.href;

        // Skip invalid links
        if (!href || href === '#' || href === 'javascript:void(0)') {
          return;
        }

        // Resolve relative URLs to absolute
        let absoluteUrl = href;
        if (href.startsWith('./')) {
          // Handle relative paths
          const baseUrl = window.location.origin + window.location.pathname.replace(/\/[^\/]*$/, '/');
          absoluteUrl = baseUrl + href.substring(2);
        } else if (!href.startsWith('http')) {
          // Handle other relative paths
          absoluteUrl = new URL(href, window.location.href).href;
        }

        hrefs.push(absoluteUrl);
      }
    });

    if (hrefs.length === 0) {
      console.log('[CEB] No valid links to open');
      return;
    }

    // Open all links with a delay to prevent browser blocking
    console.log(`[CEB] Opening ${hrefs.length} links...`);

    hrefs.forEach((href, index) => {
      setTimeout(() => {
        console.log(`[CEB] Opening link ${index + 1}/${hrefs.length}: ${href}`);

        // Use window.open with specific features to ensure new tab
        const newWindow = window.open(href, '_blank', 'noopener,noreferrer');

        if (!newWindow) {
          console.warn(`[CEB] Failed to open: ${href} (popup may be blocked)`);
        }
      }, index * 150); // 150ms delay between each tab to avoid blocking
    });

    // Log completion after all tabs should be opened
    setTimeout(
      () => {
        console.log('[CEB] Finished opening all simulation links');
      },
      hrefs.length * 150 + 500,
    );
  };

  // Wait for DOM to be ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', processLinks);
  } else {
    // DOM is already ready, but let's give it a moment for any dynamic content
    setTimeout(processLinks, 100);
  }
}

/**
 * Processes an image from a simulation page by:
 * 1. Extracting the image from the DOM
 * 2. Sending it to the background script for API processing (bypasses CORS)
 * 3. Filling in the result and submitting the form
 */
export async function processImage(): Promise<void> {
  console.log('[CEB] Processing simulation image...');

  try {
    // Find the image element
    const imageElement = document.querySelector('.image-container img') as HTMLImageElement;
    if (!imageElement) {
      throw new Error('Image not found on page');
    }

    // Find the form elements
    const inputElement = document.getElementById('numberInput') as HTMLInputElement;
    const formElement = document.getElementById('validationForm') as HTMLFormElement;

    if (!inputElement || !formElement) {
      throw new Error('Form elements not found on page');
    }

    console.log('[CEB] Extracting image from:', imageElement.src);

    // Convert image to base64 data URL for message passing
    const imageDataUrl = await fetchImageAsDataUrl(imageElement.src);

    console.log('[CEB] Sending image to background script for processing...');

    // Send message to background script to process the image
    // This bypasses CORS completely as the background script makes the API call
    const response = await sendBackgroundCommand('image.solve', {
      imageData: imageDataUrl,
    });

    if (!response.success) {
      throw new Error(response.error || 'Failed to process image');
    }

    console.log('[CEB] Received result from background:', response.data);

    // Extract the numeric answer from the result
    // The API might return something like "The answer is 10" or just "10"
    const result = extractNumericAnswer(response.data);

    console.log('[CEB] Extracted answer:', result);

    // Fill in the input
    inputElement.value = result;

    // Trigger input event to ensure any validation listeners are fired
    inputElement.dispatchEvent(new Event('input', { bubbles: true }));

    // Submit the form
    console.log('[CEB] Submitting form with answer:', result);

    // Find and click the submit button or submit the form directly
    const submitButton = formElement.querySelector('button[type="submit"]') as HTMLButtonElement;
    if (submitButton) {
      submitButton.click();
    } else {
      formElement.submit();
    }

    console.log('[CEB] Image processing completed successfully');
  } catch (error) {
    console.error('[CEB] Error processing image:', error);

    // Show error in result div if it exists
    const resultDiv = document.getElementById('result');
    if (resultDiv) {
      resultDiv.className = 'result error show';
      resultDiv.textContent = `Error: ${error instanceof Error ? error.message : 'Unknown error'}`;
    }
  }
}

/**
 * Fetches an image URL and returns it as a data URL for message passing
 */
async function fetchImageAsDataUrl(imageUrl: string): Promise<string> {
  try {
    // If it's a relative URL, convert to absolute
    const absoluteUrl = new URL(imageUrl, window.location.href).href;

    const response = await fetch(absoluteUrl);
    if (!response.ok) {
      throw new Error(`Failed to fetch image: ${response.status}`);
    }

    const blob = await response.blob();

    // Ensure it's an image
    if (!blob.type.startsWith('image/')) {
      throw new Error(`Fetched content is not an image: ${blob.type}`);
    }

    // Convert blob to data URL for message passing
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        if (typeof reader.result === 'string') {
          resolve(reader.result);
        } else {
          reject(new Error('Failed to convert image to data URL'));
        }
      };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  } catch (error) {
    console.error('[CEB] Error fetching image:', error);
    throw error;
  }
}

/**
 * Fetches an image URL and returns it as a Blob
 */
export async function fetchImageAsBlob(imageUrl: string): Promise<Blob> {
  try {
    // If it's a relative URL, convert to absolute
    const absoluteUrl = new URL(imageUrl, window.location.href).href;

    const response = await fetch(absoluteUrl);
    if (!response.ok) {
      throw new Error(`Failed to fetch image: ${response.status}`);
    }

    const blob = await response.blob();

    // Ensure it's an image
    if (!blob.type.startsWith('image/')) {
      throw new Error(`Fetched content is not an image: ${blob.type}`);
    }

    return blob;
  } catch (error) {
    console.error('[CEB] Error fetching image:', error);
    throw error;
  }
}

/**
 * Extracts a numeric answer from the API result text
 * The API might return various formats like:
 * - "10"
 * - "The answer is 10"
 * - "x = 10"
 * - "Result: 10"
 */
export function extractNumericAnswer(result: string): string {
  // First, try to find the answer pattern from the simulation page
  // The correct answer format follows the pattern in the HTML files

  // Remove any markdown or formatting
  const cleanResult = result
    .replace(/```[\s\S]*?```/g, '') // Remove code blocks
    .replace(/[*_~`]/g, '') // Remove markdown formatting
    .trim();

  // Try to extract numbers that match the expected format
  // Look for patterns like "answer is X", "= X", "result: X", etc.
  const patterns = [
    /answer[\s:]*is[\s:]*(\d+)/i,
    /result[\s:]*is[\s:]*(\d+)/i,
    /=[\s]*(\d+)/,
    /:[\s]*(\d+)$/,
    /^(\d+)$/,
  ];

  for (const pattern of patterns) {
    const match = cleanResult.match(pattern);
    if (match && match[1]) {
      return match[1];
    }
  }

  // If no pattern matches, try to find any number in the result
  const numbers = cleanResult.match(/\d+/g);
  if (numbers && numbers.length === 1) {
    return numbers[0];
  }

  // If multiple numbers or no numbers found, return the cleaned result
  // and let the validation handle it
  console.warn('[CEB] Could not extract clear numeric answer from:', result);
  return cleanResult;
}
