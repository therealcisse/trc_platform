import { cn } from '../utils';
import * as React from 'react';
import type { ComponentPropsWithoutRef } from 'react';

export interface SelectOption {
  value: string | number;
  label: string;
}

export interface SelectProps extends Omit<ComponentPropsWithoutRef<'select'>, 'value' | 'onChange'> {
  value?: string | number;
  options: SelectOption[];
  onChange?: (value: string) => void;
}

const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, value, options, onChange, ...props }, ref) => (
    <select
      ref={ref}
      value={value}
      onChange={e => onChange?.(e.target.value)}
      className={cn(
        'border-input bg-background ring-offset-background placeholder:text-muted-foreground focus-visible:ring-ring flex h-10 w-full rounded-md border px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
        className,
      )}
      {...props}>
      {options.map(option => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  ),
);

Select.displayName = 'Select';

export { Select };
