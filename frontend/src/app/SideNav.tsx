import React from 'react';
import { Cpu, Lock } from 'lucide-react';
import { NAV_GROUPS, ROUTES, type RouteId } from './navigation';

interface SideNavProps {
  current: RouteId;
  onNavigate: (id: RouteId) => void;
  toolCount: number;
  modelCount: number;
  open: boolean;
  onClose: () => void;
}

export const SideNav: React.FC<SideNavProps> = ({
  current,
  onNavigate,
  toolCount,
  modelCount,
  open,
  onClose,
}) => (
  <>
    {open && <div className="sidenav-scrim" onClick={onClose} aria-hidden />}

    <nav className={`sidenav${open ? ' is-open' : ''}`} aria-label="Primary">
      <div>
        {NAV_GROUPS.map((group) => (
          <div className="nav-group" key={group}>
            <p className="nav-group-label">{group}</p>
            {ROUTES.filter((route) => route.group === group).map((route) => {
              const Icon = route.icon;
              const isCurrent = route.id === current;
              return (
                <button
                  key={route.id}
                  type="button"
                  className="nav-item"
                  aria-current={isCurrent ? 'page' : undefined}
                  onClick={() => onNavigate(route.id)}
                >
                  <Icon size={16} />
                  <span className="truncate">{route.label}</span>
                </button>
              );
            })}
          </div>
        ))}
      </div>

      <div className="sidenav-footer">
        <div className="row gap-6" style={{ marginBottom: 4 }}>
          <Cpu size={13} />
          <span>
            {modelCount} local {modelCount === 1 ? 'model' : 'models'} · {toolCount} tools
          </span>
        </div>
        <div className="row gap-6" style={{ color: 'var(--success-700)' }}>
          <Lock size={13} />
          <span>Air-gapped deployment</span>
        </div>
      </div>
    </nav>
  </>
);
