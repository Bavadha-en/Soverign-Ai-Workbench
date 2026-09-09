import React from 'react';
import { Binary, Brain, Cpu, Eye, Server } from 'lucide-react';
import { Card, CardBody, CardHead } from '../ui/primitives';
import { formatTime } from '../lib/format';
import type { HealthResponse } from '../types/api';

interface ModelSpec {
  key: string;
  id: string;
  role: string;
  icon: React.ReactNode;
}

const MODEL_SPECS: ModelSpec[] = [
  { key: 'general', id: 'llama3', role: 'Reasoning and report drafting', icon: <Brain size={15} /> },
  { key: 'coding', id: 'qwen2.5-coder:7b', role: 'Engineering scripts', icon: <Cpu size={15} /> },
  {
    // The health payload spells this key coding_heavy.
    key: 'coding_heavy',
    id: 'qwen2.5-coder:14b',
    role: 'Simulation and physics',
    icon: <Cpu size={15} />,
  },
  { key: 'vision', id: 'moondream', role: 'Defect inspection', icon: <Eye size={15} /> },
  {
    key: 'embedding',
    id: 'nomic-embed-text',
    role: 'Knowledge base embeddings',
    icon: <Binary size={15} />,
  },
];

export const RuntimeHealth: React.FC<{ health: HealthResponse | null }> = ({ health }) => {
  const models = health?.models ?? {};
  const ollamaReady = health?.ollama === 'available';
  const backendReady = health?.status === 'healthy';

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
              {ollamaReady ? 'Ollama online' : 'Fallback mode'}
            </p>
            <p className="text-xs faint">Open-weight models only</p>
          </div>

          <div className="panel">
            <p className="text-xs muted">Egress policy</p>
            <p className="text-base" style={{ fontWeight: 600, color: 'var(--success-700)' }}>
              Blocked
            </p>
            <p className="text-xs faint">No outbound AI calls permitted</p>
          </div>
        </div>

        <div>
          <p className="eyebrow" style={{ marginBottom: 8 }}>
            Model registry
          </p>
          <div className="stack gap-6">
            {MODEL_SPECS.map((spec) => {
              const ready = models[spec.key] ?? ollamaReady;
              return (
                <div key={spec.key} className="panel row-between">
                  <span className="row gap-10 truncate">
                    <span className="muted shrink-0">{spec.icon}</span>
                    <span className="truncate">
                      <span className="text-sm mono strong">{spec.id}</span>
                      <span className="text-xs muted" style={{ display: 'block' }}>
                        {spec.role}
                      </span>
                    </span>
                  </span>
                  <span className={`badge badge-${ready ? 'success' : 'neutral'} shrink-0`}>
                    <span className="dot" />
                    {ready ? 'Loaded' : 'Not loaded'}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </CardBody>
    </Card>
  );
};
