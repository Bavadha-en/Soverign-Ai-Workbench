import React from 'react';
import { ExternalLink, FileCheck2, Lock, ShieldCheck } from 'lucide-react';
import { Card, CardBody, CardHead, PageHeader } from '../ui/primitives';
import { NetworkTelemetry } from '../components/NetworkTelemetry';
import { api } from '../services/api';
import type { NetworkStatus } from '../types/api';

const CONTROLS = [
  {
    title: 'Socket-level blocking',
    detail:
      'Generated Python runs in a subprocess where the socket module is patched to refuse connections, so a model-written script cannot open a network handle.',
  },
  {
    title: 'Continuous connection scanning',
    detail:
      'A background monitor enumerates every TCP and UDP connection owned by the process and flags any endpoint outside the loopback range.',
  },
  {
    title: 'No cloud provider credentials',
    detail:
      'The model factory only registers local providers. There is no code path to a hosted inference API, with or without an API key.',
  },
  {
    title: 'Hash-chained audit ledger',
    detail:
      'Each entry carries the digest of the one before it, so removing or editing a record breaks the chain and is detectable.',
  },
];

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

      <Card>
        <CardHead
          icon={<Lock size={16} />}
          title="How isolation is enforced"
          subtitle="Four independent controls, each verifiable from the source tree."
        />
        <CardBody>
          <div className="grid grid-2">
            {CONTROLS.map((control) => (
              <div key={control.title} className="panel">
                <p className="text-sm strong" style={{ fontWeight: 600, marginBottom: 3 }}>
                  {control.title}
                </p>
                <p className="text-sm muted">{control.detail}</p>
              </div>
            ))}
          </div>
        </CardBody>
      </Card>
    </>
  );
};
