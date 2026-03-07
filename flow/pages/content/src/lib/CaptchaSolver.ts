import { Log, sendBackgroundCommand } from '@extension/shared';
import { CaptchaSolverType, MATCHER_IDS } from '@extension/types';
import { extractNumericAnswer } from '@src/lib';

function assertNever(x: never): never {
  throw new Error(`Unhandled CaptchaSolverType: ${String(x)}`);
}

function extractCaptchaText(result: string): string {
  const clean = result.replace(/```[\s\S]*?```/g, '').trim();

  const m = clean.match(/^["'`](.*)["'`]$/s);
  const unquoted = m && m[1] != null ? m[1].trim() : clean;

  // Preserve explicit error sentinel values as-is (aside from outer trimming).
  if (/^error:/i.test(unquoted)) {
    return unquoted;
  }

  // For normal CAPTCHA content, remove all internal whitespace so that any spaced or
  // multi-line characters (for example, "r b k d", "AB CD", or "r\nb\nk\nd")
  // become a single contiguous token (for example, "rbkd", "ABCD").
  return unquoted.replace(/\s+/g, '');
}

interface CaptchaCache {
  answer: string;
  timestamp: number;
  flowId: string;
}

type SolveResult =
  | { ok: true; answer: string }
  | { ok: false; retriable: boolean; message: string; retryAfterMs?: number };

export class CaptchaSolver {
  private static instance: CaptchaSolver;

  private cache: Map<string, CaptchaCache> = new Map();
  private readonly cacheDuration = 5 * 60 * 1000; // 5 minutes

  // Tracks in-flight solves by cache key to dedupe bursts.
  private inFlight: Map<string, Promise<string>> = new Map();

  private constructor() {}

  static getInstance(): CaptchaSolver {
    if (!CaptchaSolver.instance) {
      CaptchaSolver.instance = new CaptchaSolver();
    }
    return CaptchaSolver.instance;
  }

  private getCacheKey(imgSrc: string, flowId: string, solver: CaptchaSolverType): string {
    const urlParts = imgSrc.split('/');
    let imagePart = urlParts[urlParts.length - 1] || imgSrc;

    // Strip query strings and fragments to ensure same images map to the same cache key
    imagePart = imagePart.split('?')[0].split('#')[0];

    return `${flowId}:${solver}:${imagePart}`;
  }

  private parseSolvedResult(result: string, solver: CaptchaSolverType): string {
    switch (solver) {
      case CaptchaSolverType.Math:
        return extractNumericAnswer(result);
      case CaptchaSolverType.Text:
        return extractCaptchaText(result);
      default:
        return assertNever(solver);
    }
  }

  private isCacheValid(cacheEntry: CaptchaCache): boolean {
    return Date.now() - cacheEntry.timestamp < this.cacheDuration;
  }

  // Decorrelated jitter backoff. See AWS Builders Library and Google SRE.
  // next = min(maxDelay, randomBetween(base, prev * factor)) which avoids lockstep retries.
  private nextBackoffMs(prev: number, base: number, factor: number, maxDelay: number): number {
    const min = base;
    const max = Math.max(base, Math.min(maxDelay, prev * factor));
    return Math.floor(min + Math.random() * (max - min));
  }

  private classifyError(e: unknown, response?: any): Extract<SolveResult, { ok: false }> {
    // Decide if we should retry. Mark 5xx and transient network errors as retriable.
    const message = response?.error || (e as Error)?.message || 'Unknown error';
    const code = response?.code;
    const retryAfterMs = this.parseRetryAfter(response?.retryAfter, response?.headers?.['retry-after']);

    // Treat known transient conditions as retriable.
    const retriable =
      code === 429 || (code && code >= 500) || /network|timeout|temporar|rate|throttle|busy/i.test(message);

    return { ok: false, retriable, message, retryAfterMs };
  }

  private parseRetryAfter(...values: Array<number | string | undefined>): number | undefined {
    for (const v of values) {
      if (v == null) continue;
      if (typeof v === 'number' && v > 0) return v * 1000;
      if (typeof v === 'string') {
        const num = Number(v);
        if (!Number.isNaN(num) && num > 0) return num * 1000; // seconds format
        const dateMs = Date.parse(v);
        if (!Number.isNaN(dateMs)) return Math.max(0, dateMs - Date.now());
      }
    }
    return undefined;
  }

  // Abort helper using AbortSignal.timeout where supported.
  private withTimeout<T>(ms: number, task: (signal: AbortSignal) => Promise<T>): Promise<T> {
    // Always create our own timer and a rejector. This guarantees settlement even if
    // the task ignores AbortSignal.
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), ms);

    const timeoutPromise = new Promise<never>((_, reject) => {
      // Reject on abort with a stable error message that classifyError can read.
      controller.signal.addEventListener(
        'abort',
        () => {
          reject(new Error('timeout'));
        },
        { once: true },
      );
    });

    // Ensure synchronous throws from task are captured as a rejected promise so
    // timers are always cleaned up and we do not leave a dangling timeoutPromise.
    const taskPromise = Promise.resolve().then(() => task(controller.signal));

    return Promise.race([taskPromise, timeoutPromise]).finally(() => clearTimeout(timer));
  }

  async solveCaptcha(
    imgSrc: string,
    imageDataUrl: string,
    flowId: string,
    solver: CaptchaSolverType = CaptchaSolverType.Math,
    maxRetries = 7,
    opts?: { perAttemptTimeoutMs?: number; totalDeadlineMs?: number }, // testability
  ): Promise<string> {
    const log = Log.withFlow(MATCHER_IDS.BUY_OFFER, flowId);
    const cacheKey = this.getCacheKey(imgSrc, flowId, solver);
    const cached = this.cache.get(cacheKey);

    if (cached && this.isCacheValid(cached)) {
      log.info('Using cached CAPTCHA solution');
      return cached.answer;
    }

    // In-flight dedupe to collapse bursts hitting the same image.
    const existing = this.inFlight.get(cacheKey);
    if (existing) {
      log.info('Awaiting in-flight CAPTCHA solution for same key');
      return existing;
    }

    const solvePromise = this._solveWithRetries(cacheKey, imageDataUrl, flowId, solver, log, maxRetries, opts).finally(
      () => this.inFlight.delete(cacheKey),
    );

    // Attach a noop handler to avoid unhandled rejection warnings if callers attach
    // their own handlers later (for example in tests).
    void solvePromise.catch(() => {});

    this.inFlight.set(cacheKey, solvePromise);
    return solvePromise;
  }

  private async _solveWithRetries(
    cacheKey: string,
    imageDataUrl: string,
    flowId: string,
    solver: CaptchaSolverType,
    log: any,
    maxRetries: number,
    opts?: { perAttemptTimeoutMs?: number; totalDeadlineMs?: number }, // testability
  ): Promise<string> {
    const command: 'image.solve.local' = 'image.solve.local';

    // Backoff parameters tuned for UI latency and burst smoothing.
    const base = 400; // base delay in ms
    const factor = 2.0; // growth factor
    const maxDelay = 10_000; // cap individual backoff
    const perAttemptTimeout = opts?.perAttemptTimeoutMs ?? 7_000;
    const totalDeadlineMs = opts?.totalDeadlineMs ?? 45_000;
    let backoff = base;
    let lastError: Error | null = null;
    const start = Date.now();

    for (let attempt = 0; attempt < maxRetries; attempt++) {
      const timeLeft = totalDeadlineMs - (Date.now() - start);
      if (timeLeft <= 0) break;

      try {
        log.info(`Solving CAPTCHA attempt ${attempt + 1}/${maxRetries}`);

        // Optional limiter for extreme bursts.
        // await this.limiter.schedule(() => Promise.resolve());

        const attemptTimeout = Math.min(perAttemptTimeout, timeLeft);
        const response = await this.withTimeout(
          attemptTimeout,
          _signal =>
            sendBackgroundCommand(command, { imageData: imageDataUrl, flowId, solver }, attemptTimeout) as Promise<any>,
        );

        if (response?.success && response.data?.result) {
          const answer = this.parseSolvedResult(response.data.result, solver);
          this.cache.set(cacheKey, { answer, timestamp: Date.now(), flowId });
          log.info('CAPTCHA solved successfully');
          return answer;
        }

        const { retriable, message, retryAfterMs } = this.classifyError(null, response);
        lastError = new Error(message);

        if (!retriable || attempt === maxRetries - 1) {
          log.error('Non retriable or final attempt failed', { message });
          throw lastError;
        }

        // Respect Retry-After if provided, else use jittered backoff.
        const sleepMs = retryAfterMs ?? this.nextBackoffMs(backoff, base, factor, maxDelay);
        backoff = Math.min(maxDelay, Math.max(base, sleepMs)); // progress backoff window
        log.warn(`Attempt failed: ${message}. Sleeping ${sleepMs}ms before retry.`);
        await new Promise(r => setTimeout(r, Math.min(sleepMs, Math.max(0, totalDeadlineMs - (Date.now() - start)))));
      } catch (error) {
        const { retriable, message, retryAfterMs } = this.classifyError(error);
        lastError = new Error(message);
        if (!retriable || Date.now() - start >= totalDeadlineMs || attempt === maxRetries - 1) {
          log.error(`CAPTCHA solve error on attempt ${attempt + 1}`, { error: message });
          break;
        }
        const sleepMs = retryAfterMs ?? this.nextBackoffMs(backoff, base, factor, maxDelay);
        backoff = Math.min(maxDelay, Math.max(base, sleepMs));
        log.warn(`Transient error. Sleeping ${sleepMs}ms before retry.`);
        await new Promise(r => setTimeout(r, Math.min(sleepMs, Math.max(0, totalDeadlineMs - (Date.now() - start)))));
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
