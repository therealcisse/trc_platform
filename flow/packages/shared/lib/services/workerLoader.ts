// workerLoader.ts
export type LoadedWorker = {
  worker: Worker;
  url: string; // blob URL, kept alive until stop() is called
  stop: () => void; // terminates the worker and revokes the blob URL
};

/**
 * Load an extension packaged worker script as a same-origin Blob and construct a Worker.
 * @param extScriptPath Path inside your extension bundle, for example "ticker.worker.iife.js".
 * @param workerType "classic" is the safest choice when using a Blob URL. Defaults to "classic".
 */
export async function loadExtensionWorkerAsBlob(
  extScriptPath: string,
  workerType: 'classic' | 'module' = 'classic',
): Promise<LoadedWorker> {
  // 1) Build an extension URL for the packaged file and fetch its source.
  const url = chrome.runtime.getURL(extScriptPath);
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) throw new Error(`Failed to fetch worker script ${extScriptPath}: ${res.status}`);
  const code = await res.text();

  // 2) Create a Blob URL on the page origin so Worker() is same origin.
  const blob = new Blob([code], { type: 'text/javascript' });
  const blobUrl = URL.createObjectURL(blob);

  // 3) Start the worker.
  const worker = workerType === 'module' ? new Worker(blobUrl, { type: 'module' }) : new Worker(blobUrl); // classic

  const stop = () => {
    try {
      worker.postMessage({ type: 'stop' });
    } catch {}
    try {
      worker.terminate();
    } catch {}
    URL.revokeObjectURL(blobUrl);
  };

  return { worker, url: blobUrl, stop };
}
