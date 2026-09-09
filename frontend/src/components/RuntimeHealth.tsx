import React, { useEffect, useState } from 'react';
import { Binary, Brain, Cpu, Eye, Server } from 'lucide-react';
import { Card, CardBody, CardHead } from '../ui/primitives';
import { api } from '../services/api';
import { formatTime } from '../lib/format';
import type { HealthResponse } from '../types/api';

/** Role keys the backend reports, with the label and icon used to present them. */
const ROLE_PRESENTATION: Record<string, { label: string; icon: React.ReactNode }> = {
  general: { label: 'Reasoning and report drafting', icon: <Brain size={15} /> },
  coding: { label: 'Engineering scripts', icon: <Cpu size={15} /> },
  coding_heavy: { label: 'Simulation and physics', icon: <Cpu size={15} /> },
  vision: { label: 'Defect inspection', icon: <Eye size={15} /> },
  embedding: { label: 'Knowledge base embeddings', icon: <Binary size={15} /> },
};

export const RuntimeHealth: React.FC<{ health: HealthResponse | null }> = ({ health }) => {
  const [registry, setRegistry] = useState<Record<string, string>>({});

  useEffect(() => {
    let cancelled = false;
    api
      .getModelRegistry()
      .then((response) => {
        if (!cancelled) setRegistry(response.registry ?? {});
      })
      .catch(() => {
        // Without the registry the role rows simply show no model name.
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const models = health?.models ?? {};
  const ollamaReady = health?.ollama === 'available';
  const backendReady = health?.status === 'healthy';

  // Drive the list from what the backend actually reports, not a fixed list.
  const roles = Object.keys({ ...registry, ...models });

  return (
    <Card>
      <CardHead
        icon={<Server size={16} />}
        title="Runtime"
        subtitle={health?.version ? `Version ${health.version}` : undefined}
        actions={<span className="text-xs muted">Checked {formatTime(health?.timestamp)}</span>}
      />

      <CardBody className="stack gap-16">
        <div className="grid grid-3" style={{ gap: 10 }}>
          <div className="panel">
            <p className="text-xs muted">API service</p>
            <p
              className="text-base"
              style={{ fontWeight: 600, color: backendReady ? 'var(--success-700)' : 'var(--danger-700)' }}
            >
              {backendReady ? 'Healthy' : 'Unreachable'}
            </p>
            <p className="text-xs faint">{health?.environment || 'On-premise node'}</p>
          </div>

          <div className="panel">
            <p className="text-xs muted">Model runtime</p>
            <p
              className="text-base"
              style={{ fontWeight: 600, color: ollamaReady ? 'var(--success-700)' : 'var(--warning-700)' }}
            >
              {ollamaReady ? 'Ollama online' : 'Unavailable'}
            </p>
            <p className="text-xs faint">Open-weight models only</p>
          </div>

          <div className="panel">
            <p className="text-xs muted">Network mode</p>
            <p className="text-base" style={{ fontWeight: 600, color: 'var(--success-700)' }}>
              {health?.network || 'LOCAL_ONLY'}
            </p>
            <p className="text-xs faint">Reported by the backend</p>
          </div>
        </div>

        {roles.length > 0 && (
          <div>
            <p className="eyebrow" style={{ marginBottom: 8 }}>
              Model registry
            </p>
            <div className="stack gap-6">
              {roles.map((role) => {
                const presentation = ROLE_PRESENTATION[role];
                const modelName = registry[role];
                const loaded = models[role] ?? false;

                return (
                  <div key={role} className="panel row-between">
                    <span className="row gap-10 truncate">
                      <span className="muted shrink-0">{presentation?.icon ?? <Cpu size={15} />}</span>
                      <span className="truncate">
                        <span className="text-sm mono strong">{modelName ?? role}</span>
                        <span className="text-xs muted" style={{ display: 'block' }}>
                          {presentation?.label ?? role}
                        </span>
                      </span>
                    </span>
                    <span className={`badge badge-${loaded ? 'success' : 'neutral'} shrink-0`}>
                      <span className="dot" />
                      {loaded ? 'Loaded' : 'Not loaded'}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </CardBody>
    </Card>
  );
};
