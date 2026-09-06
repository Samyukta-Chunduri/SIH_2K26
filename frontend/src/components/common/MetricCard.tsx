import React from 'react';
import { CheckCircle2, AlertTriangle } from 'lucide-react';

interface MetricCardProps {
  label: string;
  observed: number | string | null | undefined;
  expected?: number | string | null;
  threshold?: number | string | null;
  unit?: string;
  isAnomalous?: boolean;
  description?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  observed,
  expected,
  threshold,
  unit = '',
  isAnomalous = false,
  description,
}) => {
  const isAvailable = observed !== null && observed !== undefined;

  return (
    <div
      className="card"
      style={{
        borderLeft: isAvailable && isAnomalous
          ? '4px solid var(--verdict-suspicious)'
          : isAvailable
          ? '4px solid var(--verdict-accept)'
          : '4px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        minHeight: '120px',
      }}
    >
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
            {label}
          </span>
          {isAvailable && (
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.2rem',
                fontSize: '0.7rem',
                fontWeight: 600,
                color: isAnomalous ? 'var(--verdict-suspicious)' : 'var(--verdict-accept)',
                background: isAnomalous ? 'var(--verdict-suspicious-bg)' : 'var(--verdict-accept-bg)',
                padding: '0.15rem 0.4rem',
                borderRadius: 'var(--radius-sm)',
              }}
            >
              {isAnomalous ? <AlertTriangle size={11} /> : <CheckCircle2 size={11} />}
              {isAnomalous ? 'ANOMALOUS' : 'NORMAL'}
            </span>
          )}
        </div>

        <div style={{ fontSize: '1.6rem', fontWeight: 700, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
          {isAvailable ? `${observed}${unit}` : <span style={{ color: 'var(--text-muted)', fontSize: '1rem' }}>Not available</span>}
        </div>
      </div>

      <div style={{ marginTop: 'var(--space-3)', paddingTop: 'var(--space-2)', borderTop: '1px solid var(--border-subtle)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
        {expected !== undefined && expected !== null && (
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>Honest Baseline:</span>
            <span style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>{expected}{unit}</span>
          </div>
        )}
        {threshold !== undefined && threshold !== null && (
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>Policy Threshold:</span>
            <span style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>{threshold}{unit}</span>
          </div>
        )}
        {description && <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.72rem' }}>{description}</p>}
      </div>
    </div>
  );
};
