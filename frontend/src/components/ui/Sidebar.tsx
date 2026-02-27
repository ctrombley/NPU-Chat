import { type ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface SidebarProps {
  title: string;
  children: ReactNode;
  className?: string;
}

const Sidebar = ({ title, children, className }: SidebarProps) => (
  <div className={cn('w-48 h-full bg-sidebar-bg border-r border-gray-600 overflow-y-auto z-10', className)}>
    <h3 className="m-2.5 text-white text-base border-b border-gray-600 pb-1.5">
      {title}
    </h3>
    {children}
  </div>
);

export { Sidebar };
