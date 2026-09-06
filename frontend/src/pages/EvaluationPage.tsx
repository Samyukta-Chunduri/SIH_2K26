import React, { useEffect, useState } from 'react';
import { FileCheck2, Play, CheckCircle2, XCircle, Grid, Info } from 'lucide-react';
import { api } from '../api/client';
import type { EvaluationRunDetail, EvaluationRunSummary } from '../types';
import { MetricCard } from '../components/common/MetricCard';
import { StatusBadge } from '../components/common/StatusBadge';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';
import { EmptyState } from '../components/common/EmptyState';

export const EvaluationPage: React.FC = () => {
  const [runs, setRuns] = useState<EvaluationRunSummary[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string>('');
  const [runDetail, setRunDetail] = useState<EvaluationRunDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadRunDetail(id: string) {
    try {
      const detail = await api.getEvaluationRun(id);
      setRunDetail(detail);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load evaluation details');
    }
  }

  async function loadRuns() {
    try {
      setLoading(true);
      setError(null);
      const fetchedRuns = await api.getEvaluationRuns(20);
      setRuns(fetchedRuns);
      if (fetchedRuns.length > 0) {
        setSelectedRunId(fetchedRuns[0].run_id);
        await loadRunDetail(fetchedRuns[0].run_id);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load evaluation runs');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const fetchedRuns = await api.getEvaluationRuns(20);
        if (!active) return;
        setRuns(fetchedRuns);
        if (fetchedRuns.length > 0) {
          setSelectedRunId(fetchedRuns[0].run_id);
          const detail = await api.getEvaluationRun(fetchedRuns[0].run_id);
          if (!active) return;
          setRunDetail(detail);
        }
      } catch (err: unknown) {
        if (!active) return;
        setError(err instanceof Error ? err.message : 'Failed to load evaluation runs');
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const handleRunChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const id = e.target.value;
    setSelectedRunId(id);
    loadRunDetail(id);
  };

  const handleTriggerRun = async () => {
    try {
      setRunning(true);
      const newRun = await api.triggerEvaluationRun(`eval_session_${Date.now().toString(36)}`);
      setRunDetail(newRun);
      const refreshed = await api.getEvaluationRuns(20);
      setRuns(refreshed);
      setSelectedRunId(newRun.summary.run_id);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to trigger evaluation run');
    } finally {
      setRunning(false);
    }
  };

  if (loading && !runDetail) {
    return <LoadingState message="Loading M17 Security Evaluation Report..." />;
  }

  const summary = runDetail?.summary;
  const cm = runDetail?.confusion_matrix;
  const scenarios = runDetail?.scenario_results || [];

  return (
    <div className="page-container">
      {/* Header & Controls */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--space-4)' }}>
        <div>
          <h1 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FileCheck2 size={24} style={{ color: 'var(--accent-cyan)' }} />
            M17 Security Evaluation Interface
          </h1>
          <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.9rem' }}>
            Deterministic evaluation of the Q-SHIELD detection pipeline across controlled security scenarios.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {runs.length > 0 && (
            <select
              className="select"
              value={selectedRunId}
              onChange={handleRunChange}
              style={{ width: '260px', fontSize: '0.8rem' }}
            >
              {runs.map((r) => (
                <option key={r.run_id} value={r.run_id}>
                  {r.run_id} — {r.passed_scenarios}/{r.total_scenarios} Passed ({((r.pass_rate || 0) * 100).toFixed(0)}%)
                </option>
              ))}
            </select>
          )}

          <button className="btn btn-primary" onClick={handleTriggerRun} disabled={running}>
            <Play size={13} fill="currentColor" />
            <span>{running ? 'Executing M17 Suite...' : 'Run M17 Evaluation Suite'}</span>
          </button>
        </div>
      </div>

      {error && <ErrorState message={error} onRetry={loadRuns} />}

      {!runDetail ? (
        <EmptyState
          message="No evaluation suite executions recorded yet. Run the M17 suite to evaluate pipeline accuracy."
          actionText="Run M17 Evaluation Suite"
          onAction={handleTriggerRun}
        />
      ) : (
        <>
          {/* Summary Metric Cards */}
          <div className="grid-4">
            <MetricCard
              label="Evaluation Pass Rate"
              observed={summary ? (summary.pass_rate * 100).toFixed(1) : null}
              unit="%"
              expected="100%"
              isAnomalous={summary ? summary.pass_rate < 1.0 : false}
              description="Fraction of scenarios matching expected M12 verdict"
            />

            <MetricCard
              label="Total Scenarios Evaluated"
              observed={summary?.total_scenarios ?? null}
              expected="16 Scenarios"
              description="Covers honest, noise, impersonation, auth, & channel breaches"
            />

            <MetricCard
              label="Pipeline Sensitivity (Recall)"
              observed={cm?.sensitivity !== null && cm?.sensitivity !== undefined ? (cm.sensitivity * 100).toFixed(1) : null}
              unit="%"
              expected="100%"
              description="True Positive Rate: TP / (TP + FN)"
            />

            <MetricCard
              label="Pipeline Specificity"
              observed={cm?.specificity !== null && cm?.specificity !== undefined ? (cm.specificity * 100).toFixed(1) : null}
              unit="%"
              expected="100%"
              description="True Negative Rate: TN / (TN + FP)"
            />
          </div>

          {/* Confusion Matrix Card */}
          {cm && (
            <div className="card">
              <div className="card-header">
                <div className="card-title">
                  <Grid size={18} style={{ color: 'var(--accent-cyan)' }} />
                  <span>Categorical Security Confusion Matrix</span>
                </div>
              </div>

              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(4, 1fr)',
                  gap: 'var(--space-4)',
                  textAlign: 'center',
                }}
              >
                <div style={{ background: 'var(--verdict-accept-bg)', border: '1px solid var(--verdict-accept-border)', borderRadius: 'var(--radius-md)', padding: 'var(--space-3)' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>True Positives (TP)</div>
                  <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--verdict-accept)' }}>{cm.true_positives}</div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Attacks correctly identified</div>
                </div>

                <div style={{ background: 'var(--verdict-accept-bg)', border: '1px solid var(--verdict-accept-border)', borderRadius: 'var(--radius-md)', padding: 'var(--space-3)' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>True Negatives (TN)</div>
                  <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--verdict-accept)' }}>{cm.true_negatives}</div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Honest states accepted</div>
                </div>

                <div style={{ background: cm.false_positives > 0 ? 'var(--verdict-attack-bg)' : 'var(--bg-input)', border: `1px solid ${cm.false_positives > 0 ? 'var(--verdict-attack-border)' : 'var(--border-subtle)'}`, borderRadius: 'var(--radius-md)', padding: 'var(--space-3)' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>False Positives (FP)</div>
                  <div style={{ fontSize: '1.75rem', fontWeight: 800, color: cm.false_positives > 0 ? 'var(--verdict-attack)' : 'var(--text-muted)' }}>{cm.false_positives}</div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Honest states rejected</div>
                </div>

                <div style={{ background: cm.false_negatives > 0 ? 'var(--verdict-attack-bg)' : 'var(--bg-input)', border: `1px solid ${cm.false_negatives > 0 ? 'var(--verdict-attack-border)' : 'var(--border-subtle)'}`, borderRadius: 'var(--radius-md)', padding: 'var(--space-3)' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>False Negatives (FN)</div>
                  <div style={{ fontSize: '1.75rem', fontWeight: 800, color: cm.false_negatives > 0 ? 'var(--verdict-attack)' : 'var(--text-muted)' }}>{cm.false_negatives}</div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Attacks accepted as honest</div>
                </div>
              </div>
            </div>
          )}

          {/* Scenario Results Table */}
          <div className="card">
            <div className="card-header">
              <div className="card-title">
                <FileCheck2 size={18} style={{ color: 'var(--accent-cyan)' }} />
                <span>Scenario Audit Results ({scenarios.length} Test Cases)</span>
              </div>
            </div>

            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Scenario ID</th>
                    <th>Category</th>
                    <th>Expected Verdict</th>
                    <th>Observed (M12)</th>
                    <th>Result</th>
                    <th>Mismatch Diagnostic</th>
                  </tr>
                </thead>
                <tbody>
                  {scenarios.map((sc) => (
                    <tr key={sc.scenario_id}>
                      <td>
                        <code style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{sc.scenario_id}</code>
                      </td>
                      <td style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                        {sc.category}
                      </td>
                      <td>
                        <StatusBadge status={sc.expected_verdict} size="sm" />
                      </td>
                      <td>
                        <StatusBadge status={sc.observed_verdict} size="sm" />
                      </td>
                      <td>
                        <span
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.25rem',
                            fontWeight: 700,
                            color: sc.passed ? 'var(--verdict-accept)' : 'var(--verdict-attack)',
                          }}
                        >
                          {sc.passed ? <CheckCircle2 size={14} /> : <XCircle size={14} />}
                          <span>{sc.passed ? 'PASS' : 'FAIL'}</span>
                        </span>
                      </td>
                      <td style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                        {sc.mismatch_reason || '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
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
              <strong>Evaluation Methodology:</strong> Evaluates reproducibility and precision of detection algorithms
              under deterministic synthetic attack fixtures. Not a statistical probability guarantee.
            </span>
          </div>
        </>
      )}
    </div>
  );
};
