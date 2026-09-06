import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingStateProps {
  message?: string;
  minHeight?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'Loading Q-SHIELD telemetry...',
  minHeight = '200px',
}) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight,
        gap: 'var(--space-3)',
        color: 'var(--text-secondary)',
      }}
    >
      <Loader2
        size={32}
        style={{
          color: 'var(--accent-cyan)',
          animation: 'spin 1s linear infinite',
        }}
      />
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
      <span style={{ fontSize: '0.875rem' }}>{message}</span>
    </div>
  );
};
