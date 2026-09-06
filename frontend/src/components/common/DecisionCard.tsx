import React from 'react';
import { ShieldCheck, AlertTriangle, ShieldAlert, Cpu, Hash, Clock, FileText } from 'lucide-react';
import type { SecurityEventSummary } from '../../types';
import { StatusBadge } from './StatusBadge';
import { HashDisplay } from './HashDisplay';

interface DecisionCardProps {
  event: SecurityEventSummary | null;
  title?: string;
  subtitle?: string;
}

export const DecisionCard: React.FC<DecisionCardProps> = ({
  event,
  title = 'Authoritative Security Verdict',
  subtitle = 'Evaluated strictly by M12 Final Decision Engine',
}) => {
  if (!event) {
    return (
      <div className="card" style={{ padding: 'var(--space-6)', textAlign: 'center' }}>
        <p style={{ color: 'var(--text-muted)' }}>No security verification event evaluated yet.</p>
      </div>
    );
  }

  const verdict = event.verdict;

  let borderColor = 'var(--border-card)';
  let glowColor = 'transparent';
  let IconComponent = ShieldCheck;
  let verdictColor = 'var(--verdict-accept)';

  if (verdict === 'ACCEPT') {
    borderColor = 'var(--verdict-accept-border)';
    glowColor = 'var(--verdict-accept-glow)';
    IconComponent = ShieldCheck;
    verdictColor = 'var(--verdict-accept)';
  } else if (verdict === 'SUSPICIOUS') {
    borderColor = 'var(--verdict-suspicious-border)';
    glowColor = 'var(--verdict-suspicious-glow)';
    IconComponent = AlertTriangle;
    verdictColor = 'var(--verdict-suspicious)';
  } else if (verdict === 'ATTACK') {
    borderColor = 'var(--verdict-attack-border)';
    glowColor = 'var(--verdict-attack-glow)';
    IconComponent = ShieldAlert;
    verdictColor = 'var(--verdict-attack)';
  }

  return (
    <div
      className="card"
      style={{
        border: `2px solid ${borderColor}`,
        boxShadow: `0 0 25px ${glowColor}`,
        background: 'linear-gradient(180deg, var(--bg-card) 0%, var(--bg-secondary) 100%)',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Top Banner indicating M12 Authority */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid var(--border-subtle)',
          paddingBottom: 'var(--space-3)',
          marginBottom: 'var(--space-4)',
        }}
      >
        <div>
          <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Cpu size={18} style={{ color: 'var(--accent-cyan)' }} />
            {title}
          </h3>
          <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--text-muted)' }}>{subtitle}</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span
            style={{
              fontSize: '0.7rem',
              fontWeight: 600,
              textTransform: 'uppercase',
              color: 'var(--accent-cyan)',
              background: 'var(--accent-cyan-subtle)',
              padding: '0.2rem 0.5rem',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid rgba(6, 182, 212, 0.25)',
            }}
          >
            M12 Authority
          </span>
          <StatusBadge status={verdict} size="lg" />
        </div>
      </div>

      {/* Main Verdict Display */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'auto 1fr',
          gap: 'var(--space-6)',
          alignItems: 'center',
          marginBottom: 'var(--space-5)',
        }}
      >
        <div
          style={{
            width: '80px',
            height: '80px',
            borderRadius: 'var(--radius-xl)',
            background: `radial-gradient(circle, ${glowColor} 0%, rgba(0,0,0,0.3) 100%)`,
            border: `2px solid ${borderColor}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: verdictColor,
          }}
        >
          <IconComponent size={44} />
        </div>

        <div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Authoritative Outcome
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: verdictColor, letterSpacing: '-0.02em' }}>
            {verdict}
          </div>
          <div style={{ fontSize: '0.92rem', color: 'var(--text-primary)', marginTop: '0.25rem' }}>
            <span style={{ color: 'var(--text-muted)' }}>Primary Reason: </span>
            <code style={{ background: 'var(--bg-input)', padding: '0.15rem 0.4rem', borderRadius: 'var(--radius-sm)', color: 'var(--accent-cyan)' }}>
              {event.primary_reason}
            </code>
          </div>
        </div>
      </div>

      {/* Reason Codes Chips */}
      {event.reason_codes && event.reason_codes.length > 0 && (
        <div style={{ marginBottom: 'var(--space-4)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.4rem', textTransform: 'uppercase' }}>
            Contributing Reason Codes ({event.reason_codes.length}):
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
            {event.reason_codes.map((code) => (
              <span
                key={code}
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.75rem',
                  padding: '0.2rem 0.5rem',
                  background: 'var(--bg-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-subtle)',
                  color: 'var(--text-secondary)',
                }}
              >
                {code}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Provenance Metadata Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: 'var(--space-3)',
          paddingTop: 'var(--space-3)',
          borderTop: '1px solid var(--border-subtle)',
          fontSize: '0.78rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <FileText size={14} style={{ color: 'var(--text-muted)' }} />
          <span style={{ color: 'var(--text-muted)' }}>Event ID:</span>
          <code style={{ color: 'var(--text-primary)' }}>{event.event_id}</code>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <Clock size={14} style={{ color: 'var(--text-muted)' }} />
          <span style={{ color: 'var(--text-muted)' }}>Timestamp:</span>
          <span style={{ color: 'var(--text-primary)' }}>{new Date(event.timestamp).toLocaleString()}</span>
        </div>
        {event.session_id && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <span style={{ color: 'var(--text-muted)' }}>Session:</span>
            <code style={{ color: 'var(--text-primary)' }}>{event.session_id}</code>
          </div>
        )}
        {event.configuration_hash && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <Hash size={14} style={{ color: 'var(--text-muted)' }} />
            <HashDisplay hash={event.configuration_hash} label="Config" truncateLength={6} />
          </div>
        )}
      </div>
    </div>
  );
};
