import React from 'react';
import { Database, Plus } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  message: string;
  actionText?: string;
  onAction?: () => void;
  minHeight?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No Records Found',
  message,
  actionText,
  onAction,
  minHeight = '180px',
}) => {
  return (
    <div
      className="card"
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight,
        gap: 'var(--space-3)',
        textAlign: 'center',
        padding: 'var(--space-6)',
      }}
    >
      <div
        style={{
          width: '44px',
          height: '44px',
          borderRadius: 'var(--radius-full)',
          background: 'var(--bg-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--text-muted)',
        }}
      >
        <Database size={22} />
      </div>

      <div>
        <h4 style={{ margin: 0, color: 'var(--text-primary)' }}>{title}</h4>
        <p style={{ margin: '0.25rem 0 0 0', color: 'var(--text-muted)', fontSize: '0.85rem' }}>{message}</p>
      </div>

      {actionText && onAction && (
        <button className="btn btn-primary" onClick={onAction} style={{ marginTop: '0.5rem' }}>
          <Plus size={14} />
          <span>{actionText}</span>
        </button>
      )}
    </div>
  );
};
