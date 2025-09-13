import * as React from 'react';
import type { ComponentPropsWithoutRef } from 'react';
import { cn } from '../utils';

type LabelProps = ComponentPropsWithoutRef<'label'>;

const Label = React.forwardRef<HTMLLabelElement, LabelProps>(({ className, ...props }, ref) => {
  return (
    <label
      ref={ref}
      className={cn(
        'text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70',
        className,
      )}
      {...props}
    />
  );
});

Label.displayName = 'Label';

export { Label };
export type { LabelProps };
