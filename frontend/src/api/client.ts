/**
 * Q-SHIELD — Frontend API Client Module (Milestone M19-C).
 *
 * Provides typed, clean asynchronous interaction with the FastAPI backend.
 * Handles HTTP error status codes and JSON deserialization defensively.
 */

import type {
  BenchmarkRunDetail,
  BenchmarkRunSummary,
  EvaluationRunDetail,
  EvaluationRunSummary,
  FusionEvidence,
  HealthStatus,
  QuantumEvidence,
  ScenarioTemplate,
  SecurityEventDetail,
  SecurityEventSummary,
  ThreatEvidence,
  VerifyScenarioRequest,
} from '../types';

const API_BASE = '';

async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    let errorDetail = `HTTP ${response.status} ${response.statusText}`;
    try {
      const errJson = await response.json();
      if (errJson?.detail) {
        errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // Ignore fallback on raw status text
    }
    throw new Error(errorDetail);
  }

  return response.json() as Promise<T>;
}

export const api = {
  // Health
  checkHealth: (): Promise<HealthStatus> => fetchJson<HealthStatus>('/health'),

  // Scenarios & Verification
  getScenarioTemplates: (): Promise<ScenarioTemplate[]> =>
    fetchJson<ScenarioTemplate[]>('/api/scenarios'),

  verifyScenario: (request: VerifyScenarioRequest): Promise<SecurityEventDetail> =>
    fetchJson<SecurityEventDetail>('/api/security/verify', {
      method: 'POST',
      body: JSON.stringify(request),
    }),

  // Events & History
  getSecurityEvents: (params?: {
    limit?: number;
    offset?: number;
    verdict?: string;
    session_id?: string;
  }): Promise<SecurityEventSummary[]> => {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    if (params?.offset) searchParams.set('offset', params.offset.toString());
    if (params?.verdict) searchParams.set('verdict', params.verdict);
    if (params?.session_id) searchParams.set('session_id', params.session_id);
    const query = searchParams.toString();
    return fetchJson<SecurityEventSummary[]>(`/api/security/events${query ? `?${query}` : ''}`);
  },

  getSecurityEvent: (eventId: string): Promise<SecurityEventDetail> =>
    fetchJson<SecurityEventDetail>(`/api/security/events/${encodeURIComponent(eventId)}`),

  // Subsystem Evidence
  getQuantumEvidence: (eventId: string): Promise<QuantumEvidence> =>
    fetchJson<QuantumEvidence>(`/api/quantum/evidence/${encodeURIComponent(eventId)}`),

  getThreatEvidence: (eventId: string): Promise<ThreatEvidence> =>
    fetchJson<ThreatEvidence>(`/api/threats/${encodeURIComponent(eventId)}`),

  getFusionEvidence: (eventId: string): Promise<FusionEvidence> =>
    fetchJson<FusionEvidence>(`/api/fusion/${encodeURIComponent(eventId)}`),

  // Evaluation (M17)
  getEvaluationRuns: (limit = 20, offset = 0): Promise<EvaluationRunSummary[]> =>
    fetchJson<EvaluationRunSummary[]>(`/api/evaluation/runs?limit=${limit}&offset=${offset}`),

  getEvaluationRun: (runId: string): Promise<EvaluationRunDetail> =>
    fetchJson<EvaluationRunDetail>(`/api/evaluation/runs/${encodeURIComponent(runId)}`),

  triggerEvaluationRun: (sessionId?: string): Promise<EvaluationRunDetail> => {
    const query = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : '';
    return fetchJson<EvaluationRunDetail>(`/api/evaluation/run${query}`, { method: 'POST' });
  },

  // Benchmarking (M18)
  getBenchmarkRuns: (limit = 20, offset = 0): Promise<BenchmarkRunSummary[]> =>
    fetchJson<BenchmarkRunSummary[]>(`/api/benchmarks?limit=${limit}&offset=${offset}`),

  getBenchmarkRun: (runId: string): Promise<BenchmarkRunDetail> =>
    fetchJson<BenchmarkRunDetail>(`/api/benchmarks/${encodeURIComponent(runId)}`),

  triggerBenchmarkRun: (suiteId?: string): Promise<BenchmarkRunDetail> => {
    const query = suiteId ? `?suite_id=${encodeURIComponent(suiteId)}` : '';
    return fetchJson<BenchmarkRunDetail>(`/api/benchmarks/run${query}`, { method: 'POST' });
  },
};
