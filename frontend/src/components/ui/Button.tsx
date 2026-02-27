import { forwardRef, type ButtonHTMLAttributes } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  'border-none rounded cursor-pointer text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed',
  {
    variants: {
      variant: {
        primary:
          'bg-accent text-white hover:bg-accent-hover',
        secondary:
          'bg-gray-600 text-white hover:bg-gray-700',
        send:
          'p-3 border border-purple-800 bg-gray-900 text-purple-500 rounded-3xl cursor-pointer text-2xl hover:text-white hover:shadow-lg hover:shadow-green-400 transition-colors disabled:hover:shadow-none disabled:hover:text-purple-500',
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
  'bg-none border-none text-gray-500 text-base cursor-pointer p-0.5 rounded transition-colors',
  {
    variants: {
      variant: {
        danger: 'hover:text-red-400 hover:bg-gray-600',
        favorite: 'hover:text-yellow-400 hover:bg-gray-600 mr-1',
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
