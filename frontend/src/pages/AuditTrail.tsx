import React, { useCallback, useEffect, useState } from 'react';
import {
  CheckCircle2,
  ExternalLink,
  FileCheck2,
  History,
  RefreshCw,
  Search,
  ShieldCheck,
  XCircle,
} from 'lucide-react';
import { Card, CardBody, CardHead, EmptyState, PageHeader, StatCard } from '../ui/primitives';
import { useToast } from '../ui/toast';
import { api } from '../services/api';
import { formatDuration, formatTime, shortId } from '../lib/format';
import type { AuditLogEntry } from '../types/api';

export const AuditTrail: React.FC = () => {
  const toast = useToast();
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [taskFilter, setTaskFilter] = useState('');
  const [limit, setLimit] = useState(50);
  const [loading, setLoading] = useState(true);

  const load = useCallback(
    async (filter: string, max: number) => {
      setLoading(true);
      try {
        const response = await api.getAuditLogs(filter.trim() || undefined, max);
        setLogs(response.logs ?? []);
      } catch (error) {
        toast.error(`Could not load the ledger: ${(error as Error).message}`);
        setLogs([]);
      } finally {
        setLoading(false);
      }
    },
    [toast],
  );

  useEffect(() => {
    load(taskFilter, limit);
    // Re-run on limit change only; the text filter is applied on submit.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [limit]);

  const failures = logs.filter(
    (log) => log.status.toUpperCase() !== 'SUCCESS' && log.status.toUpperCase() !== 'OK',
  ).length;
  const externals = logs.filter((log) => log.is_external).length;
  const totalDuration = logs.reduce((sum, log) => sum + (log.duration_ms || 0), 0);

  return (
    <>
      <PageHeader
        title="Audit trail"
        subtitle="Every tool call, model inference and file write, recorded in order with its duration and outcome. The record is what makes an AI-assisted decision defensible."
        actions={
          <>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => window.open(`${api.getBaseUrl()}/audit/report`, '_blank', 'noopener')}
            >
              <FileCheck2 size={14} />
              Export report
              <ExternalLink size={13} />
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => load(taskFilter, limit)}
              disabled={loading}
            >
              <RefreshCw size={14} className={loading ? 'spin' : undefined} />
              Refresh
            </button>
          </>
        }
      />

      <div className="grid grid-4">
        <StatCard
          label="Entries shown"
          value={logs.length}
          icon={<History size={14} />}
          tone="brand"
          footnote={`Most recent ${limit}`}
        />
        <StatCard
          label="Failed actions"
          value={failures}
          icon={<XCircle size={14} />}
          tone={failures === 0 ? 'success' : 'warning'}
          footnote={failures === 0 ? 'All actions succeeded' : 'Review the rows below'}
        />
        <StatCard
          label="External calls"
          value={externals}
          icon={<ShieldCheck size={14} />}
          tone={externals === 0 ? 'success' : 'danger'}
          footnote={externals === 0 ? 'Entirely on-premise' : 'Breaks the air-gap guarantee'}
        />
        <StatCard
          label="Recorded compute"
          value={formatDuration(totalDuration)}
          compact
          icon={<CheckCircle2 size={14} />}
          tone="violet"
          footnote="Summed across shown entries"
        />
      </div>

      <Card>
        <CardHead
          icon={<History size={16} />}
          title="Ledger"
          subtitle="Filter by run to reconstruct exactly what happened during a single task."
        />

        <CardBody>
          <form
            className="row wrap gap-10"
            onSubmit={(event) => {
              event.preventDefault();
              load(taskFilter, limit);
            }}
          >
            <div className="input-search">
              <Search size={15} />
              <input
                className="input"
                type="search"
                value={taskFilter}
                onChange={(event) => setTaskFilter(event.target.value)}
                placeholder="Filter by run id…"
                aria-label="Filter by run id"
              />
            </div>

            <div className="row gap-6 shrink-0">
              <label className="text-sm muted" htmlFor="log-limit">
                Rows
              </label>
              <select
                id="log-limit"
                className="select"
                style={{ width: 82 }}
                value={limit}
                onChange={(event) => setLimit(Number(event.target.value))}
              >
                <option value={25}>25</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
              </select>
            </div>

            <button type="submit" className="btn btn-primary shrink-0" disabled={loading}>
              Apply filter
            </button>
          </form>
        </CardBody>

        {logs.length === 0 ? (
          <CardBody>
            <EmptyState
              icon={<History size={20} />}
              title={loading ? 'Loading the ledger…' : 'No entries recorded yet'}
              text="Run a task from the workbench and every step it takes will be written here."
            />
          </CardBody>
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Action</th>
                  <th>Component</th>
                  <th>Run</th>
                  <th>Outcome</th>
                  <th>Duration</th>
                  <th>Scope</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => {
                  const succeeded = log.status.toUpperCase() === 'SUCCESS' || log.status.toUpperCase() === 'OK';
                  return (
                    <tr key={log.id}>
                      <td className="mono text-xs muted">{formatTime(log.timestamp)}</td>
                      <td className="mono text-sm strong">{log.action}</td>
                      <td className="text-sm">{log.component}</td>
                      <td className="mono text-xs muted" title={log.task_id ?? undefined}>
                        {log.task_id ? shortId(log.task_id) : 'system'}
                      </td>
                      <td>
                        <span className={`badge badge-${succeeded ? 'success' : 'danger'}`}>
                          {succeeded ? <CheckCircle2 size={12} /> : <XCircle size={12} />}
                          {log.status}
                        </span>
                      </td>
                      <td className="mono text-xs num">{formatDuration(log.duration_ms)}</td>
                      <td>
                        <span className={`badge badge-${log.is_external ? 'danger' : 'neutral'}`}>
                          {log.is_external ? 'External' : 'Local'}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </>
  );
};
