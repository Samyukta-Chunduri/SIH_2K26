/**
 * Q-SHIELD — Frontend Type Definitions (Milestone M19-C).
 *
 * Mappings mirroring the authoritative FastAPI schemas.
 * Invariant: The frontend only visualizes; it never computes verdicts.
 */

export type DecisionVerdict = 'ACCEPT' | 'SUSPICIOUS' | 'ATTACK';

export interface ScenarioTemplate {
  scenario_type: string;
  name: string;
  description: string;
  expected_verdict: DecisionVerdict;
  category: string;
}

export interface VerifyScenarioRequest {
  scenario_type: string;
  session_id?: string;
  metadata?: Record<string, unknown>;
}

export interface SecurityEventSummary {
  event_id: string;
  timestamp: string;
  verdict: DecisionVerdict;
  primary_reason: string;
  reason_codes: string[];
  session_id?: string | null;
  scenario_id?: string | null;
  configuration_hash?: string | null;
  exceeded_count: number;
  is_explicit_violation: boolean;
  is_evidence_complete: boolean;
  created_at: string;
}

export interface EvidenceRecord {
  record_id: string;
  event_id: string;
  source: 'IMPERSONATION' | 'AUTHORIZATION' | 'QUANTUM_CHANNEL' | 'FUSION';
  status: string;
  primary_reason: string;
  evidence_payload: Record<string, unknown>;
  violations: string[];
  created_at: string;
}

export interface SecurityEventDetail {
  event: SecurityEventSummary;
  evidence_records: EvidenceRecord[];
}

export interface QuantumEvidence {
  event_id: string;
  status: string;
  qber: number | null;
  teleportation_fidelity: number | null;
  bell_correlations: Record<string, number>;
  measurement_distribution?: Record<string, number>;
  threshold_exceeded?: boolean;
  is_anomalous?: boolean;
  details?: Record<string, unknown>;
  baseline_expected?: Record<string, number>;
  threshold_policy?: Record<string, number>;
}

export interface ThreatEvidence {
  event_id: string;
  timestamp?: string;
  impersonation: Record<string, unknown>;
  authorization: Record<string, unknown>;
  quantum_channel: Record<string, unknown>;
  confirmed_violations: string[];
}

export interface FusionEvidence {
  event_id: string;
  fused_status: string;
  primary_reason: string;
  source_statuses: Record<string, string>;
  present_sources: string[];
  missing_sources?: string[];
  violations?: string[];
  m12_verdict?: DecisionVerdict;
  m12_primary_reason?: string;
  authoritative_verdict?: DecisionVerdict;
  is_clean?: boolean;
  is_anomalous?: boolean;
  is_explicit_violation?: boolean;
}

export interface EvaluationScenarioResult {
  id?: number;
  scenario_id: string;
  category: string;
  expected_verdict: DecisionVerdict;
  observed_verdict: DecisionVerdict;
  passed: boolean;
  mismatch_reason?: string | null;
  violations: string[];
}

export interface ConfusionMatrix {
  true_positives: number;
  true_negatives: number;
  false_positives: number;
  false_negatives: number;
  sensitivity: number | null;
  specificity: number | null;
}

export interface CategorySummary {
  passed: number;
  total: number;
  pass_rate: number;
}

export interface EvaluationRunSummary {
  run_id: string;
  timestamp: string;
  session_id?: string | null;
  total_scenarios: number;
  passed_scenarios: number;
  failed_scenarios: number;
  pass_rate: number;
  created_at: string;
}

export interface EvaluationRunDetail {
  summary: EvaluationRunSummary;
  confusion_matrix: ConfusionMatrix;
  category_summaries: Record<string, CategorySummary>;
  scenario_results: EvaluationScenarioResult[];
}

export interface BenchmarkResult {
  benchmark_id: string;
  category: string;
  workload_size: number;
  iterations: number;
  total_elapsed_seconds: number;
  cpu_time_seconds: number;
  mean_latency_seconds: number;
  min_latency_seconds: number;
  max_latency_seconds: number;
  median_latency_seconds: number;
  p95_latency_seconds: number;
  throughput_ops_per_sec: number;
  observed_verdicts: Record<string, number>;
  errors: string[];
}

export interface BenchmarkRunSummary {
  run_id: string;
  suite_id: string;
  timestamp: string;
  total_benchmarks: number;
  successful_benchmarks: number;
  failed_benchmarks: number;
  total_elapsed_seconds: number;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface BenchmarkRunDetail {
  summary: BenchmarkRunSummary;
  benchmark_results: BenchmarkResult[];
}

export interface HealthStatus {
  status: string;
  service: string;
  version: string;
}
