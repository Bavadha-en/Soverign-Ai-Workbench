import React, { useState, useEffect, useRef } from 'react';
import { TaskInput } from '../components/TaskInput';
import { AgentTrace } from '../components/AgentTrace';
import { ModelStatus } from '../components/ModelStatus';
import { DeliverablesPanel } from '../components/DeliverablesPanel';
import { VerificationPanel } from '../components/VerificationPanel';
import { SourcesPanel } from '../components/SourcesPanel';
import { api } from '../services/api';
import { AgentTaskState, AgentRunResponse } from '../types/api';
import { AlertCircle } from 'lucide-react';

interface WorkbenchProps {
  initialTask?: string;
}

export const Workbench: React.FC<WorkbenchProps> = ({ initialTask }) => {
  const [currentTaskText, setCurrentTaskText] = useState<string>(initialTask || '');
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
  const [taskState, setTaskState] = useState<AgentTaskState | null>(null);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const pollIntervalRef = useRef<number | null>(null);

  // Stop polling helper
  const stopPolling = () => {
    if (pollIntervalRef.current !== null) {
      window.clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  };

  // Cleanup polling timer when unmounting
  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, []);

  const pollTaskStatus = async (taskId: string) => {
    try {
      const state = await api.getAgentTask(taskId);
      setTaskState(state);

      const statusUpper = (state.status || '').toUpperCase();
      if (statusUpper === 'COMPLETED' || statusUpper === 'FAILED') {
        setIsRunning(false);
        stopPolling();
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      console.error('Task poll error:', msg);
      // do not abort immediately on minor network jitter, but stop if 404
      if (msg.includes('404')) {
        stopPolling();
        setIsRunning(false);
      }
    }
  };

  const handleRunAgent = async (task: string, documentIds: string[]) => {
    stopPolling();
    setErrorMessage(null);
    setCurrentTaskText(task);
    setIsRunning(true);
    setActiveTaskId(null);
    setTaskState(null);

    try {
      // Step 1: Call actual POST /agent/run
      const response: AgentRunResponse = await api.runAgent({
        task,
        document_ids: documentIds,
      });

      setActiveTaskId(response.task_id);

      // Initialize preliminary task state from run response
      const initialPlanState: AgentTaskState = {
        task_id: response.task_id,
        status: response.status.toUpperCase(),
        current_step_index: response.steps_completed,
        plan: response.plan,
        completed_steps: [],
        retrieved_context: response.sources || [],
        intermediate_data: {},
        verification_results: response.verification || null,
        final_output: response.final_output,
        generated_files: response.generated_files || [],
        execution_trace: response.execution_trace || [],
        retry_count: 0,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        task,
        document_ids: documentIds,
      };
      setTaskState(initialPlanState);

      const statusUpper = response.status.toUpperCase();
      if (statusUpper === 'COMPLETED' || statusUpper === 'FAILED') {
        setIsRunning(false);
      } else {
        // Step 2: Poll GET /agent/{task_id} every 750ms
        pollIntervalRef.current = window.setInterval(() => {
          pollTaskStatus(response.task_id);
        }, 750);
      }
    } catch (err: unknown) {
      setIsRunning(false);
      const msg = err instanceof Error ? err.message : String(err);
      setErrorMessage(`Agent execution error: ${msg}`);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
      {errorMessage && (
        <div
          style={{
            padding: '12px 16px',
            backgroundColor: 'var(--color-danger-bg)',
            border: '1px solid var(--color-danger)',
            borderRadius: '6px',
            color: '#f87171',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            fontSize: '13px',
          }}
        >
          <AlertCircle size={16} />
          <div>{errorMessage}</div>
        </div>
      )}

      {/* Main Workbench Grid */}
      <div className="grid-workbench">
        {/* Left Column: Input, Execution Graph Trace, Model Routing */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <TaskInput
            onRunAgent={handleRunAgent}
            isRunning={isRunning}
            activeTaskId={activeTaskId}
          />
          <AgentTrace taskState={taskState} isRunning={isRunning} />
          <ModelStatus currentTask={currentTaskText} />
        </div>

        {/* Right Column: Deliverables, Fact & Physics Verifier, SOP Sources */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <DeliverablesPanel files={taskState?.generated_files || []} />
          <VerificationPanel verification={taskState?.verification_results || null} />
          <SourcesPanel sources={taskState?.retrieved_context || []} />
        </div>
      </div>
    </div>
  );
};
