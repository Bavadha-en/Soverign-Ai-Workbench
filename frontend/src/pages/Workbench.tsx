import React, { useCallback, useEffect, useRef, useState } from 'react';
import { AlertCircle, RotateCcw } from 'lucide-react';
import { PageHeader, Notice } from '../ui/primitives';
import { TaskComposer } from '../components/TaskComposer';
import { ExecutionTrace } from '../components/ExecutionTrace';
import { AgentAnswer } from '../components/AgentAnswer';
import { Deliverables } from '../components/Deliverables';
import { VerificationReport } from '../components/VerificationReport';
import { SourceEvidence } from '../components/SourceEvidence';
import { ModelRouting } from '../components/ModelRouting';
import { useToast } from '../ui/toast';
import { api } from '../services/api';
import type { AgentTaskState } from '../types/api';

const POLL_INTERVAL_MS = 750;

interface WorkbenchProps {
  presetTask?: string;
  onPresetConsumed: () => void;
}

export const Workbench: React.FC<WorkbenchProps> = ({ presetTask, onPresetConsumed }) => {
  const toast = useToast();
  const [taskText, setTaskText] = useState(presetTask ?? '');
  const [taskState, setTaskState] = useState<AgentTaskState | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<number | null>(null);

  const stopPolling = useCallback(() => {
    if (pollRef.current !== null) {
      window.clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  useEffect(() => stopPolling, [stopPolling]);

  useEffect(() => {
    if (presetTask) {
      setTaskText(presetTask);
      onPresetConsumed();
    }
  }, [presetTask, onPresetConsumed]);

  const poll = useCallback(
    async (taskId: string) => {
      try {
        const state = await api.getAgentTask(taskId);
        setTaskState(state);

        const status = (state.status || '').toUpperCase();
        if (status === 'COMPLETED' || status === 'FAILED') {
          stopPolling();
          setRunning(false);
          if (status === 'COMPLETED') {
            const count = state.generated_files?.length ?? 0;
            toast.success(
              count > 0
                ? `Run complete — ${count} deliverable${count === 1 ? '' : 's'} ready`
                : 'Run complete',
            );
          } else {
            toast.error('Run failed — see the runtime log for detail');
          }
        }
      } catch (pollError) {
        const message = (pollError as Error).message;
        // Transient network jitter is expected while the agent is busy; only a
        // missing task is fatal to the poll loop.
        if (message.includes('404')) {
          stopPolling();
          setRunning(false);
          setError('The run could not be found on the backend. It may have been restarted.');
        }
      }
    },
    [stopPolling, toast],
  );

  const runTask = useCallback(
    async (task: string, documentIds: string[]) => {
      stopPolling();
      setError(null);
      setTaskText(task);
      setTaskState(null);
      setRunning(true);

      try {
        const response = await api.runAgent({ task, document_ids: documentIds });

        setTaskState({
          task_id: response.task_id,
          status: response.status.toUpperCase(),
          current_step_index: response.steps_completed,
          plan: response.plan,
          completed_steps: [],
          retrieved_context: response.sources ?? [],
          intermediate_data: {},
          verification_results: response.verification ?? null,
          final_output: response.final_output,
          generated_files: response.generated_files ?? [],
          execution_trace: response.execution_trace ?? [],
          retry_count: 0,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          task,
          document_ids: documentIds,
        });

        const status = response.status.toUpperCase();
        if (status === 'COMPLETED' || status === 'FAILED') {
          setRunning(false);
          if (status === 'COMPLETED') {
            const count = response.generated_files?.length ?? 0;
            toast.success(
              count > 0
                ? `Run complete — ${count} deliverable${count === 1 ? '' : 's'} ready`
                : 'Run complete',
            );
          } else {
            toast.error('Run failed — see the runtime log for detail');
          }
        } else {
          pollRef.current = window.setInterval(() => poll(response.task_id), POLL_INTERVAL_MS);
        }
      } catch (runError) {
        setRunning(false);
        setError((runError as Error).message);
        toast.error('Could not start the run');
      }
    },
    [poll, stopPolling, toast],
  );

  const reset = () => {
    stopPolling();
    setRunning(false);
    setTaskState(null);
    setError(null);
  };

  return (
    <>
      <PageHeader
        title="Workbench"
        subtitle="Give the agent an engineering objective. It plans the work, runs each tool locally, verifies what it produced, and hands back signed-off documents."
        actions={
          taskState && !running ? (
            <button type="button" className="btn btn-secondary" onClick={reset}>
              <RotateCcw size={14} />
              Clear run
            </button>
          ) : undefined
        }
      />

      {error && (
        <Notice tone="danger" icon={<AlertCircle size={16} />}>
          <strong>Run could not start.</strong> {error}
        </Notice>
      )}

      <div className="split-workbench">
        <div className="stack gap-18">
          <TaskComposer
            onRun={runTask}
            running={running}
            activeTaskId={taskState?.task_id ?? null}
            presetTask={presetTask}
          />
          <AgentAnswer output={taskState?.final_output ?? null} status={taskState?.status ?? ''} />
          <ExecutionTrace taskState={taskState} running={running} />
        </div>

        <div className="stack gap-18">
          <Deliverables files={taskState?.generated_files ?? []} />
          <VerificationReport verification={taskState?.verification_results ?? null} />
          <SourceEvidence sources={taskState?.retrieved_context ?? []} />
          <ModelRouting task={taskText} />
        </div>
      </div>
    </>
  );
};
