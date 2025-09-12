import { type FC } from 'react';
import { cn } from '@extension/ui';
import type { DayConfig } from '../types';

interface TimeRangeSelectorProps {
  value: DayConfig;
  onChange: (value: DayConfig) => void;
  className?: string;
}

const TimeRangeSelector: FC<TimeRangeSelectorProps> = ({ value, onChange, className }) => {
  const { enabled, min, max } = value;

  const handleToggle = () => {
    onChange({ ...value, enabled: !enabled });
  };

  const handleMinChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newMin = parseInt(e.target.value, 10);
    onChange({ ...value, min: newMin });
  };

  const handleMaxChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newMax = parseInt(e.target.value, 10);
    onChange({ ...value, max: newMax });
  };

  const hours = Array.from({ length: 24 }, (_, i) => i);

  return (
    <div className={cn('flex items-center gap-4', className)}>
      <label className="inline-flex items-center">
        <input
          type="checkbox"
          checked={enabled}
          onChange={handleToggle}
          className="form-checkbox text-primary-600 focus:ring-primary-500 h-5 w-5 rounded border-gray-300"
        />
        <span className="ml-2">Enabled</span>
      </label>

      <div className="flex items-center gap-2">
        <select
          value={min}
          onChange={handleMinChange}
          disabled={!enabled}
          className="form-select focus:border-primary-500 focus:ring-primary-500 rounded-md border-gray-300 py-2 pl-3 pr-10 text-base focus:outline-none disabled:bg-gray-100">
          {hours.map(hour => (
            <option key={hour} value={hour}>
              {hour.toString().padStart(2, '0')}:00
            </option>
          ))}
        </select>

        <span>to</span>

        <select
          value={max}
          onChange={handleMaxChange}
          disabled={!enabled}
          className="form-select focus:border-primary-500 focus:ring-primary-500 rounded-md border-gray-300 py-2 pl-3 pr-10 text-base focus:outline-none disabled:bg-gray-100">
          {hours.map(hour => (
            <option key={hour} value={hour}>
              {hour.toString().padStart(2, '0')}:00
            </option>
          ))}
        </select>
      </div>
    </div>
  );
};

export default TimeRangeSelector;
