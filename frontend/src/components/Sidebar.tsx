import React from 'react';
import {
  LayoutDashboard,
  Terminal,
  Database,
  ShieldAlert,
  Server,
  Cpu,
  Layers,
} from 'lucide-react';

export type NavTab = 'dashboard' | 'workbench' | 'knowledge' | 'network' | 'audit_logs' | 'system';

interface SidebarProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  toolCount?: number;
  unsupportedClaimsCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  toolCount = 11,
}) => {
  return (
    <aside className="app-sidebar">
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div className="nav-section">
          <span className="nav-label">Core Modules</span>
          <button
            className={`nav-item ${currentTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => onSelectTab('dashboard')}
          >
            <LayoutDashboard size={15} />
            <span>Dashboard</span>
          </button>
          <button
            className={`nav-item ${currentTab === 'workbench' ? 'active' : ''}`}
            onClick={() => onSelectTab('workbench')}
          >
            <Terminal size={15} />
            <span>Workbench</span>
          </button>
          <button
            className={`nav-item ${currentTab === 'knowledge' ? 'active' : ''}`}
            onClick={() => onSelectTab('knowledge')}
          >
            <Database size={15} />
            <span>Knowledge Base</span>
          </button>
          <button
            className={`nav-item ${currentTab === 'network' ? 'active' : ''}`}
            onClick={() => onSelectTab('network')}
          >
            <ShieldAlert size={15} color="#38bdf8" />
            <span>Network & Sovereignty</span>
          </button>
          <button
            className={`nav-item ${currentTab === 'audit_logs' ? 'active' : ''}`}
            onClick={() => onSelectTab('audit_logs')}
          >
            <ShieldAlert size={15} />
            <span>Audit Logs</span>
          </button>
        </div>


        <div className="nav-section">
          <span className="nav-label">Engine & Platform</span>
          <button
            className={`nav-item ${currentTab === 'system' ? 'active' : ''}`}
            onClick={() => onSelectTab('system')}
          >
            <Server size={15} />
            <span>System & Model Routing</span>
          </button>
        </div>

        <div className="nav-section" style={{ marginTop: '8px' }}>
          <div
            style={{
              padding: '10px 12px',
              backgroundColor: 'rgba(2, 132, 199, 0.08)',
              border: '1px solid rgba(56, 189, 248, 0.15)',
              borderRadius: '4px',
              fontSize: '11px',
              color: 'var(--text-secondary)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--color-brand-light)', fontWeight: 600, marginBottom: '4px' }}>
              <Layers size={13} />
              <span>Orchestrator Tools</span>
            </div>
            <div>{toolCount} Local Tools Registered</div>
            <div style={{ color: 'var(--text-muted)', fontSize: '10px', marginTop: '2px' }}>
              Phase 5A Deliverables Active
            </div>
          </div>
        </div>
      </div>

      <div className="sidebar-footer">
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-secondary)', marginBottom: '3px' }}>
          <Cpu size={12} />
          <span>ConfigIQ v1.0.0</span>
        </div>
        <div style={{ fontSize: '10px', color: '#10b981' }}>
          Air-Gapped Node #1
        </div>
      </div>
    </aside>
  );
};
