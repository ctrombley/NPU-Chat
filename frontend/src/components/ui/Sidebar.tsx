import { type ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface SidebarProps {
  title: string;
  children: ReactNode;
  footer?: ReactNode;
  className?: string;
  style?: React.CSSProperties;
}

const Sidebar = ({ title, children, footer, className, style }: SidebarProps) => (
  <div
    className={cn('h-full bg-theme-sidebar border-r border-theme-border z-10 flex-shrink-0 flex flex-col', className)}
    style={{ width: 192, minWidth: 120, maxWidth: 480, ...style }}
  >
    <h3 className="m-2.5 text-theme-fg text-base border-b border-theme-border pb-1.5 flex-shrink-0">
      {title}
    </h3>
    <div className="flex-1 overflow-y-auto">
      {children}
    </div>
    {footer && (
      <div className="flex-shrink-0">
        {footer}
      </div>
    )}
  </div>
);

export { Sidebar };
