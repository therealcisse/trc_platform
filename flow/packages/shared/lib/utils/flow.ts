import type { Flow } from '@extension/types';

export class FlowUtils {
  static parseDateToEpoch(dateStr: string): number {
    // Example input: "15.09.2025 – 18:46:04"
    // Normalize dash and trim
    const normalized = dateStr.replace('–', '-').trim();

    // Split into date and time parts
    const [datePart, timePart] = normalized.split('-').map(s => s.trim());

    if (!datePart || !timePart) {
      throw new Error(`Invalid date string format: ${dateStr}`);
    }

    // Extract day, month, year
    const [dayStr, monthStr, yearStr] = datePart.split('.');
    const day = parseInt(dayStr, 10);
    const month = parseInt(monthStr, 10);
    const year = parseInt(yearStr, 10);

    // Extract hour, minute, second
    const [hourStr, minuteStr, secondStr] = timePart.split(':');
    const hour = parseInt(hourStr, 10);
    const minute = parseInt(minuteStr, 10);
    const second = parseInt(secondStr, 10);

    // Build Date object (note: month is 0-based in JS/TS)
    const date = new Date(year, month - 1, day, hour, minute, second);

    if (isNaN(date.getTime())) {
      throw new Error(`Failed to parse date: ${dateStr}`);
    }

    // Return timestamp in milliseconds
    return date.getTime();
  }

  static parseIDFromTitle(title: string): string {
    // Try to match "(ID 12345)" format
    const idInParensMatch = /\(ID\s+(\d+)\)/.exec(title);
    if (idInParensMatch) {
      return idInParensMatch[1];
    }

    // Try to match "Lead 1455952 ..." format (anything starting with Lead followed by a number)
    const leadMatch = /Lead\s+(\d+)/.exec(title);
    if (leadMatch) {
      return leadMatch[1];
    }

    throw new Error('Could not parse ID from title');
  }

  static parseIDFromHref(href: string): string {
    const url = new URL(href);
    const id = url.searchParams.get('id');
    if (!id) {
      throw new Error('No ID parameter in URL');
    }
    return id;
  }

  static parseIDFromPath(href: string): string {
    const match = /\/id\/(\d+)\.html/.exec(href);
    if (!match) {
      throw new Error('Could not parse ID from path');
    }
    return match[1];
  }

  static email(id: string, title: string): Flow {
    const now = Date.now();
    return {
      id,
      timestamp: now,
      requestTimestamp: now,
      status: 'running',
      source: 'email',
      title,
    };
  }

  static inbox(id: string, requestTimestamp: number, title: string): Flow {
    return {
      id,
      timestamp: Date.now(),
      requestTimestamp,
      status: 'running',
      source: 'inbox',
      title,
    };
  }
}
