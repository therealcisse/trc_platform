import { Log } from '@extension/shared';
import { MATCHER_IDS } from '@extension/types';
import { extractNumericAnswer } from '@src/lib';
import { sendBackgroundCommand } from '@extension/shared';

interface CaptchaCache {
  answer: string;
  timestamp: number;
  flowId: string;
}

export class CaptchaProcessor {
  private static instance: CaptchaProcessor;
  private cache: Map<string, CaptchaCache> = new Map();
  private readonly cacheDuration = 5 * 60 * 1000; // 5 minutes

  private constructor() {}

  static getInstance(): CaptchaProcessor {
    if (!CaptchaProcessor.instance) {
      CaptchaProcessor.instance = new CaptchaProcessor();
    }
    return CaptchaProcessor.instance;
  }

  private getCacheKey(imgSrc: string, flowId: string): string {
    const urlParts = imgSrc.split('/');
    const imagePart = urlParts[urlParts.length - 1];
    return `${flowId}:${imagePart}`;
  }

  private isCacheValid(cacheEntry: CaptchaCache): boolean {
    return Date.now() - cacheEntry.timestamp < this.cacheDuration;
  }

  async solveCaptcha(imgSrc: string, imageDataUrl: string, flowId: string, maxRetries = 3): Promise<string> {
    const log = Log.withFlow(MATCHER_IDS.BUY_OFFER, flowId);
    const cacheKey = this.getCacheKey(imgSrc, flowId);
    const cached = this.cache.get(cacheKey);

    if (cached && this.isCacheValid(cached)) {
      log.info('Using cached CAPTCHA solution');
      return cached.answer;
    }

    let lastError: Error | null = null;

    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        log.info(`Solving CAPTCHA attempt ${attempt + 1}/${maxRetries}`);

        const response = await sendBackgroundCommand(
          'image.solve',
          { imageData: imageDataUrl, flowId },
          5000 * Math.pow(2, attempt), // 5s, 10s, 20s
        );

        if (response.success && response.data?.result) {
          const answer = extractNumericAnswer(response.data.result);

          this.cache.set(cacheKey, {
            answer,
            timestamp: Date.now(),
            flowId,
          });

          log.info('CAPTCHA solved successfully');
          return answer;
        }

        lastError = new Error(response.error || 'Failed to process CAPTCHA');
        log.warn(`CAPTCHA solve attempt failed: ${lastError.message}`);
      } catch (error) {
        lastError = error as Error;
        log.error(`CAPTCHA solve error on attempt ${attempt + 1}`, { error });

        if (attempt < maxRetries - 1) {
          const delay = 1000 * Math.pow(2, attempt);
          log.info(`Waiting ${delay}ms before next attempt`);
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }

    log.error('All CAPTCHA solve attempts failed', { lastError });
    throw lastError || new Error('Failed to solve CAPTCHA after retries');
  }

  clearCacheForFlow(flowId: string): void {
    const keysToDelete = Array.from(this.cache.entries())
      .filter(([_, value]) => value.flowId === flowId)
      .map(([key]) => key);

    keysToDelete.forEach(key => this.cache.delete(key));
  }

  clearCache(): void {
    this.cache.clear();
  }
}
