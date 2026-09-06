import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  minHeight?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Application Error',
  message,
  onRetry,
  minHeight = '160px',
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
        border: '1px solid var(--verdict-attack-border)',
        background: 'var(--verdict-attack-bg)',
        gap: 'var(--space-3)',
        textAlign: 'center',
        padding: 'var(--space-6)',
      }}
    >
      <div
        style={{
          width: '40px',
          height: '40px',
          borderRadius: 'var(--radius-full)',
          background: 'rgba(244, 63, 94, 0.2)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--verdict-attack)',
        }}
      >
        <AlertTriangle size={22} />
      </div>

      <div>
        <h4 style={{ margin: 0, color: 'var(--verdict-attack)' }}>{title}</h4>
        <p style={{ margin: '0.25rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{message}</p>
      </div>

      {onRetry && (
        <button className="btn btn-secondary" onClick={onRetry} style={{ marginTop: '0.5rem' }}>
          <RefreshCw size={14} />
          <span>Retry Request</span>
        </button>
      )}
    </div>
  );
};
