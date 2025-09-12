import type { ExtensionStorage } from '@extension/shared';

export type DayConfig = {
  enabled: boolean;
  min: number;
  max: number;
};

export type OperationalHours = {
  [key: number]: DayConfig;
};

export type OptionsFormData = ExtensionStorage['config'] & {
  enabled: boolean;
};

export const DAYS_OF_WEEK = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'] as const;

export type DayOfWeek = (typeof DAYS_OF_WEEK)[number];

export const DEFAULT_TIMEZONE = Intl.DateTimeFormat().resolvedOptions().timeZone;
