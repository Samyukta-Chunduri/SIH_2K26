import React, { useEffect, useState } from 'react';
import { Radio, Activity, Info } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, CartesianGrid } from 'recharts';
import { api } from '../api/client';
import type { QuantumEvidence, SecurityEventSummary } from '../types';
import { MetricCard } from '../components/common/MetricCard';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';
import { StatusBadge } from '../components/common/StatusBadge';

export const QuantumPage: React.FC = () => {
  const [events, setEvents] = useState<SecurityEventSummary[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<string>('');
  const [evidence, setEvidence] = useState<QuantumEvidence | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadEvidence(id: string) {
    try {
      const qEv = await api.getQuantumEvidence(id);
      setEvidence(qEv);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load quantum telemetry');
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
        await loadEvidence(evts[0].event_id);
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
          const qEv = await api.getQuantumEvidence(evts[0].event_id);
          if (!active) return;
          setEvidence(qEv);
        }
      } catch (err: unknown) {
        if (!active) return;
        setError(err instanceof Error ? err.message : 'Failed to load quantum telemetry');
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
    loadEvidence(id);
  };

  if (loading && !evidence) {
    return <LoadingState message="Loading Quantum Subsystem Evidence..." />;
  }

  if (error && !evidence) {
    return <ErrorState message={error} onRetry={loadEvents} />;
  }

  // Chart data preparing: observed vs baseline vs threshold
  const chartData = [
    {
      metric: 'QBER',
      observed: evidence?.qber !== null && evidence?.qber !== undefined ? Number(evidence.qber.toFixed(4)) : null,
      baseline: evidence?.baseline_expected?.['qber'] ?? 0.015,
      threshold: evidence?.threshold_policy?.['qber_max'] ?? 0.06,
    },
    {
      metric: 'Fidelity',
      observed: evidence?.teleportation_fidelity !== null && evidence?.teleportation_fidelity !== undefined
        ? Number(evidence.teleportation_fidelity.toFixed(4))
        : null,
      baseline: evidence?.baseline_expected?.['fidelity'] ?? 0.985,
      threshold: evidence?.threshold_policy?.['fidelity_min'] ?? 0.85,
    },
  ];

  // Bell Correlations
  const bellData = evidence?.bell_correlations
    ? Object.entries(evidence.bell_correlations).map(([axis, val]) => ({
        axis,
        observed: Number(val.toFixed(3)),
        expected: axis === 'E_YY' ? -1.0 : 1.0,
      }))
    : [];

  return (
    <div className="page-container">
      {/* Header with Event Selector */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--space-4)' }}>
        <div>
          <h1 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Radio size={24} style={{ color: 'var(--accent-cyan)' }} />
            Quantum Monitoring & Evidence UI
          </h1>
          <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.9rem' }}>
            Physical channel imperfections, QBER, Bell correlations, and teleportation fidelity inspection.
          </p>
        </div>

        {events.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <label htmlFor="evt-select" style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Select Event:
            </label>
            <select
              id="evt-select"
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

      {/* Metric Cards Grid */}
      <div className="grid-4">
        <MetricCard
          label="Quantum Bit Error Rate (QBER)"
          observed={evidence?.qber !== null && evidence?.qber !== undefined ? (evidence.qber * 100).toFixed(2) : null}
          unit="%"
          expected="1.5%"
          threshold="≤ 6.0%"
          isAnomalous={evidence?.is_anomalous}
          description="Fraction of mismatched transmission key bits across channel"
        />

        <MetricCard
          label="Teleportation State Fidelity"
          observed={evidence?.teleportation_fidelity !== null && evidence?.teleportation_fidelity !== undefined ? (evidence.teleportation_fidelity * 100).toFixed(2) : null}
          unit="%"
          expected="98.5%"
          threshold="≥ 85.0%"
          isAnomalous={evidence?.is_anomalous}
          description="Quantum state reconstruction overlap F = ⟨ψ|ρ|ψ⟩"
        />

        <MetricCard
          label="Bell Correlation E_ZZ"
          observed={evidence?.bell_correlations?.['E_ZZ'] !== undefined ? evidence.bell_correlations['E_ZZ'].toFixed(3) : null}
          expected="+1.000"
          threshold="≥ 0.707"
          isAnomalous={evidence?.is_anomalous}
          description="Projective spin measurement parity along Z-basis"
        />

        <MetricCard
          label="Channel Status"
          observed={evidence?.is_anomalous ? 'ANOMALY DETECTED' : 'NORMAL (WITHIN POLICY)'}
          expected="Clean / Benign"
          threshold="M11 Thresholds"
          isAnomalous={evidence?.is_anomalous}
          description="Evaluated by M15 against M11 statistical threshold policy"
        />
      </div>

      {/* Comparison Chart: Observed vs Baseline vs Threshold */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <Activity size={18} style={{ color: 'var(--accent-cyan)' }} />
            <span>Quantum Channel Metrics vs. Baseline & Threshold Policy</span>
          </div>
          {evidence && (
            <StatusBadge
              status={evidence.is_anomalous ? 'ANOMALOUS' : 'VALID'}
              size="sm"
            />
          )}
        </div>

        <div style={{ width: '100%', height: '300px', marginTop: 'var(--space-2)' }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="metric" stroke="var(--text-muted)" />
              <YAxis stroke="var(--text-muted)" domain={[0, 1.1]} />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'var(--bg-secondary)',
                  borderColor: 'var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  color: 'var(--text-primary)',
                  fontSize: '0.8rem',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '0.8rem' }} />
              <Bar dataKey="observed" name="Observed Value" fill="var(--accent-cyan)" radius={[4, 4, 0, 0]} />
              <Bar dataKey="baseline" name="Honest Baseline" fill="var(--verdict-accept)" radius={[4, 4, 0, 0]} />
              <Bar dataKey="threshold" name="Policy Threshold" fill="var(--verdict-suspicious)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Bell Correlations Table */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <Radio size={18} style={{ color: 'var(--accent-cyan)' }} />
            <span>Bell Correlation Tensor Components</span>
          </div>
        </div>

        {bellData.length === 0 ? (
          <p style={{ color: 'var(--text-muted)' }}>No Bell correlation data recorded for this event.</p>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Axis / Operator</th>
                  <th>Observed Correlation</th>
                  <th>Ideal Singlet Target</th>
                  <th>Absolute Deviation</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {bellData.map((b) => {
                  const dev = Math.abs(b.observed - b.expected);
                  const isOk = dev < 0.35;
                  return (
                    <tr key={b.axis}>
                      <td>
                        <code style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>{b.axis}</code>
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)' }}>{b.observed}</td>
                      <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>{b.expected}</td>
                      <td style={{ fontFamily: 'var(--font-mono)' }}>{dev.toFixed(3)}</td>
                      <td>
                        <StatusBadge status={isOk ? 'VALID' : 'ANOMALOUS'} size="sm" />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Scientific Notice */}
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
          <strong>Quantum Simulation Scope:</strong> Metrics derived from the validated Qiskit statevector & density matrix simulation (M0–M7).
          No physical qubit hardware or real-time cryostat telemetry is fabricated.
        </span>
      </div>
    </div>
  );
};
