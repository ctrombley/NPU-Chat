import { forwardRef, type HTMLAttributes } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const messageBubbleVariants = cva(
  'block m-2.5 p-2.5 text-tn-fg bg-transparent rounded-lg',
  {
    variants: {
      variant: {
        sent:
          'bg-message-sent w-11/12 max-w-11/12 ml-auto mr-0 border-l-2 border-tn-blue rounded-tl-3xl rounded-bl-3xl shadow-lg text-left word-wrap break-words pl-5',
        received:
          'bg-message-received w-4/5 shadow-lg border-r-2 border-tn-magenta rounded-tr-3xl rounded-br-3xl pt-1.5 pr-5 mr-12 mb-5 word-wrap break-words text-left relative group',
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
