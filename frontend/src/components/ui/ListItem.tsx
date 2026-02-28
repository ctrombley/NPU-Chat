import { forwardRef, type LiHTMLAttributes } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const listItemVariants = cva(
  'flex justify-between items-center p-2.5 cursor-pointer border-b border-tn-border transition-colors hover:bg-tn-bg-highlight',
  {
    variants: {
      active: {
        true: 'bg-tn-selection border-l-4 border-l-tn-blue',
        false: '',
      },
    },
    defaultVariants: {
      active: false,
    },
  }
);

export interface ListItemProps
  extends LiHTMLAttributes<HTMLLIElement>,
    VariantProps<typeof listItemVariants> {}

const ListItem = forwardRef<HTMLLIElement, ListItemProps>(
  ({ className, active, ...props }, ref) => (
    <li
      ref={ref}
      className={cn(listItemVariants({ active }), className)}
      {...props}
    />
  )
);
ListItem.displayName = 'ListItem';

export { ListItem, listItemVariants };
