import { BackgroundUtils, TabManager } from '@extension/shared';
import { LocalTime, LocalTimeUtils } from '@extension/types';
import type {
  Matcher,
  WaitOptions,
  ClickOptions,
  TelemetryEvent,
  LocalDate as LocalDateType,
  ExecutionConfig,
} from '@extension/types';

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

export async function ensureFocus(
  target: HTMLElement | string,
  opts?: {
    selectorContext?: ParentNode;
    timeoutMs?: number;
    intervalMs?: number;
    preventScroll?: boolean;
    scrollIntoView?: boolean;
    ensureTabbable?: boolean;
    ensureEnabled?: boolean;
  },
): Promise<HTMLElement | undefined> {
  // Check if the document is visible; if not, return immediately
  if (document.visibilityState !== 'visible') {
    return undefined;
  }

  const {
    selectorContext = document,
    timeoutMs = 200,
    intervalMs = 8,
    preventScroll = true,
    scrollIntoView = false,
    ensureTabbable = false,
    ensureEnabled = true,
  } = opts ?? {};

  const resolveElement = (): HTMLElement | null => {
    if (typeof target === 'string') {
      const el = selectorContext.querySelector(target);
      return el instanceof HTMLElement ? el : null;
    }
    return target;
  };

  let el = resolveElement();
  if (!el) throw new Error('ensureFocus: element not found');

  if (scrollIntoView) {
    el.scrollIntoView({ block: 'nearest', inline: 'nearest' });
    await new Promise<void>(r => requestAnimationFrame(() => r()));
  }

  if (ensureTabbable && el.tabIndex < 0 && !(el instanceof HTMLInputElement)) {
    el.tabIndex = 0;
  }

  if (
    ensureEnabled &&
    (el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement || el instanceof HTMLSelectElement)
  ) {
    const deadline = performance.now() + timeoutMs;
    while ((el.disabled || el.getAttribute('aria-disabled') === 'true') && performance.now() < deadline) {
      await new Promise(r => setTimeout(r, intervalMs));
    }
    if (el.disabled || el.getAttribute('aria-disabled') === 'true') {
      throw new Error('ensureFocus: element remained disabled');
    }
  }

  el.focus({ preventScroll });
  if (document.activeElement === el) {
    if (el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement) {
      try {
        const len = el.value?.length ?? 0;
        el.setSelectionRange(len, len);
      } catch {
        // ignore if not applicable
      }
    }
    return el;
  }

  const deadline = performance.now() + timeoutMs;
  while (performance.now() < deadline) {
    if (!el.isConnected) {
      const next = resolveElement();
      if (next) el = next;
      else throw new Error('ensureFocus: element not found');
    }

    el.focus({ preventScroll });
    if (document.activeElement === el) {
      if (el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement) {
        try {
          const len = el.value?.length ?? 0;
          el.setSelectionRange(len, len);
        } catch {
          // ignore if not applicable
        }
      }
      return el;
    }

    await new Promise(r => setTimeout(r, intervalMs));
  }

  throw new Error('ensureFocus: failed to focus element within timeout');
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
    const tabManager = TabManager.getInstance();
    await tabManager.openUnmanagedTab(url);
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
          await BackgroundUtils.sendTelemetry(events);
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

export async function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export function random(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1) + min);
}

const DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'] as const;

// Check if current time is within operational hours
export function isValidTimeOfDay(config: ExecutionConfig): boolean {
  const now = new LocalDate();
  const day = DAYS[now.getDay()];

  const operationalHours = config.operationalHours[day];
  if (!operationalHours.enabled) {
    return false;
  }

  const { min, max } = operationalHours;

  // Use minute-precision with inclusive end
  const currentMins = LocalTime.now().toMinutesOfDay();
  const start = LocalTimeUtils.toMinutesOfDay(min);
  const endInclusive = LocalTimeUtils.toMinutesOfDay(max);

  if (start <= endInclusive) {
    return currentMins >= start && currentMins <= endInclusive;
  }
  // Midnight crossover: [start..23:59] U [00:00..end]
  return currentMins >= start || currentMins <= endInclusive;
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
