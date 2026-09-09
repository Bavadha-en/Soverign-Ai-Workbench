import React, { useEffect, useState } from 'react';
import {
  ArrowRight,
  CheckCircle2,
  Database,
  FileSpreadsheet,
  FileText,
  ImageIcon,
  Package,
  ShieldCheck,
  SquareTerminal,
} from 'lucide-react';
import { Card, CardBody, CardHead, PageHeader, StatCard } from '../ui/primitives';
import { RuntimeHealth } from '../components/RuntimeHealth';
import { api } from '../services/api';
import type { RouteId } from '../app/navigation';
import type { HealthResponse, NetworkStatus, SystemStats, ToolDefinition } from '../types/api';

interface OverviewProps {
  health: HealthResponse | null;
  network: NetworkStatus | null;
  tools: ToolDefinition[];
  backendReachable: boolean;
  onNavigate: (id: RouteId) => void;
  onRunPreset: (task: string) => void;
}

const WORKFLOWS = [
  {
    title: 'Inspection report to approval note',
    detail: 'Reads the report, checks it against the SOPs, and drafts a Word approval note.',
    icon: <FileText size={17} />,
    tone: { fg: 'var(--brand-600)', bg: 'var(--brand-50)' },
    task: 'Analyse the attached inspection report, check the findings against the maintenance SOPs, and prepare an approval note with an executive summary.',
  },
  {
    title: 'Pump efficiency workbook',
    detail: 'Runs the calculation in the sandbox and exports a four-sheet Excel workbook.',
    icon: <FileSpreadsheet size={17} />,
    tone: { fg: 'var(--success-600)', bg: 'var(--success-50)' },
    task: 'Calculate pump efficiency for a flow rate of 50 m3/h, a head of 60 m and a shaft power of 11 kW, then produce a calculation workbook showing the working.',
  },
  {
    title: 'Component defect inspection',
    detail: 'Classifies visible damage on a component photo and ranks it by severity.',
    icon: <ImageIcon size={17} />,
    tone: { fg: 'var(--warning-600)', bg: 'var(--warning-50)' },
    task: 'Run a visual defect inspection on the attached component image, classify the anomaly and rank it by severity against the inspection guide.',
  },
];

const COMPLIANCE_CHECKS = [
  {
    label: 'No cloud AI providers configured',
    detail: 'Inference is served by the local Ollama runtime only.',
  },
  {
    label: 'Sandbox blocks socket creation',
    detail: 'Generated Python runs in a subprocess with networking patched out.',
  },
  {
    label: 'Every action is written to the ledger',
    detail: 'Tool calls, inferences and file writes are hash-chained.',
  },
  {
    label: 'Documents never leave the host',
    detail: 'Uploads, embeddings and outputs stay on local disk.',
  },
];

export const Overview: React.FC<OverviewProps> = ({
  health,
  network,
  tools,
  backendReachable,
  onNavigate,
  onRunPreset,
}) => {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loadingStats, setLoadingStats] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const data = await api.getSystemStats();
        if (!cancelled) setStats(data);
      } catch {
        if (!cancelled) setStats(null);
      } finally {
        if (!cancelled) setLoadingStats(false);
      }
    };

    load();
    const timer = window.setInterval(load, 15_000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  const externalAttempts = stats?.external_attempts ?? network?.external_ai_calls ?? 0;
  const isolated = externalAttempts === 0;
  const modelsReady = health?.models ? Object.values(health.models).filter(Boolean).length : 0;

  return (
    <>
      <PageHeader
        title="Operations overview"
        subtitle="An on-premise workbench for confidential engineering work. Every model, document and calculation stays inside this machine."
        actions={
          <button type="button" className="btn btn-primary" onClick={() => onNavigate('workbench')}>
            <SquareTerminal size={15} />
            Open workbench
          </button>
        }
      />

      <div className="grid grid-4">
        <StatCard
          label="Network isolation"
          value={isolated ? 'Air-gapped' : 'Attention'}
          compact
          icon={<ShieldCheck size={14} />}
          tone={isolated ? 'success' : 'danger'}
          footnote={`${externalAttempts} external ${externalAttempts === 1 ? 'attempt' : 'attempts'} recorded`}
        />
        <StatCard
          label="Tasks completed"
          value={stats?.tasks_completed ?? 0}
          icon={<CheckCircle2 size={14} />}
          tone="brand"
          loading={loadingStats && !stats}
          footnote={`${stats?.total_actions ?? 0} audited actions`}
        />
        <StatCard
          label="Deliverables produced"
          value={stats?.deliverables_generated ?? 0}
          icon={<Package size={14} />}
          tone="violet"
          loading={loadingStats && !stats}
          footnote="Word, Excel and PowerPoint"
        />
        <StatCard
          label="Knowledge base"
          value={stats?.chunks_indexed ?? 0}
          unit="chunks"
          icon={<Database size={14} />}
          tone="neutral"
          loading={loadingStats && !stats}
          footnote={`${stats?.kb_documents ?? 0} source documents indexed`}
        />
      </div>

      <div className="grid grid-2">
        <Card>
          <CardHead
            icon={<SquareTerminal size={16} />}
            title="Start a workflow"
            subtitle="Pre-built tasks that exercise the full pipeline end to end."
          />
          <CardBody>
            <div className="stack gap-10">
              {WORKFLOWS.map((workflow) => (
                <div key={workflow.title} className="panel panel-plain row gap-12">
                  <span
                    className="stat-icon shrink-0"
                    style={{ width: 36, height: 36, background: workflow.tone.bg, color: workflow.tone.fg }}
                  >
                    {workflow.icon}
                  </span>
                  <div className="grow">
                    <p className="text-sm strong" style={{ fontWeight: 600 }}>
                      {workflow.title}
                    </p>
                    <p className="text-xs muted">{workflow.detail}</p>
                  </div>
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm shrink-0"
                    onClick={() => onRunPreset(workflow.task)}
                    disabled={!backendReachable}
                  >
                    Run
                    <ArrowRight size={13} />
                  </button>
                </div>
              ))}
            </div>
          </CardBody>
          <footer className="card-footer">
            <span>
              {tools.length} tools registered · {modelsReady} models loaded · all running on this
              host
            </span>
          </footer>
        </Card>

        <RuntimeHealth health={health} />
      </div>

      <Card>
        <CardHead
          icon={<ShieldCheck size={16} />}
          title="Compliance posture"
          subtitle="What an auditor can verify about this deployment right now."
          actions={
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => onNavigate('sovereignty')}
            >
              Open evidence
              <ArrowRight size={13} />
            </button>
          }
        />
        <CardBody>
          <div className="grid grid-auto">
            {COMPLIANCE_CHECKS.map((check) => (
              <div key={check.label} className="panel row-top gap-10">
                <CheckCircle2 size={15} style={{ color: 'var(--success-600)', flexShrink: 0, marginTop: 1 }} />
                <div>
                  <p className="text-sm strong" style={{ fontWeight: 550 }}>
                    {check.label}
                  </p>
                  <p className="text-xs muted">{check.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </CardBody>
      </Card>
    </>
  );
};
