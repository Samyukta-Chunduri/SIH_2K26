import React from 'react';
import { ArrowRight, Cpu, Layers, Radio, Shield } from 'lucide-react';
import type { DecisionVerdict } from '../../types';
import { StatusBadge } from './StatusBadge';

interface PipelineFlowProps {
  currentVerdict?: DecisionVerdict | null;
}

export const PipelineFlow: React.FC<PipelineFlowProps> = ({ currentVerdict }) => {
  const stages = [
    {
      id: 'quantum',
      label: 'M0–M9 Quantum Layer',
      desc: 'Bell pairs & channel teleportation',
      icon: Radio,
    },
    {
      id: 'stats',
      label: 'M10–M11 Stats & Policy',
      desc: 'Distributions & thresholds',
      icon: Cpu,
    },
    {
      id: 'threats',
      label: 'M13–M15 Threat Detectors',
      desc: 'Identity, Auth, Channel checks',
      icon: Shield,
    },
    {
      id: 'fusion',
      label: 'M16 Evidence Fusion',
      desc: 'Deterministic synthesis',
      icon: Layers,
    },
    {
      id: 'm12',
      label: 'M12 Sole Decision Engine',
      desc: 'Sole authoritative verdict',
      icon: Cpu,
      highlight: true,
    },
  ];

  return (
    <div className="card" style={{ padding: 'var(--space-5)' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-4)' }}>
        <div>
          <h3 style={{ margin: 0, fontSize: '1rem' }}>Authoritative Security Pipeline Flow</h3>
          <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            Strict invariant: M12 remains the sole final decision authority. M19 visualizes and persists.
          </p>
        </div>
        {currentVerdict && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Current Verdict:</span>
            <StatusBadge status={currentVerdict} size="md" />
          </div>
        )}
      </div>

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--space-2)',
          overflowX: 'auto',
          paddingBottom: '0.5rem',
        }}
      >
        {stages.map((stage, idx) => {
          const Icon = stage.icon;
          const isM12 = stage.highlight;

          return (
            <React.Fragment key={stage.id}>
              <div
                style={{
                  flex: '1 0 160px',
                  background: isM12 ? 'rgba(6, 182, 212, 0.08)' : 'var(--bg-input)',
                  border: isM12 ? '1px solid var(--accent-cyan)' : '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: 'var(--space-3)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.3rem',
                  position: 'relative',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <Icon size={16} style={{ color: isM12 ? 'var(--accent-cyan)' : 'var(--text-secondary)' }} />
                  <span style={{ fontSize: '0.8rem', fontWeight: 600, color: isM12 ? 'var(--accent-cyan)' : 'var(--text-primary)' }}>
                    {stage.label}
                  </span>
                </div>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{stage.desc}</span>
                {isM12 && (
                  <span
                    style={{
                      fontSize: '0.62rem',
                      fontWeight: 700,
                      color: '#ffffff',
                      background: 'var(--accent-cyan)',
                      padding: '0.1rem 0.35rem',
                      borderRadius: 'var(--radius-sm)',
                      alignSelf: 'flex-start',
                      marginTop: '0.2rem',
                    }}
                  >
                    FINAL AUTHORITY
                  </span>
                )}
              </div>

              {idx < stages.length - 1 && (
                <ArrowRight size={18} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
