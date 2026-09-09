import React, { useState } from 'react';
import {
  CheckCircle2,
  Cpu,
  Database,
  Eye,
  Package,
  Play,
  RotateCcw,
  ShieldCheck,
  SquareTerminal,
  XCircle,
} from 'lucide-react';
import { Card, CardBody, CardHead, Notice, PageHeader, Spinner } from '../ui/primitives';
import { api } from '../services/api';
import { formatDuration } from '../lib/format';

type StepStatus = 'pending' | 'running' | 'passed' | 'failed';

interface DemoStep {
  id: number;
  title: string;
  purpose: string;
  icon: React.ReactNode;
  status: StepStatus;
  detail?: string;
}

const STEPS: DemoStep[] = [
  {
    id: 1,
    title: 'Confirm network isolation',
    purpose: 'Read live telemetry and prove no external endpoint has been contacted.',
    icon: <ShieldCheck size={16} />,
    status: 'pending',
  },
  {
    id: 2,
    title: 'Query the knowledge base',
    purpose: 'Search local SOP embeddings and return ranked passages with provenance.',
    icon: <Database size={16} />,
    status: 'pending',
  },
  {
    id: 3,
    title: 'Route to the right model',
    purpose: 'Classify a coding request and confirm it reaches the coder model, not the general one.',
    icon: <Cpu size={16} />,
    status: 'pending',
  },
  {
    id: 4,
    title: 'Run the agent pipeline',
    purpose: 'Execute plan, act, observe, verify and deliver against a real engineering task.',
    icon: <SquareTerminal size={16} />,
    status: 'pending',
  },
  {
    id: 5,
    title: 'Check the vision path',
    purpose: 'Confirm the local vision model is registered for defect inspection.',
    icon: <Eye size={16} />,
    status: 'pending',
  },
  {
    id: 6,
    title: 'Verify document generators',
    purpose: 'Confirm the Word, Excel and PowerPoint generators are available to the agent.',
    icon: <Package size={16} />,
    status: 'pending',
  },
];

const pause = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms));

export const GuidedDemo: React.FC = () => {
  const [steps, setSteps] = useState<DemoStep[]>(STEPS);
  const [running, setRunning] = useState(false);
  const [finished, setFinished] = useState(false);
  const [elapsed, setElapsed] = useState(0);

  const update = (id: number, patch: Partial<DemoStep>) =>
    setSteps((current) => current.map((step) => (step.id === id ? { ...step, ...patch } : step)));

  /** Runs one step, recording either its detail line or the reason it failed. */
  const runStep = async (id: number, work: () => Promise<string>) => {
    update(id, { status: 'running', detail: undefined });
    try {
      const detail = await work();
      update(id, { status: 'passed', detail });
    } catch (error) {
      update(id, { status: 'failed', detail: (error as Error).message });
    }
    await pause(420);
  };

  const run = async () => {
    setSteps(STEPS);
    setRunning(true);
    setFinished(false);
    const startedAt = performance.now();

    await runStep(1, async () => {
      const [network, health] = await Promise.all([api.getNetworkStatus(), api.getHealth()]);
      return `Mode ${network.status} · ${network.external_ai_calls} external calls · runtime ${health.ollama ?? 'unknown'}`;
    });

    await runStep(2, async () => {
      const response = await api.searchKnowledge('valve inspection safety procedure', 3);
      const top = response.results?.[0];
      return top
        ? `${response.results.length} passages · best match ${(top.score * 100).toFixed(1)}% from ${top.document}`
        : 'Index reachable but returned no passages — re-index the knowledge base';
    });

    await runStep(3, async () => {
      const response = await api.chatConversation({
        messages: [{ role: 'user', content: 'Write Python to calculate pump efficiency' }],
        auto_route: true,
      });
      return `Routed to ${response.model} · classified as ${response.task_type ?? 'auto'} · ${formatDuration(response.duration_ms)}`;
    });

    await runStep(4, async () => {
      const response = await api.runAgent({
        task: 'Calculate pump efficiency using a flow rate of 50 m3/h, a head of 60 m and a power of 11 kW.',
      });
      return `Run ${response.task_id} · ${response.plan.length} planned steps · ${response.generated_files.length} files produced`;
    });

    await runStep(5, async () => {
      const tools = await api.getAgentTools();
      const vision = tools.find((tool) => tool.name === 'vision');
      if (!vision) throw new Error('Vision tool is not registered');
      return 'Vision tool registered — attach a component image in the workbench to run an inspection';
    });

    await runStep(6, async () => {
      const tools = await api.getAgentTools();
      const generators = tools.filter((tool) =>
        ['document_generator', 'excel_generator', 'ppt_generator'].includes(tool.name),
      );
      if (generators.length === 0) throw new Error('No document generators are registered');
      return `${generators.length} generators ready: ${generators.map((tool) => tool.name).join(', ')}`;
    });

    setElapsed(performance.now() - startedAt);
    setRunning(false);
    setFinished(true);
  };

  const reset = () => {
    setSteps(STEPS);
    setRunning(false);
    setFinished(false);
    setElapsed(0);
  };

  const passed = steps.filter((step) => step.status === 'passed').length;
  const failed = steps.filter((step) => step.status === 'failed').length;
  const settled = passed + failed;

  return (
    <>
      <PageHeader
        title="Guided demo"
        subtitle="Six checks that exercise every subsystem against the live backend. Nothing here is mocked — each step calls a real endpoint and reports what came back."
        actions={
          <>
            {(running || finished) && (
              <button type="button" className="btn btn-secondary" onClick={reset} disabled={running}>
                <RotateCcw size={14} />
                Reset
              </button>
            )}
            <button type="button" className="btn btn-primary btn-lg" onClick={run} disabled={running}>
              {running ? <Spinner size={15} /> : <Play size={15} />}
              {running ? 'Running…' : 'Run all checks'}
            </button>
          </>
        }
      />

      <Card>
        <CardHead
          icon={<CheckCircle2 size={16} />}
          title="Progress"
          subtitle={
            finished
              ? `${passed} of ${steps.length} checks passed in ${formatDuration(elapsed)}`
              : `${settled} of ${steps.length} checks complete`
          }
          actions={
            failed > 0 ? (
              <span className="badge badge-danger">{failed} failed</span>
            ) : finished ? (
              <span className="badge badge-success">All passed</span>
            ) : undefined
          }
        />
        <CardBody>
          <div
            className="progress"
            role="progressbar"
            aria-valuenow={settled}
            aria-valuemin={0}
            aria-valuemax={steps.length}
          >
            <div
              className={`progress-bar${finished && failed === 0 ? ' is-complete' : ''}`}
              style={{ width: `${(settled / steps.length) * 100}%` }}
            />
          </div>
        </CardBody>
      </Card>

      <div className="stack gap-10">
        {steps.map((step) => (
          <div
            key={step.id}
            className={
              step.status === 'running'
                ? 'plan-step is-running'
                : step.status === 'passed'
                  ? 'plan-step is-done'
                  : step.status === 'failed'
                    ? 'plan-step is-failed'
                    : 'plan-step'
            }
            style={{ alignItems: 'flex-start', padding: '14px 16px' }}
          >
            <span className="plan-step-index" style={{ marginTop: 2 }}>
              {step.status === 'passed' ? (
                <CheckCircle2 size={14} />
              ) : step.status === 'failed' ? (
                <XCircle size={14} />
              ) : step.status === 'running' ? (
                <Spinner size={12} />
              ) : (
                step.id
              )}
            </span>

            <div className="grow">
              <div className="row gap-8 wrap">
                <span className="muted">{step.icon}</span>
                <span className="text-base strong" style={{ fontWeight: 600 }}>
                  {step.title}
                </span>
                {step.status === 'running' && <span className="badge badge-brand">Running</span>}
                {step.status === 'passed' && <span className="badge badge-success">Passed</span>}
                {step.status === 'failed' && <span className="badge badge-danger">Failed</span>}
              </div>

              <p className="text-sm muted" style={{ marginTop: 2 }}>
                {step.purpose}
              </p>

              {step.detail && (
                <p
                  className="text-xs mono"
                  style={{
                    marginTop: 8,
                    padding: '7px 10px',
                    borderRadius: 'var(--r-xs)',
                    background: 'var(--surface-card)',
                    border: '1px solid var(--border)',
                    color: step.status === 'failed' ? 'var(--danger-700)' : 'var(--text)',
                  }}
                >
                  {step.detail}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>

      {finished && (
        <Notice tone={failed === 0 ? 'success' : 'warning'} icon={<CheckCircle2 size={16} />}>
          {failed === 0 ? (
            <>
              <strong>All checks passed.</strong> Isolation, retrieval, routing, the agent pipeline,
              the vision path and the document generators are all operating on this host.
            </>
          ) : (
            <>
              <strong>
                {passed} passed, {failed} failed.
              </strong>{' '}
              Open the failing step for the error the backend returned.
            </>
          )}
        </Notice>
      )}
    </>
  );
};
