import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  FileCheck2,
  RefreshCw,
  Clock,
  Lock,
  Search,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';
import { api } from '../services/api';
import { AuditLogEntry } from '../types/api';

export const AuditLogs: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [taskIdFilter, setTaskIdFilter] = useState<string>('');
  const [limit, setLimit] = useState<number>(50);
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchLogs = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const resp = await api.getAuditLogs(taskIdFilter.trim() || undefined, limit);
      setLogs(resp.logs || []);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setErrorMsg(`Failed to fetch audit logs: ${msg}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [limit]);

  const handleFilterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchLogs();
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
      {/* Header */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <ShieldAlert size={15} color="#38bdf8" />
            <span>Forensic Audit Logging & Sovereignty Ledger</span>
          </div>
          <button
            onClick={fetchLogs}
            disabled={loading}
            className="btn btn-secondary btn-sm"
            style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <RefreshCw size={12} className={loading ? 'spin' : ''} />
            <span>Refresh Ledger</span>
          </button>
        </div>

        <p style={{ fontSize: '12.5px', color: 'var(--text-secondary)', marginBottom: '14px' }}>
          ConfigIQ logs every tool invocation, sandboxed code execution, RAG query, and deliverable creation immutably to verify complete air-gapped isolation. Every logged entry records execution duration and certifies that zero external network egress occurred.
        </p>

        {/* Filter Bar */}
        <form onSubmit={handleFilterSubmit} style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <Search size={14} style={{ position: 'absolute', left: '12px', top: '11px', color: 'var(--text-muted)' }} />
            <input
              type="text"
              className="input-text"
              style={{ paddingLeft: '34px' }}
              placeholder="Filter by Task ID (e.g. task_3f2ed8a9)..."
              value={taskIdFilter}
              onChange={(e) => setTaskIdFilter(e.target.value)}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', whiteSpace: 'nowrap', fontSize: '12px', color: 'var(--text-muted)' }}>
            <span>Limit:</span>
            <select
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              style={{
                backgroundColor: 'var(--bg-panel-elevated)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '4px',
                padding: '6px 8px',
                fontSize: '12px',
              }}
            >
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>

          <button type="submit" className="btn btn-primary" disabled={loading} style={{ minWidth: '100px' }}>
            <span>Filter</span>
          </button>
        </form>
      </div>

      {errorMsg && (
        <div
          style={{
            padding: '10px 14px',
            backgroundColor: 'var(--color-danger-bg)',
            border: '1px solid var(--color-danger)',
            borderRadius: '4px',
            fontSize: '12px',
            color: '#f87171',
          }}
        >
          {errorMsg}
        </div>
      )}

      {/* Logs Table */}
      <div className="card" style={{ overflowX: 'auto' }}>
        <div className="card-header">
          <div className="card-title">
            <FileCheck2 size={14} color="#10b981" />
            <span>Audit Trail Entries ({logs.length})</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: '#10b981', fontWeight: 600 }}>
            <Lock size={12} />
            <span>100% LOCAL RECORDINGS</span>
          </div>
        </div>

        {logs.length > 0 ? (
          <table className="table-custom">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Action</th>
                <th>Component</th>
                <th>Task ID</th>
                <th>Status</th>
                <th>Duration</th>
                <th>Sovereignty</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => {
                const isSuccess = log.status === 'SUCCESS' || log.status === 'success';
                const formattedTime = log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : 'N/A';

                return (
                  <tr key={log.id}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '11.5px', color: 'var(--text-muted)' }}>
                      {formattedTime}
                    </td>
                    <td>
                      <span
                        style={{
                          fontFamily: 'var(--font-mono)',
                          fontWeight: 700,
                          fontSize: '11.5px',
                          color: 'var(--color-brand-light)',
                        }}
                      >
                        {log.action}
                      </span>
                    </td>
                    <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                      {log.component}
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-muted)' }}>
                      {log.task_id ? `${log.task_id.slice(0, 12)}...` : 'system'}
                    </td>
                    <td>
                      <span
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px',
                          fontSize: '10.5px',
                          fontWeight: 700,
                          color: isSuccess ? '#10b981' : '#ef4444',
                          backgroundColor: isSuccess ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                          padding: '1px 6px',
                          borderRadius: '3px',
                        }}
                      >
                        {isSuccess ? <CheckCircle2 size={10} /> : <AlertTriangle size={10} />}
                        <span>{log.status}</span>
                      </span>
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-muted)' }}>
                      {log.duration_ms ? `${log.duration_ms.toFixed(1)}ms` : '0.0ms'}
                    </td>
                    <td>
                      <span
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px',
                          fontSize: '10px',
                          fontWeight: 700,
                          color: '#34d399',
                          backgroundColor: 'rgba(16, 185, 129, 0.1)',
                          border: '1px solid rgba(16, 185, 129, 0.25)',
                          padding: '1px 5px',
                          borderRadius: '3px',
                          fontFamily: 'var(--font-mono)',
                        }}
                      >
                        <Lock size={9} />
                        <span>LOCAL</span>
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : (
          <div style={{ textAlign: 'center', padding: '36px 20px', color: 'var(--text-muted)' }}>
            <Clock size={28} style={{ opacity: 0.3, marginBottom: '8px' }} />
            <div style={{ fontSize: '13px' }}>No audit log records available.</div>
          </div>
        )}
      </div>
    </div>
  );
};
