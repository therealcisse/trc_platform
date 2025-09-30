import { describe, it, expect, beforeEach, afterEach, vi, type MockInstance } from 'vitest';

// 1) Declare mocks BEFORE importing the SUT.
vi.mock('@extension/shared', () => {
  const logs: any[] = [];
  const Log = {
    withFlow: vi.fn(() => ({
      info: vi.fn((...a: any[]) => logs.push(['info', ...a])),
      warn: vi.fn((...a: any[]) => logs.push(['warn', ...a])),
      error: vi.fn((...a: any[]) => logs.push(['error', ...a])),
    })),
  };
  return {
    Log,
    // This is a real Vitest mock function
    sendBackgroundCommand: vi.fn(),
  };
});

vi.mock('@extension/types', () => ({
  MATCHER_IDS: { BUY_OFFER: 'BUY_OFFER' },
}));

vi.mock('@src/lib', () => ({
  extractNumericAnswer: vi.fn((s: string) => {
    const m = s.match(/\d+/);
    return m ? m[0] : '';
  }),
}));

// 2) Import the SUT and the mocked namespace AFTER mocks are declared.
import * as Shared from '@extension/shared';
import { CaptchaProcessor } from './CaptchaProcessor';

// Handy typed accessor to the real mock function:
const send = () => Shared.sendBackgroundCommand as unknown as MockInstance;

describe('CaptchaProcessor', () => {
  let processor: CaptchaProcessor;

  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2025-09-30T10:00:00.000Z'));

    // Polyfill AbortSignal.any for Node if needed
    if (!(AbortSignal as any).any) {
      (AbortSignal as any).any = function any(signals: AbortSignal[]): AbortSignal {
        const controller = new AbortController();
        const onAbort = () => controller.abort();
        signals.forEach(s => {
          if (s.aborted) controller.abort();
          else s.addEventListener('abort', onAbort, { once: true });
        });
        return controller.signal;
      };
    }

    // Reset all mocks between tests
    vi.resetAllMocks();

    // Reset singleton internal state between tests
    processor = CaptchaProcessor.getInstance();
    (processor as any).cache.clear();
    (processor as any).inFlight.clear();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('solves and caches on first successful attempt', async () => {
    send().mockResolvedValueOnce({ success: true, data: { result: 'answer=1234' } });

    const result = await processor.solveCaptcha('https://x/y/abc.png', 'data:image/png;base64,AAA', 'flow-1');
    expect(result).toBe('1234');

    const result2 = await processor.solveCaptcha('https://x/y/abc.png', 'data:image/png;base64,AAA', 'flow-1');
    expect(result2).toBe('1234');
    expect(send()).toHaveBeenCalledTimes(1);
  });

  it('cache expires after duration', async () => {
    send().mockResolvedValue({ success: true, data: { result: 'answer=4321' } });
    const keyImg = 'https://x/y/abc.png';

    const first = await processor.solveCaptcha(keyImg, 'data:image/png;base64,AAA', 'flow-1');
    expect(first).toBe('4321');
    expect(send()).toHaveBeenCalledTimes(1);

    vi.advanceTimersByTime(5 * 60 * 1000 + 1);

    send().mockResolvedValueOnce({ success: true, data: { result: 'answer=1111' } });
    const second = await processor.solveCaptcha(keyImg, 'data:image/png;base64,AAA', 'flow-1');
    expect(second).toBe('1111');
    expect(send()).toHaveBeenCalledTimes(2);
  });

  it('deduplicates in-flight requests for the same key', async () => {
    let resolveBackend!: (v: any) => void;
    const p = new Promise(res => (resolveBackend = res));
    send().mockReturnValueOnce(p);

    const call1 = processor.solveCaptcha('https://x/y/same.png', 'data:image/png;base64,AAA', 'flow-2');
    const call2 = processor.solveCaptcha('https://x/y/same.png', 'data:image/png;base64,AAA', 'flow-2');
    expect(send()).toHaveBeenCalledTimes(1);

    resolveBackend({ success: true, data: { result: 'ok 9876' } });
    const [r1, r2] = await Promise.all([call1, call2]);
    expect(r1).toBe('9876');
    expect(r2).toBe('9876');

    const r3 = await processor.solveCaptcha('https://x/y/same.png', 'data:image/png;base64,AAA', 'flow-2');
    expect(r3).toBe('9876');
    expect(send()).toHaveBeenCalledTimes(1);
  });

  it('retries on transient errors with jittered backoff and respects Retry-After', async () => {
    send()
      .mockResolvedValueOnce({ success: false, code: 503, error: 'Service unavailable', retryAfter: 2 })
      .mockResolvedValueOnce({ success: false, code: 500, error: 'Temporary' })
      .mockResolvedValueOnce({ success: true, data: { result: 'num=2222' } });

    const promise = processor.solveCaptcha('https://a/b/c1.png', 'data:image/png;base64,BBB', 'flow-3');

    await vi.advanceTimersByTimeAsync(2000);
    await vi.advanceTimersByTimeAsync(10_000);

    const result = await promise;
    expect(result).toBe('2222');
    expect(send()).toHaveBeenCalledTimes(3);
  });

  it('stops retrying on non-retriable errors', async () => {
    send().mockResolvedValueOnce({ success: false, code: 400, error: 'Bad request' });

    await expect(
      processor.solveCaptcha('https://a/b/c2.png', 'data:image/png;base64,CCC', 'flow-4', 5),
    ).rejects.toThrow(/Bad request/i);

    expect(send()).toHaveBeenCalledTimes(1);
  });

  it('enforces per attempt timeout and total deadline', async () => {
    // Simulate a hung backend
    send().mockImplementation(() => new Promise(() => {}));
    // Use tiny timeouts so the test finishes in milliseconds
    const p = processor.solveCaptcha('https://a/b/slow.png', 'data:image/png;base64,DDD', 'flow-5', 3, {
      perAttemptTimeoutMs: 200,
      totalDeadlineMs: 1000,
    });
    await vi.advanceTimersByTimeAsync(1_200);
    await expect(p).rejects.toThrow(/timeout|Failed|solve/i);
    expect(send().mock.calls.length).toBeGreaterThanOrEqual(2);
    // Drain any pending timers to avoid post-test rejections
    await vi.runOnlyPendingTimersAsync();
  });

  it('handles thrown network errors as retriable with backoff', async () => {
    send()
      .mockImplementationOnce(() => {
        throw new Error('Network error');
      })
      .mockImplementationOnce(() => {
        throw new Error('Temporary outage');
      })
      .mockResolvedValueOnce({ success: true, data: { result: 'val=9999' } });

    const promise = processor.solveCaptcha('https://a/b/c3.png', 'data:image/png;base64,EEE', 'flow-6');
    await vi.advanceTimersByTimeAsync(20_000);
    const result = await promise;
    expect(result).toBe('9999');
    expect(send()).toHaveBeenCalledTimes(3);
  });

  it('clearCacheForFlow removes only entries for the specified flow', async () => {
    send()
      .mockResolvedValueOnce({ success: true, data: { result: 'k=1111' } })
      .mockResolvedValueOnce({ success: true, data: { result: 'k=2222' } });

    const r1 = await processor.solveCaptcha('https://x/one.png', 'data:image/png;base64,FFF', 'flow-A');
    const r2 = await processor.solveCaptcha('https://x/two.png', 'data:image/png;base64,GGG', 'flow-B');
    expect(r1).toBe('1111');
    expect(r2).toBe('2222');

    processor.clearCacheForFlow('flow-A');

    send().mockResolvedValueOnce({ success: true, data: { result: 'k=3333' } });
    const r1b = await processor.solveCaptcha('https://x/one.png', 'data:image/png;base64,FFF', 'flow-A');
    const r2b = await processor.solveCaptcha('https://x/two.png', 'data:image/png;base64,GGG', 'flow-B');

    expect(r1b).toBe('3333');
    expect(r2b).toBe('2222');
    expect(send()).toHaveBeenCalledTimes(3);
  });

  it('clearCache wipes everything', async () => {
    send()
      .mockResolvedValueOnce({ success: true, data: { result: 'm=1010' } })
      .mockResolvedValueOnce({ success: true, data: { result: 'm=2020' } });
    await processor.solveCaptcha('https://x/a.png', 'data:image/png;base64,HHH', 'flow-C');
    await processor.solveCaptcha('https://x/b.png', 'data:image/png;base64,III', 'flow-D');

    processor.clearCache();

    send().mockResolvedValueOnce({ success: true, data: { result: 'm=3030' } });
    const r = await processor.solveCaptcha('https://x/a.png', 'data:image/png;base64,HHH', 'flow-C');
    expect(r).toBe('3030');
  });

  it('getCacheKey uses trailing segment', () => {
    const key1 = (processor as any).getCacheKey('https://server/a/b/image123.png', 'flow-Z');
    const key2 = (processor as any).getCacheKey('https://server/a/b/image123.png?x=1', 'flow-Z');

    // Your current implementation keeps the query string in the trailing segment.
    expect(key1).toContain('flow-Z:');
    expect(key1.endsWith('image123.png')).toBe(true);
    expect(key2.endsWith('image123.png?x=1')).toBe(true);
  });

  it('retries on transient server failures until retries exhausted', async () => {
    send()
      .mockResolvedValueOnce({ success: false, code: 502, error: 'Bad gateway' })
      .mockResolvedValueOnce({ success: false, code: 500, error: 'Server error' })
      .mockResolvedValueOnce({ success: false, code: 503, error: 'Service unavailable' })
      .mockResolvedValueOnce({ success: false, code: 500, error: 'Still broken' });

    const p = processor.solveCaptcha('https://server/odd.png', 'data:image/png;base64,JJJ', 'flow-Q', 4);

    // Drive the backoffs. Use a generous upper bound to cover jitter windows.
    await vi.advanceTimersByTimeAsync(40_000);

    await expect(p).rejects.toThrow();
    expect(send()).toHaveBeenCalledTimes(4);
  });
});
