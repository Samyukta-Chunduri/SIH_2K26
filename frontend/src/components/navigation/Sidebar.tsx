import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  ShieldAlert,
  Radio,
  UserCheck,
  Layers,
  FileCheck2,
  BarChart3,
  Cpu,
  Lock,
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const navItems = [
    { to: '/', label: 'Overview', icon: ShieldAlert },
    { to: '/quantum', label: 'Quantum Telemetry', icon: Radio },
    { to: '/threats', label: 'Threat Detectors', icon: UserCheck },
    { to: '/fusion', label: 'Fusion & M12', icon: Layers },
    { to: '/evaluation', label: 'Evaluation (M17)', icon: FileCheck2 },
    { to: '/benchmarking', label: 'Benchmarks (M18)', icon: BarChart3 },
  ];

  return (
    <aside
      style={{
        width: '240px',
        backgroundColor: 'var(--bg-secondary)',
        borderRight: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        flexShrink: 0,
      }}
    >
      {/* Brand Header */}
      <div
        style={{
          padding: 'var(--space-5)',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          gap: '0.6rem',
        }}
      >
        <div
          style={{
            width: '32px',
            height: '32px',
            borderRadius: 'var(--radius-md)',
            background: 'linear-gradient(135deg, var(--accent-cyan), var(--accent-indigo))',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#ffffff',
            boxShadow: '0 0 12px var(--accent-cyan-glow)',
          }}
        >
          <Lock size={18} />
        </div>
        <div>
          <div style={{ fontWeight: 800, fontSize: '1.05rem', letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
            Q-SHIELD
          </div>
          <div style={{ fontSize: '0.68rem', color: 'var(--accent-cyan)', fontWeight: 600 }}>
            SIH 26141 • Quantum Security
          </div>
        </div>
      </div>

      {/* Navigation Links */}
      <nav style={{ flex: 1, padding: 'var(--space-4) var(--space-3)' }}>
        <div
          style={{
            fontSize: '0.68rem',
            fontWeight: 700,
            textTransform: 'uppercase',
            color: 'var(--text-muted)',
            padding: '0 0.75rem 0.5rem 0.75rem',
            letterSpacing: '0.05em',
          }}
        >
          Security Modules
        </div>
        <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  end={item.to === '/'}
                  style={({ isActive }) => ({
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.65rem',
                    padding: '0.6rem 0.75rem',
                    borderRadius: 'var(--radius-md)',
                    color: isActive ? '#ffffff' : 'var(--text-secondary)',
                    backgroundColor: isActive ? 'var(--accent-cyan-subtle)' : 'transparent',
                    border: isActive ? '1px solid var(--border-card)' : '1px solid transparent',
                    fontWeight: isActive ? 600 : 500,
                    fontSize: '0.85rem',
                    textDecoration: 'none',
                    transition: 'all var(--transition-fast)',
                  })}
                >
                  <Icon size={17} style={{ flexShrink: 0 }} />
                  <span>{item.label}</span>
                </NavLink>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Architecture Invariant Footer */}
      <div
        style={{
          padding: 'var(--space-4)',
          borderTop: '1px solid var(--border-subtle)',
          fontSize: '0.72rem',
          color: 'var(--text-muted)',
          backgroundColor: 'rgba(0, 0, 0, 0.2)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: 'var(--accent-cyan)', fontWeight: 600, marginBottom: '0.2rem' }}>
          <Cpu size={13} />
          <span>Security Invariant</span>
        </div>
        <p style={{ margin: 0, lineHeight: 1.35 }}>
          M12 is the sole final decision authority. M19 visualizes and persists.
        </p>
      </div>
    </aside>
  );
};
