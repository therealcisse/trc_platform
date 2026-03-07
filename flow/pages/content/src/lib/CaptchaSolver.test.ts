import { CaptchaSolver } from './CaptchaSolver';
import * as Shared from '@extension/shared';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import type { MockInstance } from 'vitest';
import { CaptchaSolverType } from '@extension/types';

// 2) Import the SUT and the mocked namespace AFTER mocks are declared.

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
  const sendBackgroundCommand = vi.fn();
  return {
    Log,
    sendBackgroundCommand,
  };
});

vi.mock('@extension/types', () => ({
  MATCHER_IDS: { BUY_OFFER: 'BUY_OFFER' },
  CaptchaSolverType: {
    Math: 'math',
    Text: 'text',
  },
}));

vi.mock('@src/lib', () => ({
  extractNumericAnswer: vi.fn((s: string) => {
    const m = s.match(/\d+/);
    return m ? m[0] : '';
  }),
}));

// Handy typed accessor to the real mock function:
const send = () => Shared.sendBackgroundCommand as unknown as MockInstance;

describe('CaptchaSolver', () => {
  let solver: CaptchaSolver;

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
    solver = CaptchaSolver.getInstance();
    (solver as any).cache.clear();
    (solver as any).inFlight.clear();
  });

  afterEach(async () => {
    // Drain pending timers to avoid unhandled rejections surfacing after the test completes.
    try {
      await vi.runOnlyPendingTimersAsync();
    } catch {
      // ignore
    }
    vi.useRealTimers();
  });

  it('solves and caches on first successful attempt', async () => {
    send().mockResolvedValueOnce({ success: true, data: { result: 'answer=1234' } });

    const result = await solver.solveCaptcha('https://x/y/abc.png', 'data:image/png;base64,AAA', 'flow-1');
    expect(result).toBe('1234');

    const result2 = await solver.solveCaptcha('https://x/y/abc.png', 'data:image/png;base64,AAA', 'flow-1');
    expect(result2).toBe('1234');
    expect(send()).toHaveBeenCalledTimes(1);
  });

  it('cache expires after duration', async () => {
    send().mockResolvedValue({ success: true, data: { result: 'answer=4321' } });
    const keyImg = 'https://x/y/abc.png';

    const first = await solver.solveCaptcha(keyImg, 'data:image/png;base64,AAA', 'flow-1');
    expect(first).toBe('4321');
    expect(send()).toHaveBeenCalledTimes(1);

    vi.advanceTimersByTime(5 * 60 * 1000 + 1);

    send().mockResolvedValueOnce({ success: true, data: { result: 'answer=1111' } });
    const second = await solver.solveCaptcha(keyImg, 'data:image/png;base64,AAA', 'flow-1');
    expect(second).toBe('1111');
    expect(send()).toHaveBeenCalledTimes(2);
  });

  it('deduplicates in-flight requests for the same key', async () => {
    let resolveBackend!: (v: any) => void;
    const p = new Promise(res => (resolveBackend = res));
    send().mockReturnValueOnce(p);

    const call1 = solver.solveCaptcha('https://x/y/same.png', 'data:image/png;base64,AAA', 'flow-2');
    const call2 = solver.solveCaptcha('https://x/y/same.png', 'data:image/png;base64,AAA', 'flow-2');

    // sendBackgroundCommand is invoked via a microtask inside withTimeout.
    await Promise.resolve();

    expect(send()).toHaveBeenCalledTimes(1);

    resolveBackend({ success: true, data: { result: 'ok 9876' } });
    const [r1, r2] = await Promise.all([call1, call2]);
    expect(r1).toBe('9876');
    expect(r2).toBe('9876');

    const r3 = await solver.solveCaptcha('https://x/y/same.png', 'data:image/png;base64,AAA', 'flow-2');
    expect(r3).toBe('9876');
    expect(send()).toHaveBeenCalledTimes(1);
  });

  it('retries on transient errors with jittered backoff and respects Retry-After', async () => {
    send()
      .mockResolvedValueOnce({ success: false, code: 503, error: 'Service unavailable', retryAfter: 2 })
      .mockResolvedValueOnce({ success: false, code: 500, error: 'Temporary' })
      .mockResolvedValueOnce({ success: true, data: { result: 'num=2222' } });

    const promise = solver.solveCaptcha('https://a/b/c1.png', 'data:image/png;base64,BBB', 'flow-3');

    await vi.advanceTimersByTimeAsync(2000);
    await vi.advanceTimersByTimeAsync(10_000);

    const result = await promise;
    expect(result).toBe('2222');
    expect(send()).toHaveBeenCalledTimes(3);
  });

  it('stops retrying on non-retriable errors', async () => {
    send().mockResolvedValueOnce({ success: false, code: 400, error: 'Bad request' });

    await expect(
      solver.solveCaptcha('https://a/b/c2.png', 'data:image/png;base64,CCC', 'flow-4', CaptchaSolverType.Math, 5),
    ).rejects.toThrow(/Bad request/i);

    expect(send()).toHaveBeenCalledTimes(1);
  });

  it('enforces per attempt timeout and total deadline', async () => {
    // Simulate a hung backend
    send().mockImplementation(() => new Promise(() => {}));

    // Attach the rejection handler immediately to avoid unhandled rejection warnings.
    const p = solver.solveCaptcha(
      'https://a/b/slow.png',
      'data:image/png;base64,DDD',
      'flow-5',
      CaptchaSolverType.Math,
      3,
      {
        perAttemptTimeoutMs: 200,
        totalDeadlineMs: 1000,
      },
    );
    const assertion = expect(p).rejects.toThrow(/timeout|Failed|solve/i);

    await vi.advanceTimersByTimeAsync(1_200);
    await assertion;

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

    const promise = solver.solveCaptcha('https://a/b/c3.png', 'data:image/png;base64,EEE', 'flow-6');
    await vi.advanceTimersByTimeAsync(20_000);
    const result = await promise;
    expect(result).toBe('9999');
    expect(send()).toHaveBeenCalledTimes(3);
  });

  it('always calls image.solve.local and passes the solver type in payload', async () => {
    send().mockResolvedValueOnce({ success: true, data: { result: 'answer=5555' } });

    const result = await solver.solveCaptcha(
      'https://local/test.png',
      'data:image/png;base64,LLL',
      'flow-local',
      CaptchaSolverType.Math,
    );
    expect(result).toBe('5555');
    expect(send()).toHaveBeenCalledTimes(1);

    const [command, payload] = send().mock.calls[0];
    expect(command).toBe('image.solve.local');
    expect(payload).toMatchObject({ flowId: 'flow-local', solver: CaptchaSolverType.Math });
  });

  it('returns case sensitive text when solver is Text', async () => {
    send().mockResolvedValueOnce({ success: true, data: { result: 'AbC123xYz' } });

    const result = await solver.solveCaptcha(
      'https://x/y/txt.png',
      'data:image/png;base64,TXT',
      'flow-text',
      CaptchaSolverType.Text,
    );

    expect(result).toBe('AbC123xYz');
  });

  it('normalizes space-separated characters in text mode to a contiguous string', async () => {
    send().mockResolvedValueOnce({ success: true, data: { result: 'r b k d' } });

    const result = await solver.solveCaptcha(
      'https://x/y/txt-space.png',
      'data:image/png;base64,TXTSPACE',
      'flow-text-space',
      CaptchaSolverType.Text,
    );

    expect(result).toBe('rbkd');
  });

  it('strips outer quotes then normalizes inner spaces for text captchas', async () => {
    send().mockResolvedValueOnce({ success: true, data: { result: "  ' r b k d '  " } });

    const result = await solver.solveCaptcha(
      'https://x/y/txt-quoted.png',
      'data:image/png;base64,TXTQUOTED',
      'flow-text-quoted',
      CaptchaSolverType.Text,
    );

    expect(result).toBe('rbkd');
  });

  it('collapses word-level spaces like "AB CD" into "ABCD" in text mode', async () => {
    send().mockResolvedValueOnce({ success: true, data: { result: 'AB CD' } });

    const result = await solver.solveCaptcha(
      'https://x/y/txt-abcd.png',
      'data:image/png;base64,TXTABCD',
      'flow-text-abcd',
      CaptchaSolverType.Text,
    );

    expect(result).toBe('ABCD');
  });

  it('collapses newline-separated characters into a contiguous string in text mode', async () => {
    send().mockResolvedValueOnce({ success: true, data: { result: 'r\nb\nk\nd' } });

    const result = await solver.solveCaptcha(
      'https://x/y/txt-newlines.png',
      'data:image/png;base64,TXTNEWLINES',
      'flow-text-newlines',
      CaptchaSolverType.Text,
    );

    expect(result).toBe('rbkd');
  });

  it('preserves the explicit ERROR: Unreadable sentinel in text mode', async () => {
    send().mockResolvedValueOnce({ success: true, data: { result: 'ERROR: Unreadable' } });

    const result = await solver.solveCaptcha(
      'https://x/y/txt-error.png',
      'data:image/png;base64,TXTERROR',
      'flow-text-error',
      CaptchaSolverType.Text,
    );

    expect(result).toBe('ERROR: Unreadable');
  });

  it('does not reuse cache between different solver types', async () => {
    send()
      .mockResolvedValueOnce({ success: true, data: { result: 'AbC123' } })
      .mockResolvedValueOnce({ success: true, data: { result: 'AbC123' } });

    const mathResult = await solver.solveCaptcha(
      'https://x/y/same.png',
      'data:image/png;base64,SAME',
      'flow-sep',
      CaptchaSolverType.Math,
    );
    const textResult = await solver.solveCaptcha(
      'https://x/y/same.png',
      'data:image/png;base64,SAME',
      'flow-sep',
      CaptchaSolverType.Text,
    );

    expect(mathResult).toBe('123');
    expect(textResult).toBe('AbC123');
    expect(send()).toHaveBeenCalledTimes(2);
  });

  it('clearCacheForFlow removes only entries for the specified flow', async () => {
    send()
      .mockResolvedValueOnce({ success: true, data: { result: 'k=1111' } })
      .mockResolvedValueOnce({ success: true, data: { result: 'k=2222' } });

    const r1 = await solver.solveCaptcha('https://x/one.png', 'data:image/png;base64,FFF', 'flow-A');
    const r2 = await solver.solveCaptcha('https://x/two.png', 'data:image/png;base64,GGG', 'flow-B');
    expect(r1).toBe('1111');
    expect(r2).toBe('2222');

    solver.clearCacheForFlow('flow-A');

    send().mockResolvedValueOnce({ success: true, data: { result: 'k=3333' } });
    const r1b = await solver.solveCaptcha('https://x/one.png', 'data:image/png;base64,FFF', 'flow-A');
    const r2b = await solver.solveCaptcha('https://x/two.png', 'data:image/png;base64,GGG', 'flow-B');

    expect(r1b).toBe('3333');
    expect(r2b).toBe('2222');
    expect(send()).toHaveBeenCalledTimes(3);
  });

  it('clearCache wipes everything', async () => {
    send()
      .mockResolvedValueOnce({ success: true, data: { result: 'm=1010' } })
      .mockResolvedValueOnce({ success: true, data: { result: 'm=2020' } });
    await solver.solveCaptcha('https://x/a.png', 'data:image/png;base64,HHH', 'flow-C');
    await solver.solveCaptcha('https://x/b.png', 'data:image/png;base64,III', 'flow-D');

    solver.clearCache();

    send().mockResolvedValueOnce({ success: true, data: { result: 'm=3030' } });
    const r = await solver.solveCaptcha('https://x/a.png', 'data:image/png;base64,HHH', 'flow-C');
    expect(r).toBe('3030');
  });

  it('getCacheKey uses trailing segment and strips query strings', () => {
    const key1 = (solver as any).getCacheKey('https://server/a/b/image123.png', 'flow-Z', CaptchaSolverType.Math);
    const key2 = (solver as any).getCacheKey('https://server/a/b/image123.png?x=1', 'flow-Z', CaptchaSolverType.Math);

    // Query strings are stripped so both keys end with the same filename
    expect(key1).toContain('flow-Z:');
    expect(key1.endsWith('image123.png')).toBe(true);
    expect(key2.endsWith('image123.png')).toBe(true);

    // URLs with and without query strings produce identical cache keys
    expect(key1).toBe(key2);
  });

  it('retries on transient server failures until retries exhausted', async () => {
    send()
      .mockResolvedValueOnce({ success: false, code: 502, error: 'Bad gateway' })
      .mockResolvedValueOnce({ success: false, code: 500, error: 'Server error' })
      .mockResolvedValueOnce({ success: false, code: 503, error: 'Service unavailable' })
      .mockResolvedValueOnce({ success: false, code: 500, error: 'Still broken' });

    const p = solver.solveCaptcha(
      'https://server/odd.png',
      'data:image/png;base64,JJJ',
      'flow-Q',
      CaptchaSolverType.Math,
      4,
    );
    const assertion = expect(p).rejects.toThrow();

    // Drive the backoffs. Use a generous upper bound to cover jitter windows.
    await vi.advanceTimersByTimeAsync(40_000);

    await assertion;
    expect(send()).toHaveBeenCalledTimes(4);
  });
});
