import type { Flow } from '@extension/types';

export class FlowUtils {
  static parseIDFromTitle(title: string): string {
    const match = /\(ID\s+(\d+)\)/.exec(title);
    if (!match) {
      throw new Error('Could not parse ID from title');
    }
    return match[1];
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

  static email(id: string, title: string, href: string): Flow {
    const now = Date.now();
    return {
      id,
      timestamp: now,
      requestTimestamp: now,
      status: 'running',
      source: 'email',
      title,
      href,
    };
  }

  static inbox(id: string, requestTimestamp: number, title: string, href: string): Flow {
    return {
      id,
      timestamp: Date.now(),
      requestTimestamp,
      status: 'running',
      source: 'inbox',
      title,
      href,
    };
  }
}
