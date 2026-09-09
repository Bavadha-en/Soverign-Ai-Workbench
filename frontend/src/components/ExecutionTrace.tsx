import React from 'react';
import {
  CheckCircle2,
  ClipboardList,
  Cog,
  Eye,
  GitBranch,
  PackageCheck,
  ShieldCheck,
  Terminal,
  XCircle,
} from 'lucide-react';
import { Card, CardBody, CardHead, EmptyState, SectionLabel, Spinner } from '../ui/primitives';
import type { AgentTaskState, PlanStep } from '../types/api';

const PHASES = [
  { key: 'PLAN', label: 'Plan', icon: ClipboardList, desc: 'Break the objective into tool calls' },
  { key: 'ACT', label: 'Act', icon: Cog, desc: 'Execute each tool in order' },
  { key: 'OBSERVE', label: 'Observe', icon: Eye, desc: 'Collect and parse results' },
  { key: 'VERIFY', label: 'Verify', icon: ShieldCheck, desc: 'Check claims and physical bounds' },
  { key: 'DELIVER', label: 'Deliver', icon: PackageCheck, desc: 'Produce signed-off documents' },
] as const;

/** Maps the backend task status onto the five-phase pipeline. */
function phaseIndexFor(status: string): number {
  switch (status.toUpperCase()) {
    case 'PLANNING':
      return 0;
    case 'EXECUTING':
      return 1;
    case 'OBSERVING':
      return 2;
    case 'VERIFYING':
    case 'RETRYING':
      return 3;
    case 'COMPLETED':
      return PHASES.length; // every phase behind us
    case 'FAILED':
      return -1;
    default:
      return 0;
  }
}

function stepClass(status: string): string {
  switch ((status || 'pending').toLowerCase()) {
    case 'running':
      return 'plan-step is-running';
    case 'completed':
      return 'plan-step is-done';
    case 'failed':
      return 'plan-step is-failed';
    default:
      return 'plan-step';
  }
}

const StepStatus: React.FC<{ status: string }> = ({ status }) => {
  switch ((status || 'pending').toLowerCase()) {
    case 'completed':
      return (
        <span className="badge badge-success">
          <CheckCircle2 size={12} />
          Done
        </span>
      );
    case 'running':
      return (
        <span className="badge badge-brand">
          <Spinner size={11} />
          Running
        </span>
      );
    case 'failed':
      return (
        <span className="badge badge-danger">
          <XCircle size={12} />
          Failed
        </span>
      );
    case 'retried':
      return <span className="badge badge-warning">Retried</span>;
    default:
      return <span className="badge badge-neutral">Queued</span>;
  }
};

function traceLineClass(line: string): string {
  const upper = line.toUpperCase();
  if (upper.includes('FAIL') || upper.includes('ERROR')) return 'code-line code-line-err';
  if (upper.includes('COMPLETED') || upper.includes('SUCCESS')) return 'code-line code-line-ok';
  return 'code-line code-line-info';
}

interface ExecutionTraceProps {
  taskState: AgentTaskState | null;
  running: boolean;
}

export const ExecutionTrace: React.FC<ExecutionTraceProps> = ({ taskState, running }) => {
  if (!taskState) {
    return (
      <Card>
        <CardHead icon={<GitBranch size={16} />} title="Execution plan" />
        <CardBody>
          <EmptyState
            icon={<GitBranch size={20} />}
            title="No run in progress"
            text="Submit a task and the plan, each tool call and the raw trace will appear here as it executes."
          />
        </CardBody>
      </Card>
    );
  }

  const status = (taskState.status || '').toUpperCase();
  const failed = status === 'FAILED';
  const phaseIndex = phaseIndexFor(status);
  const plan = taskState.plan ?? [];
  const trace = taskState.execution_trace ?? [];

  const statusTone =
    status === 'COMPLETED' ? 'success' : failed ? 'danger' : running ? 'brand' : 'neutral';

  return (
    <Card>
      <CardHead
        icon={<GitBranch size={16} />}
        title="Execution plan"
        subtitle={`${plan.length} step${plan.length === 1 ? '' : 's'} · run ${taskState.task_id}`}
        actions={
          <span className={`badge badge-${statusTone}`}>
            {running && <Spinner size={11} />}
            {status || 'PENDING'}
          </span>
        }
      />

      <CardBody className="stack gap-18">
        <div className="pipeline">
          {PHASES.map((phase, index) => {
            const Icon = phase.icon;
            let className = 'pipeline-step';
            if (failed && index === Math.max(0, phaseIndex)) className += ' is-failed';
            else if (index === phaseIndex) className += ' is-active';
            else if (index < phaseIndex) className += ' is-done';

            return (
              <div key={phase.key} className={className}>
                <span className="pipeline-step-name">
                  <Icon size={13} />
                  {phase.label}
                </span>
                <span className="pipeline-step-desc">{phase.desc}</span>
              </div>
            );
          })}
        </div>

        <div>
          <SectionLabel>Tool calls</SectionLabel>
          {plan.length === 0 ? (
            <p className="text-sm muted">Decomposing the objective…</p>
          ) : (
            <div className="stack gap-6">
              {plan.map((step: PlanStep) => (
                <div key={step.step} className={stepClass(step.status)}>
                  <span className="plan-step-index">{step.step}</span>
                  <div className="grow">
                    <div className="row gap-8">
                      <span className="mono text-sm strong">{step.tool}</span>
                      {step.action && <span className="text-xs muted">{step.action}</span>}
                    </div>
                    {step.description && (
                      <p className="text-xs muted truncate" title={step.description}>
                        {step.description}
                      </p>
                    )}
                    {step.error && <p className="text-xs" style={{ color: 'var(--danger-700)' }}>{step.error}</p>}
                  </div>
                  <StepStatus status={step.status} />
                </div>
              ))}
            </div>
          )}
        </div>

        {trace.length > 0 && (
          <div>
            <SectionLabel
              right={<span className="text-xs faint">{trace.length} entries</span>}
            >
              <span className="row gap-6">
                <Terminal size={12} />
                Runtime log
              </span>
            </SectionLabel>
            <div className="code" style={{ maxHeight: 190 }}>
              {trace.map((line, index) => (
                <span key={index} className={traceLineClass(line)}>
                  {line}
                </span>
              ))}
            </div>
          </div>
        )}
      </CardBody>
    </Card>
  );
};
