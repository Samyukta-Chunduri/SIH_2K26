import React, { useEffect, useState } from 'react';
import { ShieldAlert, UserCheck, Shield, Radio, AlertCircle, CheckCircle2 } from 'lucide-react';
import { api } from '../api/client';
import type { SecurityEventSummary, ThreatEvidence } from '../types';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';
import { StatusBadge } from '../components/common/StatusBadge';

export const ThreatsPage: React.FC = () => {
  const [events, setEvents] = useState<SecurityEventSummary[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<string>('');
  const [threatData, setThreatData] = useState<ThreatEvidence | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadThreatEvidence(id: string) {
    try {
      const th = await api.getThreatEvidence(id);
      setThreatData(th);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load threat evidence');
    }
  }

  async function loadEvents() {
    try {
      setLoading(true);
      setError(null);
      const evts = await api.getSecurityEvents({ limit: 15 });
      setEvents(evts);
      if (evts.length > 0) {
        setSelectedEventId(evts[0].event_id);
        await loadThreatEvidence(evts[0].event_id);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load events');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const evts = await api.getSecurityEvents({ limit: 15 });
        if (!active) return;
        setEvents(evts);
        if (evts.length > 0) {
          setSelectedEventId(evts[0].event_id);
          const th = await api.getThreatEvidence(evts[0].event_id);
          if (!active) return;
          setThreatData(th);
        }
      } catch (err: unknown) {
        if (!active) return;
        setError(err instanceof Error ? err.message : 'Failed to load threat evidence');
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const handleEventChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const id = e.target.value;
    setSelectedEventId(id);
    loadThreatEvidence(id);
  };

  if (loading && !threatData) {
    return <LoadingState message="Loading Threat Subsystems Evidence..." />;
  }

  if (error && !threatData) {
    return <ErrorState message={error} onRetry={loadEvents} />;
  }

  const imp = threatData?.impersonation || {};
  const auth = threatData?.authorization || {};
  const ch = threatData?.quantum_channel || {};
  const violations = threatData?.confirmed_violations || [];

  return (
    <div className="page-container">
      {/* Header with Event Selector */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--space-4)' }}>
        <div>
          <h1 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <ShieldAlert size={24} style={{ color: 'var(--accent-cyan)' }} />
            Threat Detection Subsystems Inspector
          </h1>
          <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.9rem' }}>
            Tri-modular threat inspection: M13 Impersonation, M14 Authorization, and M15 Channel Disturbance.
          </p>
        </div>

        {events.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <label htmlFor="threat-event-select" style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Select Event:
            </label>
            <select
              id="threat-event-select"
              className="select"
              value={selectedEventId}
              onChange={handleEventChange}
              style={{ width: '260px', fontSize: '0.8rem' }}
            >
              {events.map((evt) => (
                <option key={evt.event_id} value={evt.event_id}>
                  {evt.event_id} — {evt.verdict} ({evt.primary_reason})
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Confirmed Violations Alert Banner */}
      {violations.length > 0 ? (
        <div
          style={{
            background: 'var(--verdict-attack-bg)',
            border: '1px solid var(--verdict-attack-border)',
            borderRadius: 'var(--radius-md)',
            padding: 'var(--space-4)',
            display: 'flex',
            alignItems: 'flex-start',
            gap: 'var(--space-3)',
          }}
        >
          <AlertCircle size={22} style={{ color: 'var(--verdict-attack)', flexShrink: 0, marginTop: '2px' }} />
          <div>
            <div style={{ color: 'var(--verdict-attack)', fontWeight: 700, fontSize: '0.95rem' }}>
              Security Threat Detected ({violations.length} Confirmed Violations)
            </div>
            <p style={{ margin: '0.25rem 0 0.5rem 0', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              The following explicit security violations were identified by subsystem detectors and forwarded to M16 Fusion:
            </p>
            <ul style={{ margin: 0, paddingLeft: '1.2rem', color: 'var(--verdict-attack)', fontSize: '0.82rem' }}>
              {violations.map((v, i) => (
                <li key={i}>{v}</li>
              ))}
            </ul>
          </div>
        </div>
      ) : (
        <div
          style={{
            background: 'var(--verdict-accept-bg)',
            border: '1px solid var(--verdict-accept-border)',
            borderRadius: 'var(--radius-md)',
            padding: 'var(--space-3) var(--space-4)',
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-3)',
          }}
        >
          <CheckCircle2 size={18} style={{ color: 'var(--verdict-accept)' }} />
          <span style={{ color: 'var(--verdict-accept)', fontSize: '0.85rem', fontWeight: 600 }}>
            All threat subsystems report clean or benign operating conditions. Zero explicit violations.
          </span>
        </div>
      )}

      {/* 3 Subsystem Cards Grid */}
      <div className="grid-3">
        {/* Subsystem 1: M13 Impersonation */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <UserCheck size={18} style={{ color: 'var(--accent-cyan)' }} />
              <span>M13 Impersonation</span>
            </div>
            <StatusBadge status={(imp['status'] as string) || 'CLEAN'} size="sm" />
          </div>

          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', margin: '0 0 var(--space-3) 0' }}>
            Validates cryptographic identity bindings, certificate chains, and authenticators.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.82rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.3rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>Claimed Identity:</span>
              <code style={{ color: 'var(--text-primary)' }}>{String(imp['claimed_identity'] || '—')}</code>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.3rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>Authenticated Identity:</span>
              <code style={{ color: 'var(--text-primary)' }}>{String(imp['authenticated_identity'] || '—')}</code>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.3rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>Impersonation Detected:</span>
              <span style={{ fontWeight: 600, color: imp['is_impersonation_detected'] ? 'var(--verdict-attack)' : 'var(--verdict-accept)' }}>
                {imp['is_impersonation_detected'] ? 'YES' : 'NO'}
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.3rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>Indeterminate State:</span>
              <span>{imp['is_indeterminate'] ? 'YES (Incomplete Auth)' : 'NO'}</span>
            </div>
          </div>
        </div>

        {/* Subsystem 2: M14 Authorization */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <Shield size={18} style={{ color: 'var(--accent-indigo)' }} />
              <span>M14 Authorization</span>
            </div>
            <StatusBadge status={(auth['status'] as string) || 'CLEAN'} size="sm" />
          </div>

          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', margin: '0 0 var(--space-3) 0' }}>
            Enforces role-based permissions and verification capabilities on digital signatures.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.82rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.3rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>Participant Identity:</span>
              <code style={{ color: 'var(--text-primary)' }}>{String(auth['participant_identity'] || '—')}</code>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.3rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>Assigned Role:</span>
              <code style={{ color: 'var(--text-primary)' }}>{String(auth['role'] || 'VERIFIER')}</code>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.3rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>Requested Operation:</span>
              <code style={{ color: 'var(--text-primary)' }}>{String(auth['operation'] || 'VERIFY')}</code>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.3rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>Authorized:</span>
              <span style={{ fontWeight: 600, color: auth['is_authorized'] ? 'var(--verdict-accept)' : 'var(--verdict-attack)' }}>
                {auth['is_authorized'] ? 'YES' : 'NO'}
              </span>
            </div>
          </div>
        </div>

        {/* Subsystem 3: M15 Quantum Channel */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <Radio size={18} style={{ color: 'var(--accent-cyan)' }} />
              <span>M15 Channel Disturbance</span>
            </div>
            <StatusBadge status={(ch['status'] as string) || 'CLEAN'} size="sm" />
          </div>

          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', margin: '0 0 var(--space-3) 0' }}>
            Detects eavesdropping, interception, or fiber attenuation via statistical threshold policy.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.82rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.3rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>Observed QBER:</span>
              <code style={{ color: 'var(--text-primary)' }}>
                {typeof ch['qber'] === 'number' ? `${(ch['qber'] * 100).toFixed(2)}%` : '—'}
              </code>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.3rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>State Fidelity:</span>
              <code style={{ color: 'var(--text-primary)' }}>
                {typeof ch['teleportation_fidelity'] === 'number'
                  ? `${(ch['teleportation_fidelity'] * 100).toFixed(2)}%`
                  : '—'}
              </code>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.3rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>Threshold Anomaly:</span>
              <span style={{ fontWeight: 600, color: ch['is_anomalous'] ? 'var(--verdict-suspicious)' : 'var(--verdict-accept)' }}>
                {ch['is_anomalous'] ? 'YES (Exceeded)' : 'NO'}
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.3rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>Explicit Breach:</span>
              <span style={{ fontWeight: 600, color: ch['is_explicit_violation'] ? 'var(--verdict-attack)' : 'var(--verdict-accept)' }}>
                {ch['is_explicit_violation'] ? 'YES' : 'NO'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
