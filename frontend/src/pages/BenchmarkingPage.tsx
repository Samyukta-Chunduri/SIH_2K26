import React, { useEffect, useState } from 'react';
import { BarChart3, Play, Clock, Activity, Info } from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from 'recharts';
import { api } from '../api/client';
import type { BenchmarkRunDetail, BenchmarkRunSummary } from '../types';
import { MetricCard } from '../components/common/MetricCard';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';
import { EmptyState } from '../components/common/EmptyState';

export const BenchmarkingPage: React.FC = () => {
  const [runs, setRuns] = useState<BenchmarkRunSummary[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string>('');
  const [runDetail, setRunDetail] = useState<BenchmarkRunDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadRunDetail(id: string) {
    try {
      const detail = await api.getBenchmarkRun(id);
      setRunDetail(detail);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load benchmark details');
    }
  }

  async function loadRuns() {
    try {
      setLoading(true);
      setError(null);
      const fetchedRuns = await api.getBenchmarkRuns(20);
      setRuns(fetchedRuns);
      if (fetchedRuns.length > 0) {
        setSelectedRunId(fetchedRuns[0].run_id);
        await loadRunDetail(fetchedRuns[0].run_id);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load benchmark runs');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const fetchedRuns = await api.getBenchmarkRuns(20);
        if (!active) return;
        setRuns(fetchedRuns);
        if (fetchedRuns.length > 0) {
          setSelectedRunId(fetchedRuns[0].run_id);
          const detail = await api.getBenchmarkRun(fetchedRuns[0].run_id);
          if (!active) return;
          setRunDetail(detail);
        }
      } catch (err: unknown) {
        if (!active) return;
        setError(err instanceof Error ? err.message : 'Failed to load benchmark runs');
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
      const newRun = await api.triggerBenchmarkRun(`bench_suite_${Date.now().toString(36)}`);
      setRunDetail(newRun);
      const refreshed = await api.getBenchmarkRuns(20);
      setRuns(refreshed);
      setSelectedRunId(newRun.summary.run_id);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to trigger benchmark suite');
    } finally {
      setRunning(false);
    }
  };

  if (loading && !runDetail) {
    return <LoadingState message="Loading M18 Performance Benchmarks..." />;
  }

  const summary = runDetail?.summary;
  const results = runDetail?.benchmark_results || [];

  // Prepare chart data for latency percentiles across workloads
  const latencyChartData = results.map((r) => ({
    name: `${r.category} (N=${r.workload_size})`,
    mean: Number((r.mean_latency_seconds * 1000).toFixed(3)),
    median: Number((r.median_latency_seconds * 1000).toFixed(3)),
    p95: Number((r.p95_latency_seconds * 1000).toFixed(3)),
    throughput: Number(r.throughput_ops_per_sec.toFixed(1)),
  }));

  const overallMeanLatency =
    results.length > 0
      ? results.reduce((acc, r) => acc + r.mean_latency_seconds, 0) / results.length
      : 0;

  const maxThroughput =
    results.length > 0 ? Math.max(...results.map((r) => r.throughput_ops_per_sec)) : 0;

  return (
    <div className="page-container">
      {/* Header & Controls */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--space-4)' }}>
        <div>
          <h1 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <BarChart3 size={24} style={{ color: 'var(--accent-cyan)' }} />
            M18 Performance Benchmarking Interface
          </h1>
          <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.9rem' }}>
            Deterministic measurement of operational latency, throughput, and workload scaling.
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
                  {r.run_id} — {r.total_benchmarks} benchmarks ({r.total_elapsed_seconds.toFixed(2)}s)
                </option>
              ))}
            </select>
          )}

          <button className="btn btn-primary" onClick={handleTriggerRun} disabled={running}>
            <Play size={13} fill="currentColor" />
            <span>{running ? 'Executing M18 Benchmarks...' : 'Run M18 Benchmark Suite'}</span>
          </button>
        </div>
      </div>

      {error && <ErrorState message={error} onRetry={loadRuns} />}

      {!runDetail ? (
        <EmptyState
          message="No benchmark executions recorded yet. Run the M18 suite to measure operational latency and throughput."
          actionText="Run M18 Benchmark Suite"
          onAction={handleTriggerRun}
        />
      ) : (
        <>
          {/* Metric Summary Cards */}
          <div className="grid-4">
            <MetricCard
              label="Mean Evaluation Latency"
              observed={(overallMeanLatency * 1000).toFixed(3)}
              unit=" ms"
              description="Average time per scenario evaluation"
            />

            <MetricCard
              label="Peak Pipeline Throughput"
              observed={maxThroughput.toFixed(1)}
              unit=" ops/s"
              description="Maximum sustained scenario throughput"
            />

            <MetricCard
              label="Total Benchmark Workloads"
              observed={summary?.total_benchmarks ?? 0}
              description="Workloads tested across scaling bounds"
            />

            <MetricCard
              label="Suite Elapsed Wall Time"
              observed={summary ? summary.total_elapsed_seconds.toFixed(2) : '0'}
              unit=" s"
              description="Total wall-clock runtime for benchmark suite"
            />
          </div>

          {/* Latency Percentiles Chart */}
          <div className="card">
            <div className="card-header">
              <div className="card-title">
                <Clock size={18} style={{ color: 'var(--accent-cyan)' }} />
                <span>Evaluation Latency by Workload (ms)</span>
              </div>
            </div>

            <div style={{ width: '100%', height: '320px', marginTop: 'var(--space-2)' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={latencyChartData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis
                    dataKey="name"
                    stroke="var(--text-muted)"
                    angle={-25}
                    textAnchor="end"
                    interval={0}
                    height={70}
                    fontSize={11}
                  />
                  <YAxis stroke="var(--text-muted)" unit=" ms" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'var(--bg-secondary)',
                      borderColor: 'var(--border-subtle)',
                      borderRadius: 'var(--radius-md)',
                      color: 'var(--text-primary)',
                      fontSize: '0.8rem',
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: '0.8rem', paddingTop: '10px' }} />
                  <Bar dataKey="median" name="Median (P50)" fill="var(--accent-cyan)" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="p95" name="P95 Latency" fill="var(--accent-indigo)" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="mean" name="Mean Latency" fill="var(--verdict-accept)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Benchmark Results Table */}
          <div className="card">
            <div className="card-header">
              <div className="card-title">
                <Activity size={18} style={{ color: 'var(--accent-cyan)' }} />
                <span>Benchmark Execution Metrics ({results.length} Categories)</span>
              </div>
            </div>

            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Benchmark ID</th>
                    <th>Category</th>
                    <th>Workload (N)</th>
                    <th>Mean Latency</th>
                    <th>P50 Median</th>
                    <th>P95 Latency</th>
                    <th>Throughput</th>
                    <th>CPU Time</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((b) => (
                    <tr key={b.benchmark_id}>
                      <td>
                        <code style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{b.benchmark_id}</code>
                      </td>
                      <td style={{ fontSize: '0.8rem' }}>{b.category}</td>
                      <td style={{ fontFamily: 'var(--font-mono)' }}>{b.workload_size}</td>
                      <td style={{ fontFamily: 'var(--font-mono)' }}>{(b.mean_latency_seconds * 1000).toFixed(3)} ms</td>
                      <td style={{ fontFamily: 'var(--font-mono)' }}>{(b.median_latency_seconds * 1000).toFixed(3)} ms</td>
                      <td style={{ fontFamily: 'var(--font-mono)' }}>{(b.p95_latency_seconds * 1000).toFixed(3)} ms</td>
                      <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>
                        {b.throughput_ops_per_sec.toFixed(1)} ops/s
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                        {b.cpu_time_seconds.toFixed(3)} s
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
              <strong>Benchmark Disclaimer:</strong> Performance is benchmarked on the local simulation runtime.
              Results do not reflect cryogenic physical quantum network latency or production-scale enterprise throughput.
            </span>
          </div>
        </>
      )}
    </div>
  );
};
