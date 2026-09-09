import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Activity, EthernetPort, Fingerprint, Pause, Play, Radar, ShieldX } from 'lucide-react';
import { Card, CardBody, CardHead, EmptyState, StatCard } from '../ui/primitives';
import { api } from '../services/api';
import { formatTime } from '../lib/format';
import type { NetworkTelemetry as Telemetry } from '../types/api';

const POLL_MS = 2000;

export const NetworkTelemetry: React.FC = () => {
  const [telemetry, setTelemetry] = useState<Telemetry | null>(null);
  const [live, setLive] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<string>('');
  const [failed, setFailed] = useState(false);
  const timerRef = useRef<number | null>(null);

  const poll = useCallback(async () => {
    try {
      setTelemetry(await api.getNetworkTelemetry());
      setLastUpdate(new Date().toISOString());
      setFailed(false);
    } catch {
      setFailed(true);
    }
  }, []);

  useEffect(() => {
    poll();
    if (live) {
      timerRef.current = window.setInterval(poll, POLL_MS);
    }
    return () => {
      if (timerRef.current !== null) window.clearInterval(timerRef.current);
    };
  }, [live, poll]);

  const externalCalls = telemetry?.external_ai_calls ?? 0;
  const traffic = telemetry?.recent_traffic ?? [];

  return (
    <div className="stack gap-16">
      <div className="grid grid-4">
        <StatCard
          label="External AI calls"
          value={externalCalls}
          icon={<ShieldX size={14} />}
          tone={externalCalls === 0 ? 'success' : 'danger'}
          footnote={externalCalls === 0 ? 'None since start-up' : 'Investigate immediately'}
        />
        <StatCard
          label="Blocked egress attempts"
          value={telemetry?.wan_egress_blocked ?? 0}
          icon={<Radar size={14} />}
          tone="brand"
          footnote="Refused at the socket layer"
        />
        <StatCard
          label="Local requests served"
          value={telemetry?.total_local_requests ?? 0}
          icon={<Activity size={14} />}
          tone="violet"
          footnote="Loopback traffic only"
        />
        <StatCard
          label="Interfaces monitored"
          value={telemetry?.interfaces?.length ?? 0}
          icon={<EthernetPort size={14} />}
          tone="neutral"
          footnote="Scanned every 2 seconds"
        />
      </div>

      <Card>
        <CardHead
          icon={<Radar size={16} />}
          title="Live network telemetry"
          subtitle="Socket-level evidence that no traffic leaves this host"
          actions={
            <>
              <span className="text-xs muted">
                {failed ? 'No data' : `Updated ${formatTime(lastUpdate)}`}
              </span>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => setLive((value) => !value)}
              >
                {live ? <Pause size={13} /> : <Play size={13} />}
                {live ? 'Pause' : 'Resume'}
              </button>
            </>
          }
        />

        <CardBody className="stack gap-18">
          {telemetry?.integrity_hash && (
            <div className="panel row gap-10">
              <Fingerprint size={16} className="muted shrink-0" />
              <div className="grow" style={{ minWidth: 0 }}>
                <p className="text-xs muted">Telemetry integrity seal</p>
                <p className="text-sm mono truncate strong" title={telemetry.integrity_hash}>
                  {telemetry.integrity_hash}
                </p>
              </div>
              <span className="badge badge-success shrink-0">Verified</span>
            </div>
          )}

          <div className="grid grid-2">
            <div>
              <p className="eyebrow" style={{ marginBottom: 8 }}>
                Listening ports
              </p>
              {telemetry?.active_listening_ports?.length ? (
                <div className="stack gap-6">
                  {telemetry.active_listening_ports.map((port, index) => (
                    <div key={`${port.port}-${port.service}-${index}`} className="panel row-between">
                      <span className="truncate">
                        <span className="text-sm mono strong">:{port.port}</span>
                        <span className="text-xs muted" style={{ display: 'block' }}>
                          {port.service} · {port.binding}
                        </span>
                      </span>
                      <span
                        className={`badge badge-${port.scope === 'loopback' ? 'success' : 'warning'} shrink-0`}
                      >
                        {port.scope}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm muted">No listening ports reported.</p>
              )}
            </div>

            <div>
              <p className="eyebrow" style={{ marginBottom: 8 }}>
                Interfaces
              </p>
              {telemetry?.interfaces?.length ? (
                <div className="stack gap-6">
                  {telemetry.interfaces.map((iface, index) => (
                    <div key={`${iface.name}-${iface.ip}-${index}`} className="panel row-between">
                      <span className="truncate">
                        <span className="text-sm strong">{iface.name}</span>
                        <span className="text-xs mono muted" style={{ display: 'block' }}>
                          {iface.ip} · {iface.type}
                        </span>
                      </span>
                      <span
                        className={`badge badge-${iface.egress_allowed ? 'warning' : 'success'} shrink-0`}
                      >
                        {iface.egress_allowed ? 'Egress allowed' : 'Egress blocked'}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm muted">No interfaces reported.</p>
              )}
            </div>
          </div>

          <div>
            <p className="eyebrow" style={{ marginBottom: 8 }}>
              Recent connections
            </p>
            {traffic.length === 0 ? (
              <EmptyState
                icon={<Radar size={20} />}
                title="No connection events"
                text="Every socket the process opens is listed here. An empty list is the expected steady state on an air-gapped host."
              />
            ) : (
              <div className="table-wrap card-scroll">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Time</th>
                      <th>Protocol</th>
                      <th>Source</th>
                      <th>Destination</th>
                      <th>Process</th>
                      <th>Scope</th>
                    </tr>
                  </thead>
                  <tbody>
                    {traffic.map((event, index) => (
                      <tr key={`${event.id}-${index}`}>
                        <td className="mono text-xs muted">{formatTime(event.timestamp)}</td>
                        <td className="mono text-xs">{event.protocol}</td>
                        <td className="mono text-xs">{event.source}</td>
                        <td className="mono text-xs">{event.destination}</td>
                        <td className="text-xs truncate">{event.process}</td>
                        <td>
                          <span
                            className={`badge badge-${event.is_external ? 'danger' : 'success'}`}
                          >
                            {event.is_external ? 'External' : 'Local'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </CardBody>
      </Card>
    </div>
  );
};
