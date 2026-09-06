import React, { useEffect, useState } from 'react';
import { Layers, ArrowRight, GitMerge, FileText } from 'lucide-react';
import { api } from '../api/client';
import type { FusionEvidence, SecurityEventDetail, SecurityEventSummary } from '../types';
import { DecisionCard } from '../components/common/DecisionCard';
import { StatusBadge } from '../components/common/StatusBadge';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';

export const FusionPage: React.FC = () => {
  const [events, setEvents] = useState<SecurityEventSummary[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<string>('');
  const [eventDetail, setEventDetail] = useState<SecurityEventDetail | null>(null);
  const [fusionData, setFusionData] = useState<FusionEvidence | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadDetails(id: string) {
    try {
      const [detail, fusion] = await Promise.all([
        api.getSecurityEvent(id),
        api.getFusionEvidence(id),
      ]);
      setEventDetail(detail);
      setFusionData(fusion);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load event details');
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
        await loadDetails(evts[0].event_id);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load fusion evidence');
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
          const [detail, fusion] = await Promise.all([
            api.getSecurityEvent(evts[0].event_id),
            api.getFusionEvidence(evts[0].event_id),
          ]);
          if (!active) return;
          setEventDetail(detail);
          setFusionData(fusion);
        }
      } catch (err: unknown) {
        if (!active) return;
        setError(err instanceof Error ? err.message : 'Failed to load fusion evidence');
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
    loadDetails(id);
  };

  if (loading && !fusionData) {
    return <LoadingState message="Loading Evidence Fusion & Decision Data..." />;
  }

  if (error && !fusionData) {
    return <ErrorState message={error} onRetry={loadEvents} />;
  }

  const sources = fusionData?.source_statuses || {};

  return (
    <div className="page-container">
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--space-4)' }}>
        <div>
          <h1 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Layers size={24} style={{ color: 'var(--accent-cyan)' }} />
            Evidence Fusion & M12 Final Decision
          </h1>
          <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.9rem' }}>
            Multi-source deterministic evidence synthesis funnel leading to the authoritative M12 verdict.
          </p>
        </div>

        {events.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <label htmlFor="fusion-event-select" style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Select Event:
            </label>
            <select
              id="fusion-event-select"
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

      {/* Synthesis Funnel Visual Diagram */}
      <div className="card" style={{ padding: 'var(--space-6)' }}>
        <h3 style={{ margin: '0 0 var(--space-4) 0', fontSize: '1.05rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <GitMerge size={18} style={{ color: 'var(--accent-cyan)' }} />
          Multi-Source Evidence Synthesis Funnel
        </h3>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr auto 1fr auto 1fr',
            gap: 'var(--space-4)',
            alignItems: 'center',
          }}
        >
          {/* Column 1: Contributing Sources */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Subsystem Inputs
            </div>

            {Object.entries(sources).map(([src, st]) => (
              <div
                key={src}
                style={{
                  background: 'var(--bg-input)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: '0.5rem 0.75rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {src.replace('_', ' ')}
                </span>
                <StatusBadge status={st} size="sm" />
              </div>
            ))}
          </div>

          <ArrowRight size={24} style={{ color: 'var(--accent-cyan)' }} />

          {/* Column 2: M16 Evidence Fusion */}
          <div
            style={{
              background: 'rgba(6, 182, 212, 0.08)',
              border: '1px solid var(--accent-cyan)',
              borderRadius: 'var(--radius-lg)',
              padding: 'var(--space-4)',
              textAlign: 'center',
            }}
          >
            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--accent-cyan)', textTransform: 'uppercase' }}>
              M16 Engine
            </div>
            <div style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--text-primary)', margin: '0.2rem 0' }}>
              Deterministic Fusion
            </div>
            <p style={{ margin: '0 0 var(--space-3) 0', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Strict precedence: VIOLATION &gt; CONFLICTING &gt; INCOMPATIBLE &gt; INCOMPLETE &gt; ANOMALOUS &gt; CLEAN
            </p>
            <div style={{ display: 'flex', justifyContent: 'center' }}>
              <StatusBadge
                status={fusionData?.is_explicit_violation ? 'SECURITY_VIOLATION' : fusionData?.is_anomalous ? 'ANOMALOUS' : 'CLEAN'}
                size="md"
              />
            </div>
          </div>

          <ArrowRight size={24} style={{ color: 'var(--accent-cyan)' }} />

          {/* Column 3: M12 Sole Authority */}
          <div
            style={{
              background: 'linear-gradient(135deg, var(--bg-card), var(--bg-secondary))',
              border: '2px solid var(--border-card)',
              borderRadius: 'var(--radius-lg)',
              padding: 'var(--space-4)',
              textAlign: 'center',
            }}
          >
            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Sole Final Authority
            </div>
            <div style={{ fontWeight: 800, fontSize: '1.2rem', color: 'var(--accent-cyan)', margin: '0.2rem 0' }}>
              M12 Decision Engine
            </div>
            <div style={{ marginTop: 'var(--space-2)' }}>
              <StatusBadge status={fusionData?.authoritative_verdict || 'ACCEPT'} size="lg" />
            </div>
          </div>
        </div>
      </div>

      {/* Authoritative Decision Card */}
      <DecisionCard
        event={eventDetail?.event || null}
        title="Authoritative M12 Verdict"
        subtitle="Final security decision resulting from evidence synthesis"
      />

      {/* Decision Explanation & Precedence Card */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <FileText size={18} style={{ color: 'var(--accent-cyan)' }} />
            <span>Decision Explanation & Precedence Rules</span>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-6)' }}>
          <div>
            <h4 style={{ margin: '0 0 var(--space-2) 0', color: 'var(--text-primary)' }}>
              How the Verdict was Reached:
            </h4>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              M12 evaluates synthesized evidence without guessing or calculating synthetic risk scores.
              {fusionData?.is_explicit_violation ? (
                <>
                  {' '}An <strong>explicit security violation</strong> occurred in one or more contributing subsystems.
                  Under the Q-SHIELD security invariant, confirmed violations immediately trigger an authoritative{' '}
                  <strong style={{ color: 'var(--verdict-attack)' }}>ATTACK</strong> verdict.
                </>
              ) : fusionData?.is_anomalous ? (
                <>
                  {' '}A <strong>physical channel anomaly</strong> exceeded the M11 threshold policy, but without confirmed
                  impersonation or credential compromise. Channel disturbances trigger an authoritative{' '}
                  <strong style={{ color: 'var(--verdict-suspicious)' }}>SUSPICIOUS</strong> verdict.
                </>
              ) : (
                <>
                  {' '}All required evidence sources were present, verified, compatible with the active session context,
                  and strictly within established threshold bounds. The system rendered an authoritative{' '}
                  <strong style={{ color: 'var(--verdict-accept)' }}>ACCEPT</strong> verdict.
                </>
              )}
            </p>
          </div>

          <div>
            <h4 style={{ margin: '0 0 var(--space-2) 0', color: 'var(--text-primary)' }}>
              Precedence Hierarchy:
            </h4>
            <ol style={{ margin: 0, paddingLeft: '1.2rem', fontSize: '0.82rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
              <li>
                <strong style={{ color: 'var(--verdict-attack)' }}>SECURITY_VIOLATION</strong> → ATTACK (Confirmed breaches take highest precedence)
              </li>
              <li>
                <strong style={{ color: 'var(--verdict-suspicious)' }}>CONFLICTING_EVIDENCE</strong> → SUSPICIOUS (Contradictory assertions)
              </li>
              <li>
                <strong style={{ color: 'var(--verdict-suspicious)' }}>INCOMPATIBLE_CONTEXT</strong> → SUSPICIOUS (Session / config hash mismatch)
              </li>
              <li>
                <strong style={{ color: 'var(--verdict-suspicious)' }}>INCOMPLETE_EVIDENCE</strong> → SUSPICIOUS (Missing required source)
              </li>
              <li>
                <strong style={{ color: 'var(--verdict-suspicious)' }}>ANOMALOUS</strong> → SUSPICIOUS (Statistical threshold cross)
              </li>
              <li>
                <strong style={{ color: 'var(--verdict-accept)' }}>CLEAN</strong> → ACCEPT (All sources valid and within policy)
              </li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
};
