import React from 'react';
import { Binary, Brain, Cpu, Eye, Route } from 'lucide-react';
import { Card, CardBody, CardHead } from '../ui/primitives';

interface RouteSpec {
  purpose: string;
  model: string;
  detail: string;
  icon: React.ReactNode;
  keywords: string[];
  always?: boolean;
}

const ROUTES: RouteSpec[] = [
  {
    purpose: 'General reasoning',
    model: 'llama3',
    detail: 'SOP analysis, synthesis and approval-note drafting',
    icon: <Brain size={15} />,
    keywords: [],
  },
  {
    purpose: 'Engineering scripts',
    model: 'qwen2.5-coder:7b',
    detail: 'Python generation for sandboxed calculations',
    icon: <Cpu size={15} />,
    keywords: ['code', 'script', 'python'],
  },
  {
    purpose: 'Simulation and physics',
    model: 'qwen2.5-coder:14b',
    detail: 'Numerical simulation and bounds auditing',
    icon: <Cpu size={15} />,
    keywords: ['calculate', 'efficiency', 'physics', 'pump', 'thermal', 'simulation'],
  },
  {
    purpose: 'Visual inspection',
    model: 'moondream',
    detail: 'Defect classification and anomaly localisation',
    icon: <Eye size={15} />,
    keywords: ['image', 'defect', 'visual', 'anomaly', 'inspection'],
  },
  {
    purpose: 'Retrieval embeddings',
    model: 'nomic-embed-text',
    detail: 'Offline vector index over the knowledge base',
    icon: <Binary size={15} />,
    keywords: [],
    always: true,
  },
];

/** Mirrors the backend keyword classifier so the operator can see the choice up front. */
function isSelected(spec: RouteSpec, task: string): boolean {
  if (spec.always) return true;
  const lower = task.toLowerCase();
  if (spec.keywords.length === 0) {
    return !ROUTES.some(
      (other) => other.keywords.length > 0 && other.keywords.some((word) => lower.includes(word)),
    );
  }
  return spec.keywords.some((word) => lower.includes(word));
}

export const ModelRouting: React.FC<{ task?: string }> = ({ task = '' }) => (
  <Card>
    <CardHead
      icon={<Route size={16} />}
      title="Model routing"
      subtitle="The task is classified locally, then sent to the best-suited open-weight model."
    />
    <CardBody>
      <div className="stack gap-6">
        {ROUTES.map((spec) => {
          const selected = isSelected(spec, task);
          return (
            <div
              key={spec.model}
              className="panel row-between"
              style={
                selected
                  ? { background: 'var(--brand-50)', borderColor: 'var(--brand-200)' }
                  : undefined
              }
            >
              <span className="row gap-10 truncate">
                <span
                  className="shrink-0"
                  style={{ color: selected ? 'var(--brand-600)' : 'var(--text-faint)' }}
                >
                  {spec.icon}
                </span>
                <span className="truncate">
                  <span className="row gap-8">
                    <span className="text-sm strong" style={{ fontWeight: 550 }}>
                      {spec.purpose}
                    </span>
                    <span className="badge badge-neutral badge-square">{spec.model}</span>
                  </span>
                  <span className="text-xs muted" style={{ display: 'block' }}>
                    {spec.detail}
                  </span>
                </span>
              </span>

              {selected && (
                <span className="badge badge-brand shrink-0">
                  {spec.always ? 'Always on' : 'Selected'}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </CardBody>
  </Card>
);
