import { forwardRef, type HTMLAttributes } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const messageBubbleVariants = cva(
  'block mx-3 my-1 px-3.5 py-2.5 max-w-[75%] w-fit break-words text-left shadow-sm',
  {
    variants: {
      variant: {
        sent:
          'ml-auto mr-3 rounded-2xl rounded-br-sm bg-theme-bubble-sent text-theme-bubble-sent-fg',
        received:
          'ml-3 mr-auto rounded-2xl rounded-bl-sm bg-theme-bubble-received text-theme-bubble-received-fg relative group',
      },
    },
  }
);

export interface MessageBubbleProps
  extends HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof messageBubbleVariants> {}

const MessageBubble = forwardRef<HTMLDivElement, MessageBubbleProps>(
  ({ className, variant, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(messageBubbleVariants({ variant }), className)}
      {...props}
    />
  )
);
MessageBubble.displayName = 'MessageBubble';

export { MessageBubble, messageBubbleVariants };
