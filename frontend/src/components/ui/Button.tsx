import { forwardRef, type ButtonHTMLAttributes } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  'border-none rounded cursor-pointer text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed',
  {
    variants: {
      variant: {
        primary:
          'bg-theme-active text-white hover:opacity-90',
        secondary:
          'bg-theme-highlight text-theme-fg hover:bg-theme-border',
        send:
          'p-3 border border-theme-border bg-theme-bg text-theme-active rounded-3xl cursor-pointer text-2xl hover:opacity-80 hover:shadow-lg transition-colors disabled:hover:shadow-none disabled:opacity-50',
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
  'bg-none border-none text-theme-fg-muted text-base cursor-pointer p-0.5 rounded transition-colors',
  {
    variants: {
      variant: {
        danger: 'hover:text-tn-red hover:bg-theme-highlight',
        favorite: 'hover:text-tn-yellow hover:bg-theme-highlight mr-1',
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
