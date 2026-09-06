import React, { useEffect, useState } from 'react';
import { History, Play, Filter, Info } from 'lucide-react';
import { api } from '../api/client';
import type { SecurityEventDetail, SecurityEventSummary } from '../types';
import { DecisionCard } from '../components/common/DecisionCard';
import { PipelineFlow } from '../components/common/PipelineFlow';
import { StatusBadge } from '../components/common/StatusBadge';
import { HashDisplay } from '../components/common/HashDisplay';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';
import { EmptyState } from '../components/common/EmptyState';

export const OverviewPage: React.FC = () => {
  const [latestDetail, setLatestDetail] = useState<SecurityEventDetail | null>(null);
  const [events, setEvents] = useState<SecurityEventSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [verdictFilter, setVerdictFilter] = useState<string>('ALL');
  const [executingType, setExecutingType] = useState<string | null>(null);

  async function loadData(showLoading = false) {
    try {
      if (showLoading) setLoading(true);
      setError(null);
      const fetchedEvents = await api.getSecurityEvents({ limit: 20 });
      setEvents(fetchedEvents);

      if (fetchedEvents.length > 0) {
        const detail = await api.getSecurityEvent(fetchedEvents[0].event_id);
        setLatestDetail(detail);
      } else {
        // Run default honest verification to initialize demo state
        const initial = await api.verifyScenario({ scenario_type: 'honest' });
        setLatestDetail(initial);
        const refreshed = await api.getSecurityEvents({ limit: 20 });
        setEvents(refreshed);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load security overview');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const fetchedEvents = await api.getSecurityEvents({ limit: 20 });
        if (!active) return;
        setEvents(fetchedEvents);

        if (fetchedEvents.length > 0) {
          const detail = await api.getSecurityEvent(fetchedEvents[0].event_id);
          if (!active) return;
          setLatestDetail(detail);
        } else {
          const initial = await api.verifyScenario({ scenario_type: 'honest' });
          if (!active) return;
          setLatestDetail(initial);
          const refreshed = await api.getSecurityEvents({ limit: 20 });
          if (!active) return;
          setEvents(refreshed);
        }
      } catch (err: unknown) {
        if (!active) return;
        setError(err instanceof Error ? err.message : 'Failed to load security overview');
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const handleQuickExecute = async (scenarioType: string) => {
    try {
      setExecutingType(scenarioType);
      const res = await api.verifyScenario({ scenario_type: scenarioType });
      setLatestDetail(res);
      const refreshed = await api.getSecurityEvents({ limit: 20 });
      setEvents(refreshed);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Execution failed');
    } finally {
      setExecutingType(null);
    }
  };

  const filteredEvents = events.filter((e) => {
    if (verdictFilter === 'ALL') return true;
    return e.verdict === verdictFilter;
  });

  if (loading && !latestDetail) {
    return <LoadingState message="Loading Q-SHIELD Security Overview..." />;
  }

  if (error && !latestDetail) {
    return <ErrorState message={error} onRetry={loadData} />;
  }

  return (
    <div className="page-container">
      {/* Top Banner */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ margin: 0 }}>Security Overview Dashboard</h1>
          <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.9rem' }}>
            Authoritative quantum-inspired threat detection and verification command center.
          </p>
        </div>

        {/* Quick Scenario Buttons */}
        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
          <button
            className="btn btn-secondary"
            onClick={() => handleQuickExecute('honest')}
            disabled={executingType !== null}
            style={{ fontSize: '0.78rem', borderColor: 'var(--verdict-accept-border)' }}
          >
            <Play size={11} />
            <span>Honest (ACCEPT)</span>
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => handleQuickExecute('channel_anomaly')}
            disabled={executingType !== null}
            style={{ fontSize: '0.78rem', borderColor: 'var(--verdict-suspicious-border)' }}
          >
            <Play size={11} />
            <span>Noise Anomaly (SUSPICIOUS)</span>
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => handleQuickExecute('impersonation_attack')}
            disabled={executingType !== null}
            style={{ fontSize: '0.78rem', borderColor: 'var(--verdict-attack-border)' }}
          >
            <Play size={11} />
            <span>Impersonation Attack (ATTACK)</span>
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => handleQuickExecute('multi_source_attack')}
            disabled={executingType !== null}
            style={{ fontSize: '0.78rem', borderColor: 'var(--verdict-attack-border)' }}
          >
            <Play size={11} />
            <span>Multi-Vector (ATTACK)</span>
          </button>
        </div>
      </div>

      {/* Hero: Current Authoritative Verdict */}
      <DecisionCard
        event={latestDetail?.event || null}
        title="Current System Security State"
        subtitle="Authoritative outcome from M12 Final Decision Engine"
      />

      {/* End-to-End Pipeline Visualization */}
      <PipelineFlow currentVerdict={latestDetail?.event.verdict || null} />

      {/* Historical Activity Table */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <History size={18} style={{ color: 'var(--accent-cyan)' }} />
            <span>Recent Security Verification History (SQLite Persisted)</span>
          </div>

          {/* Verdict Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Filter size={14} style={{ color: 'var(--text-muted)' }} />
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Verdict:</span>
            {['ALL', 'ACCEPT', 'SUSPICIOUS', 'ATTACK'].map((v) => (
              <button
                key={v}
                className="btn"
                onClick={() => setVerdictFilter(v)}
                style={{
                  padding: '0.2rem 0.55rem',
                  fontSize: '0.72rem',
                  backgroundColor: verdictFilter === v ? 'var(--accent-cyan-subtle)' : 'transparent',
                  color: verdictFilter === v ? 'var(--accent-cyan)' : 'var(--text-muted)',
                  border: verdictFilter === v ? '1px solid var(--accent-cyan)' : '1px solid var(--border-subtle)',
                }}
              >
                {v}
              </button>
            ))}
          </div>
        </div>

        {filteredEvents.length === 0 ? (
          <EmptyState message="No matching security verification records in SQLite database." />
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Event ID</th>
                  <th>Verdict (M12)</th>
                  <th>Primary Reason</th>
                  <th>Explicit Violation</th>
                  <th>Config Fingerprint</th>
                  <th>Session</th>
                </tr>
              </thead>
              <tbody>
                {filteredEvents.map((evt) => (
                  <tr key={evt.event_id}>
                    <td style={{ whiteSpace: 'nowrap', fontSize: '0.8rem' }}>
                      {new Date(evt.timestamp).toLocaleString()}
                    </td>
                    <td>
                      <code style={{ color: 'var(--text-secondary)' }}>{evt.event_id}</code>
                    </td>
                    <td>
                      <StatusBadge status={evt.verdict} size="sm" />
                    </td>
                    <td>
                      <code style={{ fontSize: '0.78rem', color: 'var(--accent-cyan)' }}>
                        {evt.primary_reason}
                      </code>
                    </td>
                    <td>
                      <span
                        style={{
                          color: evt.is_explicit_violation ? 'var(--verdict-attack)' : 'var(--text-muted)',
                          fontWeight: evt.is_explicit_violation ? 600 : 400,
                        }}
                      >
                        {evt.is_explicit_violation ? 'YES (ATTACK)' : 'NO'}
                      </span>
                    </td>
                    <td>
                      <HashDisplay hash={evt.configuration_hash} truncateLength={4} />
                    </td>
                    <td>
                      <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                        {evt.session_id || '—'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Scientific Honesty Disclaimer Banner */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          padding: '0.75rem 1rem',
          borderRadius: 'var(--radius-md)',
          background: 'rgba(56, 189, 248, 0.05)',
          border: '1px solid rgba(56, 189, 248, 0.15)',
          fontSize: '0.78rem',
          color: 'var(--text-secondary)',
        }}
      >
        <Info size={16} style={{ color: 'var(--accent-cyan)', flexShrink: 0 }} />
        <span>
          <strong>Scientific Notice:</strong> Telemetry reflects the validated Q-SHIELD quantum simulation engine
          (M0–M18). Q-SHIELD is not connected to physical cryogenic quantum hardware. No synthetic scores or artificial
          confidence percentages are calculated.
        </span>
      </div>
    </div>
  );
};
