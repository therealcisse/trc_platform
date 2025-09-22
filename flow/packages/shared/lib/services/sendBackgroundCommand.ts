import type { BackgroundCommands, CommandResponse } from '@extension/types';

// Background communication
export async function sendBackgroundCommand<T extends keyof BackgroundCommands>(
  command: T,
  payload: BackgroundCommands[T],
  timeoutMs?: number,
): Promise<CommandResponse> {
  const requestId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

  try {
    const message = {
      type: command,
      payload,
      timestamp: Date.now(),
      requestId,
    } as any;

    const response: CommandResponse = await new Promise((resolve, reject) => {
      let timer: ReturnType<typeof setTimeout> | null = null;
      if (timeoutMs && timeoutMs > 0) {
        timer = setTimeout(() => {
          reject(new Error(`Command ${String(command)} timed out after ${timeoutMs}ms`));
        }, timeoutMs);
      }

      chrome.runtime.sendMessage(message, (resp: CommandResponse) => {
        if (timer) clearTimeout(timer);
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
          return;
        }
        resolve(resp);
      });
    });

    return response;
  } catch (error) {
    console.error(`[Extension] Error sending background command ${command}:`, error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
      requestId,
    };
  }
}
