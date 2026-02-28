import { forwardRef, type LiHTMLAttributes } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const listItemVariants = cva(
  'flex justify-between items-center p-2.5 cursor-pointer border-b border-theme-border transition-colors hover:bg-theme-highlight text-theme-fg',
  {
    variants: {
      active: {
        true: 'bg-theme-active-bg border-l-4 border-l-theme-active',
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
