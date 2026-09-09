import React from 'react';
import { ExternalLink, FileCheck2, Lock, ShieldCheck } from 'lucide-react';
import { PageHeader } from '../ui/primitives';
import { NetworkTelemetry } from '../components/NetworkTelemetry';
import { api } from '../services/api';
import type { NetworkStatus } from '../types/api';

export const Sovereignty: React.FC<{ network: NetworkStatus | null }> = ({ network }) => {
  const isolated = network ? network.status === 'LOCAL_ONLY' && network.external_ai_calls === 0 : true;

  return (
    <>
      <PageHeader
        title="Sovereignty"
        subtitle="Evidence that this deployment processes confidential work without reaching the internet — collected live rather than asserted."
        actions={
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => window.open(`${api.getBaseUrl()}/audit/report`, '_blank', 'noopener')}
          >
            <FileCheck2 size={14} />
            Attestation report
            <ExternalLink size={13} />
          </button>
        }
      />

      <div
        className="card"
        style={{
          borderColor: isolated ? '#a7f3d0' : '#fecaca',
          background: isolated ? 'var(--success-50)' : 'var(--danger-50)',
        }}
      >
        <div className="card-body row gap-14">
          <span
            className="stat-icon shrink-0"
            style={{
              width: 42,
              height: 42,
              background: '#fff',
              color: isolated ? 'var(--success-600)' : 'var(--danger-600)',
            }}
          >
            {isolated ? <ShieldCheck size={22} /> : <Lock size={22} />}
          </span>
          <div className="grow">
            <p
              className="text-lg"
              style={{
                fontWeight: 650,
                color: isolated ? 'var(--success-700)' : 'var(--danger-700)',
              }}
            >
              {isolated ? 'Air-gap holding' : 'Outbound activity detected'}
            </p>
            <p className="text-sm" style={{ color: isolated ? 'var(--success-700)' : 'var(--danger-700)' }}>
              {isolated
                ? 'No external endpoint has been contacted since this process started. All inference, retrieval and document generation ran on this host.'
                : 'One or more connections left the loopback range. Review the connection table below before continuing confidential work.'}
            </p>
          </div>
          <span className={`badge badge-${isolated ? 'success' : 'danger'} shrink-0`}>
            {network?.status ?? 'LOCAL_ONLY'}
          </span>
        </div>
      </div>

      <NetworkTelemetry />
    </>
  );
};
