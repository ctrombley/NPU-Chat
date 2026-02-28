import { type ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface SidebarProps {
  title: string;
  children: ReactNode;
  className?: string;
  style?: React.CSSProperties;
}

const Sidebar = ({ title, children, className, style }: SidebarProps) => (
  <div
    className={cn('h-full bg-sidebar-bg border-r border-tn-border overflow-y-auto z-10 flex-shrink-0', className)}
    style={{ width: 192, minWidth: 120, maxWidth: 480, ...style }}
  >
    <h3 className="m-2.5 text-tn-fg text-base border-b border-tn-border pb-1.5">
      {title}
    </h3>
    {children}
  </div>
);

export { Sidebar };
