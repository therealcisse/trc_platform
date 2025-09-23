import { type LocalTime } from './index.js';

export class LocalTimeUtils {
  static toMinutesOfDay({ hour, minute }: { hour: number; minute: number }): number {
    return hour * 60 + minute;
  }
}
