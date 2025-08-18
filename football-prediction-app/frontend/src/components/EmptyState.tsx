import type { ReactNode } from 'react';

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  message?: string;
  action?: ReactNode;
}

export function EmptyState({ icon, title, message, action }: EmptyStateProps) {
  return (
    <div className="text-center py-12">
      {icon && (
        <div className="mx-auto h-12 w-12 text-gray-400">{icon}</div>
      )}
      <h3 className="mt-2 text-sm font-medium text-gray-900">{title}</h3>
      {message && (
        <p className="mt-1 text-sm text-gray-500">{message}</p>
      )}
      {action && (
        <div className="mt-6">{action}</div>
      )}
    </div>
  );
}