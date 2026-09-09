import React from 'react';
import { Hexagon, Menu, RefreshCw, Search, ShieldCheck, ShieldAlert, X } from 'lucide-react';
import type { HealthResponse, NetworkStatus } from '../types/api';

interface TopBarProps {
  health: HealthResponse | null;
  network: NetworkStatus | null;
  backendReachable: boolean;
  refreshing: boolean;
  onRefresh: () => void;
  onOpenPalette: () => void;
  navOpen: boolean;
  onToggleNav: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({
  health,
  network,
  backendReachable,
  refreshing,
  onRefresh,
  onOpenPalette,
  navOpen,
  onToggleNav,
}) => {
  const isolated = network ? network.status === 'LOCAL_ONLY' && network.external_ai_calls === 0 : true;
  // The backend reports itself as "ConfigIQ Backend"; the product name is just ConfigIQ.
  const appName = (health?.app_name || 'ConfigIQ').replace(/\s*backend\s*$/i, '');

  return (
    <header className="topbar">
      <div className="brand">
        <button
          type="button"
          className="btn btn-ghost btn-icon nav-toggle"
          onClick={onToggleNav}
          aria-label={navOpen ? 'Close navigation' : 'Open navigation'}
          aria-expanded={navOpen}
        >
          {navOpen ? <X size={18} /> : <Menu size={18} />}
        </button>

        <span className="brand-mark" aria-hidden>
          <Hexagon size={18} strokeWidth={2.2} />
        </span>

        <div>
          <div className="brand-name">{appName}</div>
          <div className="brand-tagline">On-premise engineering workbench</div>
        </div>
      </div>

      <div className="topbar-actions">
        <button
          type="button"
          className="btn btn-secondary btn-sm topbar-search"
          onClick={onOpenPalette}
          style={{ gap: 10 }}
        >
          <Search size={14} />
          <span>Search</span>
          <kbd className="kbd">Ctrl K</kbd>
        </button>

        <span
          className={`badge ${isolated ? 'badge-success' : 'badge-warning'}`}
          title={
            isolated
              ? 'No external network egress detected. All inference is local.'
              : 'An outbound connection attempt was recorded — open Sovereignty for detail.'
          }
        >
          {isolated ? <ShieldCheck size={13} /> : <ShieldAlert size={13} />}
          {isolated ? 'Air-gapped' : 'Egress detected'}
        </span>

        <span
          className={`badge ${backendReachable ? 'badge-brand' : 'badge-danger'}`}
          title={backendReachable ? 'Backend responding' : 'Backend unreachable'}
        >
          <span className={`dot${backendReachable ? ' dot-live' : ''}`} />
          {backendReachable ? 'Connected' : 'Offline'}
        </span>

        <button
          type="button"
          className="btn btn-secondary btn-icon"
          onClick={onRefresh}
          disabled={refreshing}
          title="Refresh system status"
          aria-label="Refresh system status"
        >
          <RefreshCw size={15} className={refreshing ? 'spin' : undefined} />
        </button>
      </div>
    </header>
  );
};
