import React from 'react';
import {
  CheckCircle2,
  Clock,
  AlertTriangle,
  XCircle,
  Activity,
  Terminal,
  Layers,
  ClipboardList,
  Cog,
  Eye,
  ShieldCheck,
  PackageCheck,
  ChevronRight,
} from 'lucide-react';
import { AgentTaskState, PlanStep } from '../types/api';

const AGENT_PHASES = [
  { key: 'PLAN', label: 'PLAN', icon: ClipboardList, desc: 'Decompose task into tool-graph' },
  { key: 'ACT', label: 'ACT', icon: Cog, desc: 'Execute tools in sandbox' },
  { key: 'OBSERVE', label: 'OBSERVE', icon: Eye, desc: 'Collect and parse results' },
  { key: 'VERIFY', label: 'VERIFY', icon: ShieldCheck, desc: 'Fact-check & bounds-check' },
  { key: 'DELIVER', label: 'DELIVER', icon: PackageCheck, desc: 'Generate certified output' },
] as const;

function resolvePhaseIndex(status: string): number {
  const s = status.toUpperCase();
  if (s === 'PLANNING') return 0;
  if (s === 'EXECUTING') return 1;
  if (s === 'OBSERVING') return 2;
  if (s === 'VERIFYING' || s === 'RETRYING') return 3;
  if (s === 'COMPLETED') return 5; // past all phases
  if (s === 'FAILED') return -1;
  return 0;
}

interface AgentTraceProps {
  taskState: AgentTaskState | null;
  isRunning: boolean;
}

export const AgentTrace: React.FC<AgentTraceProps> = ({ taskState, isRunning }) => {
  if (!taskState) {
    return (
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <Layers size={14} color="#38bdf8" />
            <span>Agent Execution Plan & Live Trace</span>
          </div>
        </div>
        <div style={{ textAlign: 'center', padding: '30px 20px', color: 'var(--text-muted)' }}>
          <Activity size={28} style={{ opacity: 0.3, marginBottom: '8px' }} />
          <div style={{ fontSize: '13px', fontWeight: 500 }}>No Active Agent Task</div>
          <div style={{ fontSize: '11px', marginTop: '4px' }}>
            Submit an industrial objective above to launch autonomous plan graph execution.
          </div>
        </div>
      </div>
    );
  }

  const getStatusBadge = (status?: string | null) => {
    switch ((status || 'pending').toLowerCase()) {
      case 'completed':
        return (
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#10b981', fontSize: '11px', fontWeight: 600 }}>
            <CheckCircle2 size={13} />
            <span>COMPLETED</span>
          </span>
        );
      case 'running':
        return (
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#38bdf8', fontSize: '11px', fontWeight: 600 }}>
            <Activity size={13} className="spin" />
            <span>RUNNING</span>
          </span>
        );
      case 'failed':
        return (
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#ef4444', fontSize: '11px', fontWeight: 600 }}>
            <XCircle size={13} />
            <span>FAILED</span>
          </span>
        );
      case 'retrying':
        return (
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#f59e0b', fontSize: '11px', fontWeight: 600 }}>
            <AlertTriangle size={13} />
            <span>RETRYING</span>
          </span>
        );
      default:
        return (
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--text-muted)', fontSize: '11px' }}>
            <Clock size={13} />
            <span>PENDING</span>
          </span>
        );
    }
  };

  const getStateColor = (st?: string | null) => {
    switch ((st || 'PENDING').toUpperCase()) {
      case 'COMPLETED':
        return '#10b981';
      case 'FAILED':
        return '#ef4444';
      case 'VERIFYING':
        return '#c084fc';
      case 'RETRYING':
        return '#f59e0b';
      case 'EXECUTING':
      case 'PLANNING':
        return '#38bdf8';
      default:
        return '#94a3b8';
    }
  };

  const phaseIndex = resolvePhaseIndex(taskState.status);
  const isFailed = taskState.status.toUpperCase() === 'FAILED';

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">
          <Layers size={14} color="#38bdf8" />
          <span>Agent Execution Plan & State</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div
            style={{
              padding: '2px 8px',
              borderRadius: '4px',
              fontSize: '11px',
              fontWeight: 700,
              fontFamily: 'var(--font-mono)',
              color: getStateColor(taskState.status),
              backgroundColor: 'rgba(0, 0, 0, 0.3)',
              border: `1px solid ${getStateColor(taskState.status)}40`,
            }}
          >
            STATE: {taskState.status}
          </div>
          {isRunning && <span className="status-dot pulse" style={{ backgroundColor: '#38bdf8' }} />}
        </div>
      </div>

      {/* Agentic State Machine Stepper */}
      <div className="state-stepper" style={{ marginBottom: '16px' }}>
        {AGENT_PHASES.map((phase, idx) => {
          const Icon = phase.icon;
          const isActive = idx === phaseIndex;
          const isCompleted = phaseIndex > idx;
          const isFailedPhase = isFailed && idx === Math.max(0, phaseIndex);
          let cls = 'state-step';
          if (isActive) cls += ' active';
          else if (isCompleted) cls += ' completed';
          if (isFailedPhase) cls = 'state-step failed';
          return (
            <React.Fragment key={phase.key}>
              {idx > 0 && (
                <ChevronRight
                  size={16}
                  className={`state-arrow${isCompleted ? ' completed' : ''}`}
                />
              )}
              <div className={cls} title={phase.desc}>
                <Icon size={13} />
                <span>{phase.label}</span>
              </div>
            </React.Fragment>
          );
        })}
      </div>

      {/* Structured Plan Graph */}
      <div style={{ marginBottom: '16px' }}>
        <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600, marginBottom: '8px' }}>
          Execution Graph ({taskState.plan?.length || 0} Steps)
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {taskState.plan && taskState.plan.length > 0 ? (
            taskState.plan.map((step: PlanStep) => (
              <div
                key={step.step}
                style={{
                  padding: '8px 12px',
                  backgroundColor: step.status === 'running' ? 'rgba(56, 189, 248, 0.08)' : '#070b14',
                  border: `1px solid ${step.status === 'running' ? 'rgba(56, 189, 248, 0.3)' : 'var(--border-subtle)'}`,
                  borderRadius: '4px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '10px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: 0 }}>
                  <div
                    style={{
                      width: '20px',
                      height: '20px',
                      borderRadius: '50%',
                      backgroundColor: 'var(--bg-panel-elevated)',
                      border: '1px solid var(--border-active)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '10px',
                      fontWeight: 700,
                      color: 'var(--text-secondary)',
                      fontFamily: 'var(--font-mono)',
                      flexShrink: 0,
                    }}
                  >
                    {step.step}
                  </div>
                  <div style={{ minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
                        {step.tool}
                      </span>
                      {step.action && (
                        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                          ({step.action})
                        </span>
                      )}
                    </div>
                    {step.description && (
                      <div style={{ fontSize: '11px', color: 'var(--text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {step.description}
                      </div>
                    )}
                  </div>
                </div>

                <div style={{ flexShrink: 0 }}>
                  {getStatusBadge(step.status)}
                </div>
              </div>
            ))
          ) : (
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontStyle: 'italic' }}>
              Plan decomposition in progress...
            </div>
          )}
        </div>
      </div>

      {/* Raw Execution Log / Trace */}
      {taskState.execution_trace && taskState.execution_trace.length > 0 && (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600, marginBottom: '6px' }}>
            <Terminal size={12} />
            <span>Autonomous Execution Trace Log</span>
          </div>
          <div
            className="code-block"
            style={{
              maxHeight: '160px',
              fontSize: '11px',
              lineHeight: '1.6',
            }}
          >
            {taskState.execution_trace.map((traceLine: string, idx: number) => (
              <div key={idx} style={{ color: traceLine.includes('FAIL') || traceLine.includes('ERROR') ? '#f87171' : traceLine.includes('COMPLETED') ? '#34d399' : '#38bdf8' }}>
                {traceLine}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
