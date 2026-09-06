import React, { useEffect, useState } from 'react';
import { Play, CheckCircle2, AlertCircle } from 'lucide-react';
import { api } from '../../api/client';
import type { ScenarioTemplate } from '../../types';

interface NavbarProps {
  onScenarioExecuted?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onScenarioExecuted }) => {
  const [healthy, setHealthy] = useState<boolean | null>(null);
  const [scenarios, setScenarios] = useState<ScenarioTemplate[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<string>('honest');
  const [executing, setExecuting] = useState(false);
  const [lastVerdict, setLastVerdict] = useState<string | null>(null);

  useEffect(() => {
    // 1. Check health
    api
      .checkHealth()
      .then((res) => setHealthy(res.status === 'ok'))
      .catch(() => setHealthy(false));

    // 2. Load templates
    api
      .getScenarioTemplates()
      .then((res) => {
        setScenarios(res);
        if (res.length > 0) setSelectedScenario(res[0].scenario_type);
      })
      .catch(() => {});
  }, []);

  const handleExecuteScenario = async () => {
    if (!selectedScenario || executing) return;
    setExecuting(true);
    setLastVerdict(null);
    try {
      const result = await api.verifyScenario({
        scenario_type: selectedScenario,
        session_id: `demo_${Date.now().toString(36)}`,
      });
      setLastVerdict(result.event.verdict);
      if (onScenarioExecuted) {
        onScenarioExecuted();
      }
    } catch (err) {
      console.error('Failed to execute scenario', err);
    } finally {
      setExecuting(false);
    }
  };

  return (
    <header
      style={{
        height: '60px',
        backgroundColor: 'var(--bg-secondary)',
        borderBottom: '1px solid var(--border-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 var(--space-8)',
        zIndex: 10,
      }}
    >
      {/* Backend Engine Status Indicator */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.25rem 0.6rem',
            borderRadius: 'var(--radius-full)',
            fontSize: '0.75rem',
            fontWeight: 600,
            background: healthy ? 'var(--verdict-accept-bg)' : 'var(--verdict-attack-bg)',
            color: healthy ? 'var(--verdict-accept)' : 'var(--verdict-attack)',
            border: `1px solid ${healthy ? 'var(--verdict-accept-border)' : 'var(--verdict-attack-border)'}`,
          }}
        >
          {healthy ? <CheckCircle2 size={13} /> : <AlertCircle size={13} />}
          <span>{healthy ? 'FastAPI Backend Online' : 'Connecting to API...'}</span>
        </div>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>|</span>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
          Simulation Engine • Frozen M0–M18
        </span>
      </div>

      {/* Quick Scenario Executor */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <label htmlFor="scenario-select" style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            Demo Scenario:
          </label>
          <select
            id="scenario-select"
            className="select"
            value={selectedScenario}
            onChange={(e) => setSelectedScenario(e.target.value)}
            style={{ width: '220px', padding: '0.35rem 0.6rem', fontSize: '0.8rem' }}
          >
            {scenarios.map((s) => (
              <option key={s.scenario_type} value={s.scenario_type}>
                {s.name} ({s.expected_verdict})
              </option>
            ))}
          </select>
        </div>

        <button
          className="btn btn-primary"
          onClick={handleExecuteScenario}
          disabled={executing || !healthy}
          style={{ padding: '0.35rem 0.85rem', fontSize: '0.8rem' }}
        >
          <Play size={13} fill="currentColor" />
          <span>{executing ? 'Evaluating Pipeline...' : 'Execute Scenario'}</span>
        </button>

        {lastVerdict && (
          <span
            style={{
              fontSize: '0.75rem',
              fontWeight: 700,
              padding: '0.2rem 0.5rem',
              borderRadius: 'var(--radius-sm)',
              color:
                lastVerdict === 'ACCEPT'
                  ? 'var(--verdict-accept)'
                  : lastVerdict === 'SUSPICIOUS'
                  ? 'var(--verdict-suspicious)'
                  : 'var(--verdict-attack)',
              background: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            M12 Result: {lastVerdict}
          </span>
        )}
      </div>
    </header>
  );
};
