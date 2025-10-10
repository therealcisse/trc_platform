// ticker.worker.ts
// Dedicated Worker that executes a time-critical action exactly on the wall-clock second.

type StartMsg = { type: 'start'; spinWindowMs?: number; microSleepThresholdMs?: number };
type StopMsg = { type: 'stop' };
type Msg = StartMsg | StopMsg;

let stopped = false;

// At top-level, after your imports and types:
const workerId: string =
  typeof crypto.randomUUID === 'function'
    ? crypto.randomUUID()
    : (() => {
        const a = new Uint8Array(16);
        crypto.getRandomValues(a); // available in workers
        // Simple hex UUID v4 formatting from 16 random bytes
        a[6] = (a[6] & 0x0f) | 0x40;
        a[8] = (a[8] & 0x3f) | 0x80;
        const h = Array.from(a, b => b.toString(16).padStart(2, '0')).join('');
        return `${h.slice(0, 8)}-${h.slice(8, 12)}-${h.slice(12, 16)}-${h.slice(16, 20)}-${h.slice(20)}`;
      })();

let seq = 0; // monotonic per worker
let startCount = 0; // monotonic per worker

// Detect SAB availability. In a content-script worker this depends on the page’s COOP/COEP.
const sabSupported = typeof SharedArrayBuffer !== 'undefined' && (self as any).crossOriginIsolated === true;
const sab = sabSupported ? new SharedArrayBuffer(4) : null;
const ia = sab ? new Int32Array(sab) : null;

function perfTargetForWallTime(targetWallMs: number): number {
  const nowWall = Date.now();
  const nowPerf = performance.now();
  return nowPerf + (targetWallMs - nowWall);
}

function scheduleNext(spinWindowMs: number, microSleepThresholdMs: number) {
  if (stopped) return;

  const now = Date.now();
  const nextWhole = Math.floor(now / 1000) * 1000 + 1000;
  const msUntil = nextWhole - now;
  const coarse = Math.max(0, msUntil - spinWindowMs);

  const go = () => preSpin(nextWhole, spinWindowMs, microSleepThresholdMs);
  if (coarse > 0) setTimeout(go, coarse);
  else go();
}

function preSpin(targetWallMs: number, spinWindowMs: number, microSleepThresholdMs: number) {
  if (stopped) return;

  let targetPerf = perfTargetForWallTime(targetWallMs);

  // Micro sleep loop: yield in tiny slices, then finish with a short spin.
  while (!stopped) {
    const nowPerf = performance.now();
    const remain = targetPerf - nowPerf;
    if (remain <= microSleepThresholdMs) break;

    const slice = Math.max(0, Math.min(remain - 0.5, 2)); // up to 2 ms

    if (slice > 0) {
      if (sabSupported && ia) {
        Atomics.wait(ia, 0, 0, slice);
      } else {
        // Fallback without SAB. Timers may be clamped in background tabs.
        // Use a short timeout and guard it with a bounded spin.
        const sleep = Math.min(1, Math.max(0, slice));
        let fired = false;
        const t0 = performance.now();
        const id = setTimeout(() => {
          fired = true;
        }, sleep);
        while (!fired && performance.now() - t0 < sleep + 0.6) {
          /* light spin */
        }
        clearTimeout(id);
      }
      // Refresh mapping to absorb any wall-clock nudges.
      targetPerf = perfTargetForWallTime(targetWallMs);
    } else {
      break;
    }
  }

  // Final tight spin for the last few hundred microseconds.
  while (!stopped && performance.now() < targetPerf) {
    /* spin */
  }
  if (stopped) return;

  // Notify the host for any main-thread follow-up.
  (postMessage as any)({
    type: 'tick',
    workerId,
    seq: seq++,
    startCount,
    scheduledWallTimeMs: targetWallMs,
  });

  scheduleNext(spinWindowMs, microSleepThresholdMs);
}

onmessage = (e: MessageEvent<Msg>) => {
  const msg = e.data;
  if (msg.type === 'start') {
    startCount++;
    stopped = false;
    const spinWindowMs = msg.spinWindowMs ?? 5;
    const microSleepThresholdMs = msg.microSleepThresholdMs ?? 1;
    scheduleNext(spinWindowMs, microSleepThresholdMs);
  } else if (msg.type === 'stop') {
    stopped = true;
  }
};
