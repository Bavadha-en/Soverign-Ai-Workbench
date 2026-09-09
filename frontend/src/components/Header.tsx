import React from 'react';
import { ShieldCheck, Cpu, RefreshCw, Radio } from 'lucide-react';
import { HealthResponse, NetworkStatus } from '../types/api';

interface HeaderProps {
  health: HealthResponse | null;
  network: NetworkStatus | null;
  loading: boolean;
  onRefresh: () => void;
  activeTaskId?: string | null;
}

export const Header: React.FC<HeaderProps> = ({
  health,
  network,
  loading,
  onRefresh,
  activeTaskId,
}) => {
  const isAirGapped = network?.status === 'LOCAL_ONLY' && (network?.external_ai_calls ?? 0) === 0;
  const isHealthy = health?.status === 'healthy';

  return (
    <header className="app-header">
      <div className="header-left">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '6px',
              background: 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)',
              border: '1px solid #38bdf8',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 12px rgba(56, 189, 248, 0.3)',
            }}
          >
            <Cpu size={18} color="#ffffff" />
          </div>
          <div className="header-title-group">
            <div className="header-title">
              <span>{health?.app_name ? health.app_name.toUpperCase() : 'CONFIGIQ'}</span>
              <span className="header-title-badge">
                {health?.environment ? (health.environment.includes('air-gapped') ? 'AIR-GAPPED' : 'LOCAL') : 'SOVEREIGN'}
              </span>
            </div>
            <div className="header-subtitle">
              Sovereign On-Premise Industrial AI Workbench
            </div>
          </div>
        </div>
      </div>

      <div className="header-right">
        {activeTaskId && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: 'rgba(14, 165, 233, 0.1)',
              border: '1px solid rgba(56, 189, 248, 0.25)',
              padding: '3px 8px',
              borderRadius: '4px',
              fontSize: '11px',
              fontFamily: 'var(--font-mono)',
              color: 'var(--color-brand-light)',
            }}
          >
            <Radio size={12} className="spin" />
            <span>ACTIVE TASK: {activeTaskId.slice(0, 14)}...</span>
          </div>
        )}

        {/* Prominent Air-Gapped Sovereign Badge */}
        <div
          className={`status-pill ${isAirGapped ? 'air-gapped' : 'warning'}`}
          title="Air-Gapped Sovereign Security: Zero telemetry and 100% on-premise execution"
        >
          <ShieldCheck size={13} />
          <span className="status-dot pulse" style={{ backgroundColor: isAirGapped ? '#34d399' : '#fbbf24' }} />
          <span>{isAirGapped ? '● LOCAL / AIR-GAPPED' : 'NETWORK ALERT'}</span>
        </div>

        {/* Backend Connectivity Status */}
        <div
          className={`status-pill ${isHealthy ? 'online' : 'danger'}`}
          title={`Backend status: ${health?.status || 'disconnected'}`}
        >
          <span className="status-dot" style={{ backgroundColor: isHealthy ? '#38bdf8' : '#ef4444' }} />
          <span>BACKEND: {isHealthy ? 'ONLINE' : 'OFFLINE'}</span>
        </div>

        {/* Manual Refresh Trigger */}
        <button
          onClick={onRefresh}
          className="btn btn-secondary btn-sm"
          style={{ padding: '6px', display: 'flex', alignItems: 'center' }}
          title="Refresh System Status"
          disabled={loading}
        >
          <RefreshCw size={13} className={loading ? 'spin' : ''} />
        </button>
      </div>
    </header>
  );
};
