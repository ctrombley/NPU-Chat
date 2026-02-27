import { forwardRef, type LiHTMLAttributes } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const listItemVariants = cva(
  'flex justify-between items-center p-2.5 cursor-pointer border-b border-gray-600 transition-colors hover:bg-gray-700',
  {
    variants: {
      active: {
        true: 'bg-gray-600 border-l-4 border-accent',
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
