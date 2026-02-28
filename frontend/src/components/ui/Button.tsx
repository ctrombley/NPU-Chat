import { forwardRef, type ButtonHTMLAttributes } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  'border-none rounded cursor-pointer text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed',
  {
    variants: {
      variant: {
        primary:
          'bg-tn-blue text-tn-bg-dark hover:bg-tn-cyan',
        secondary:
          'bg-tn-bg-highlight text-tn-fg-dark hover:bg-tn-border',
        send:
          'p-3 border border-tn-border bg-tn-bg text-tn-blue rounded-3xl cursor-pointer text-2xl hover:text-tn-cyan hover:shadow-lg hover:shadow-tn-blue/30 transition-colors disabled:hover:shadow-none disabled:hover:text-tn-comment',
      },
      size: {
        sidebar: 'w-full p-2.5 m-2.5',
        compact: 'px-1 py-0.5 text-xs',
        icon: 'p-0',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'sidebar',
    },
  }
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button
      ref={ref}
      className={cn(buttonVariants({ variant, size }), className)}
      {...props}
    />
  )
);
Button.displayName = 'Button';

const iconButtonVariants = cva(
  'bg-none border-none text-tn-comment text-base cursor-pointer p-0.5 rounded transition-colors',
  {
    variants: {
      variant: {
        danger: 'hover:text-tn-red hover:bg-tn-bg-highlight',
        favorite: 'hover:text-tn-yellow hover:bg-tn-bg-highlight mr-1',
      },
    },
    defaultVariants: {
      variant: 'danger',
    },
  }
);

export interface IconButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof iconButtonVariants> {}

const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ className, variant, ...props }, ref) => (
    <button
      ref={ref}
      className={cn(iconButtonVariants({ variant }), className)}
      {...props}
    />
  )
);
IconButton.displayName = 'IconButton';

export { Button, IconButton, buttonVariants, iconButtonVariants };
