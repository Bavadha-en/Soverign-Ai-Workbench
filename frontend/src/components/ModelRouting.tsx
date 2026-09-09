import React, { useEffect, useState } from 'react';
import { Binary, Brain, Cpu, Eye, Route } from 'lucide-react';
import { Card, CardBody, CardHead, EmptyState } from '../ui/primitives';
import { api } from '../services/api';

/** Presentation for the role keys the backend registry reports. */
const ROLE_PRESENTATION: Record<string, { purpose: string; detail: string; icon: React.ReactNode }> = {
  general: {
    purpose: 'General reasoning',
    detail: 'SOP analysis, synthesis and approval-note drafting',
    icon: <Brain size={15} />,
  },
  coding: {
    purpose: 'Engineering scripts',
    detail: 'Python generation for sandboxed calculations',
    icon: <Cpu size={15} />,
  },
  coding_heavy: {
    purpose: 'Simulation and physics',
    detail: 'Numerical simulation and bounds auditing',
    icon: <Cpu size={15} />,
  },
  vision: {
    purpose: 'Visual inspection',
    detail: 'Defect classification and anomaly localisation',
    icon: <Eye size={15} />,
  },
  embedding: {
    purpose: 'Retrieval embeddings',
    detail: 'Offline vector index over the knowledge base',
    icon: <Binary size={15} />,
  },
};

interface ModelRoutingProps {
  /** Model the backend actually used for the current run, when known. */
  activeModel?: string | null;
}

export const ModelRouting: React.FC<ModelRoutingProps> = ({ activeModel }) => {
  const [registry, setRegistry] = useState<Record<string, string> | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .getModelRegistry()
      .then((response) => {
        if (!cancelled) setRegistry(response.registry ?? {});
      })
      .catch(() => {
        if (!cancelled) setRegistry({});
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const roles = registry ? Object.keys(registry) : [];

  return (
    <Card>
      <CardHead
        icon={<Route size={16} />}
        title="Model routing"
        subtitle="The backend classifies each task locally and dispatches it to the model registered for that role."
      />
      <CardBody>
        {roles.length === 0 ? (
          <EmptyState
            icon={<Route size={20} />}
            title="Registry unavailable"
            text="The backend has not reported its model registry yet."
          />
        ) : (
          <div className="stack gap-6">
            {roles.map((role) => {
              const model = registry?.[role] ?? role;
              const presentation = ROLE_PRESENTATION[role];
              // Only highlight a row when the backend reported this exact model.
              const isActive = Boolean(activeModel && model && activeModel.includes(model));

              return (
                <div
                  key={role}
                  className="panel row-between"
                  style={
                    isActive
                      ? { background: 'var(--brand-50)', borderColor: 'var(--brand-200)' }
                      : undefined
                  }
                >
                  <span className="row gap-10 truncate">
                    <span
                      className="shrink-0"
                      style={{ color: isActive ? 'var(--brand-600)' : 'var(--text-faint)' }}
                    >
                      {presentation?.icon ?? <Cpu size={15} />}
                    </span>
                    <span className="truncate">
                      <span className="row gap-8">
                        <span className="text-sm strong" style={{ fontWeight: 550 }}>
                          {presentation?.purpose ?? role}
                        </span>
                        <span className="badge badge-neutral badge-square">{model}</span>
                      </span>
                      {presentation?.detail && (
                        <span className="text-xs muted" style={{ display: 'block' }}>
                          {presentation.detail}
                        </span>
                      )}
                    </span>
                  </span>

                  {isActive && <span className="badge badge-brand shrink-0">Used this run</span>}
                </div>
              );
            })}
          </div>
        )}
      </CardBody>
    </Card>
  );
};
