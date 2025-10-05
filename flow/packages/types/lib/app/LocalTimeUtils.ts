import { type LocalTime } from './index.js';

export class LocalTimeUtils {
  static toMinutesOfDay({ hour, minute }: { hour: number; minute: number }): number {
    return hour * 60 + minute;
  }

  static toSecondsOfDay({ hour, minute, second = 0 }: { hour: number; minute: number; second?: number }): number {
    return hour * 3600 + minute * 60 + second;
  }
}
