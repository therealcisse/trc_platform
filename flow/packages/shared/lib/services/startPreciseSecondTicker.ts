import { loadExtensionWorkerAsBlob } from './workerLoader.js';

type TickMsg = {
  type: 'tick';
  scheduledWallTimeMs: number;
  workerId: string;
  seq: number;
  startCount: number;
};

type StartOpts = {
  spinWindowMs?: number; // default 5
  microSleepThresholdMs?: number; // default 1
};

export async function startPreciseSecondTicker(
  onTick: (ctx: {
    scheduledWallTimeMs: number;
    receivedWallTimeMs: number;
    driftMs: number;
    workerId: string;
    seq: number;
    startCount: number;
  }) => void,
  opts: StartOpts = {},
): Promise<void> {
  const { worker } = await loadExtensionWorkerAsBlob(`content/ticker.iife.js`, 'classic');

  const handleMessage = (e: MessageEvent<TickMsg>) => {
    const msg = e.data;
    if (!msg || msg.type !== 'tick') return;
    const now = Date.now();
    onTick({
      scheduledWallTimeMs: msg.scheduledWallTimeMs,
      receivedWallTimeMs: now,
      driftMs: now - msg.scheduledWallTimeMs,
      workerId: msg.workerId,
      seq: msg.seq,
      startCount: msg.startCount,
    });
  };

  worker.addEventListener('message', handleMessage);

  worker.postMessage({
    type: 'start',
    spinWindowMs: opts.spinWindowMs ?? 5,
    microSleepThresholdMs: opts.microSleepThresholdMs ?? 1,
  });

  window.addEventListener('pagehide', stop);
  window.addEventListener('beforeunload', stop);
}
