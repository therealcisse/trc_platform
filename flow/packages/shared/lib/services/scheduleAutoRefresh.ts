import type { ExecutionConfig, OperationalHours } from '@extension/types';
import { LocalTime, LocalTimeUtils, MATCHER_IDS } from '@extension/types';
import { Log } from '../utils/logger.js';

// Use a module-scoped timer to ensure idempotency across calls
let intervalRef: ReturnType<typeof setInterval> | null = null;

function isWithinOperationalHours(operational: OperationalHours): boolean {
  // Compute using seconds-of-day with wrap-around support
  const now = LocalTime.now();
  const currentSeconds = LocalTimeUtils.toSecondsOfDay(now);

  // Day names are in English, match config keys
  const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'] as const;
  const today = new Date().getDay();
  const dayKey = dayNames[today];

  const cfg = operational[dayKey];
  if (!cfg || !cfg.enabled) return false;

  const minS = LocalTimeUtils.toSecondsOfDay(cfg.min);
  const maxS = LocalTimeUtils.toSecondsOfDay(cfg.max);

  if (minS <= maxS) {
    // Simple range [min, max]
    return currentSeconds >= minS && currentSeconds <= maxS;
  }
  // Wrap-around range [min..24h) U [0..max]
  return currentSeconds >= minS || currentSeconds <= maxS;
}

export function scheduleAutoRefresh(page: 'inbox' | 'item', config: ExecutionConfig): void {
  const log = new Log(MATCHER_IDS.AUTO_REFRESH);

  // Clear any existing interval first to keep idempotent behavior
  if (intervalRef) {
    clearInterval(intervalRef);
    intervalRef = null;
  }

  const intervalMs = config.inboxAutoRefreshMs;

  if (intervalMs < 0) {
    log.info('Auto-refreshing disabled...');
    return;
  }

  // Tick every second and reload when outside hours and elapsed >= interval
  const startTime = Date.now();
  log.info(
    `Scheduling auto-refresh every ${Math.round(intervalMs / 60000)} minutes, active only outside operational hours.`,
  );

  intervalRef = setInterval(() => {
    // Only consider reloads outside operational hours
    if (isWithinOperationalHours(config.operationalHours)) {
      // Do nothing while within operational hours
      return;
    }

    const elapsed = Date.now() - startTime;
    if (elapsed >= intervalMs) {
      log.info(`Auto-refreshing ${page}...`);
      window.location.reload();
    }
  }, 1000);
}

export function cleanupAutoRefresh(): void {
  if (intervalRef) {
    clearInterval(intervalRef);
    intervalRef = null;
  }
}
