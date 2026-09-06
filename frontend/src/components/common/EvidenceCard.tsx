import React from 'react';
import { UserCheck, Shield, Radio, Layers, AlertCircle } from 'lucide-react';
import type { EvidenceRecord } from '../../types';
import { StatusBadge } from './StatusBadge';

interface EvidenceCardProps {
  record: EvidenceRecord;
}

export const EvidenceCard: React.FC<EvidenceCardProps> = ({ record }) => {
  let IconComponent = Layers;
  let subsystemTitle = 'Subsystem Evidence';
  let subsystemCode = record.source;

  if (record.source === 'IMPERSONATION') {
    IconComponent = UserCheck;
    subsystemTitle = 'M13 Impersonation Detection';
  } else if (record.source === 'AUTHORIZATION') {
    IconComponent = Shield;
    subsystemTitle = 'M14 Authorization Enforcement';
  } else if (record.source === 'QUANTUM_CHANNEL') {
    IconComponent = Radio;
    subsystemTitle = 'M15 Quantum Channel Attack Detection';
  } else if (record.source === 'FUSION') {
    IconComponent = Layers;
    subsystemTitle = 'M16 Deterministic Evidence Fusion';
  }

  const payload = record.evidence_payload || {};

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
      {/* Card Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div
            style={{
              padding: '0.4rem',
              borderRadius: 'var(--radius-md)',
              background: 'var(--accent-cyan-subtle)',
              color: 'var(--accent-cyan)',
              display: 'flex',
            }}
          >
            <IconComponent size={18} />
          </div>
          <div>
            <h4 style={{ margin: 0, fontSize: '0.92rem' }}>{subsystemTitle}</h4>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{subsystemCode}</span>
          </div>
        </div>
        <StatusBadge status={record.status} size="sm" />
      </div>

      {/* Primary Reason */}
      <div style={{ fontSize: '0.82rem' }}>
        <span style={{ color: 'var(--text-muted)' }}>Primary Reason: </span>
        <code style={{ color: 'var(--text-primary)', background: 'var(--bg-input)', padding: '0.1rem 0.35rem', borderRadius: 'var(--radius-sm)' }}>
          {record.primary_reason}
        </code>
      </div>

      {/* Violations */}
      {record.violations && record.violations.length > 0 && (
        <div
          style={{
            background: 'var(--verdict-attack-bg)',
            border: '1px solid var(--verdict-attack-border)',
            borderRadius: 'var(--radius-md)',
            padding: '0.5rem 0.75rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: 'var(--verdict-attack)', fontSize: '0.75rem', fontWeight: 600, marginBottom: '0.25rem' }}>
            <AlertCircle size={13} />
            <span>Violations Detected ({record.violations.length}):</span>
          </div>
          <ul style={{ margin: 0, paddingLeft: '1.2rem', fontSize: '0.78rem', color: 'var(--verdict-attack)' }}>
            {record.violations.map((v, i) => (
              <li key={i}>{v}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Payload Details */}
      <div style={{ background: 'var(--bg-input)', borderRadius: 'var(--radius-md)', padding: '0.5rem 0.75rem', fontSize: '0.78rem' }}>
        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.25rem' }}>
          Payload Metrics & State
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '0.4rem' }}>
          {Object.entries(payload).map(([k, v]) => (
            <div key={k}>
              <span style={{ color: 'var(--text-muted)' }}>{k}: </span>
              <span style={{ color: 'var(--text-primary)', fontFamily: typeof v === 'number' || typeof v === 'boolean' ? 'var(--font-mono)' : 'inherit' }}>
                {typeof v === 'object' ? JSON.stringify(v) : String(v)}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
