import React from 'react';
import { AlertTriangle, Info, ShieldAlert, ShieldCheck } from 'lucide-react';
import type { DecisionVerdict } from '../../types';

interface StatusBadgeProps {
  status: DecisionVerdict | string;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  size = 'md',
  showIcon = true,
}) => {
  const normalized = status.toUpperCase();

  let color = 'var(--text-secondary)';
  let bg = 'var(--bg-subtle)';
  let border = 'var(--border-subtle)';
  let IconComponent = Info;

  switch (normalized) {
    case 'ACCEPT':
    case 'VALID':
    case 'CLEAN':
    case 'PASS':
      color = 'var(--verdict-accept)';
      bg = 'var(--verdict-accept-bg)';
      border = 'var(--verdict-accept-border)';
      IconComponent = ShieldCheck;
      break;

    case 'SUSPICIOUS':
    case 'ANOMALOUS':
    case 'INCOMPLETE':
    case 'CONFLICTING':
    case 'INCOMPATIBLE_CONTEXT':
      color = 'var(--verdict-suspicious)';
      bg = 'var(--verdict-suspicious-bg)';
      border = 'var(--verdict-suspicious-border)';
      IconComponent = AlertTriangle;
      break;

    case 'ATTACK':
    case 'FAIL':
    case 'SECURITY_VIOLATION':
    case 'AUTHENTICATION_FAILED':
    case 'IDENTITY_MISMATCH':
    case 'UNAUTHORIZED':
      color = 'var(--verdict-attack)';
      bg = 'var(--verdict-attack-bg)';
      border = 'var(--verdict-attack-border)';
      IconComponent = ShieldAlert;
      break;

    default:
      IconComponent = Info;
  }

  const sizeStyles = {
    sm: { padding: '0.15rem 0.45rem', fontSize: '0.72rem', iconSize: 12 },
    md: { padding: '0.25rem 0.65rem', fontSize: '0.8rem', iconSize: 14 },
    lg: { padding: '0.4rem 0.9rem', fontSize: '0.92rem', iconSize: 18 },
  }[size];

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.35rem',
        backgroundColor: bg,
        color: color,
        border: `1px solid ${border}`,
        borderRadius: 'var(--radius-full)',
        padding: sizeStyles.padding,
        fontSize: sizeStyles.fontSize,
        fontWeight: 600,
        letterSpacing: '0.03em',
        textTransform: 'uppercase',
        lineHeight: 1,
        whiteSpace: 'nowrap',
      }}
    >
      {showIcon && <IconComponent size={sizeStyles.iconSize} />}
      <span>{normalized}</span>
    </span>
  );
};
