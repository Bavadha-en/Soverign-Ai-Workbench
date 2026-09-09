import React from 'react';
import {
  Server,
  Cpu,
  Brain,
  Eye,
  Hash,
  Activity,
  CheckCircle2,
  XCircle,
  Clock,
} from 'lucide-react';
import { HealthResponse } from '../types/api';

interface SystemStatusProps {
  health: HealthResponse | null;
  loading?: boolean;
}

export const SystemStatus: React.FC<SystemStatusProps> = ({ health }) => {
  const models = health?.models || {};
  const isBackendHealthy = health?.status === 'healthy';
  const isOllamaAvailable = health?.ollama === 'available';

  const modelSpecs = [
    {
      key: 'general',
      name: 'General LLM',
      modelId: 'llama3:latest',
      role: 'Reasoning & Synthesis',
      icon: <Brain size={14} color="#38bdf8" />,
      ready: models['general'] ?? isOllamaAvailable,
    },
    {
      key: 'coding',
      name: 'Coding LLM',
      modelId: 'qwen2.5-coder:7b',
      role: 'Code & Sandboxed Scripts',
      icon: <Cpu size={14} color="#818cf8" />,
      ready: models['coding'] ?? isOllamaAvailable,
    },
    {
      key: 'heavy_coding',
      name: 'Heavy Coding LLM',
      modelId: 'qwen2.5-coder:14b',
      role: 'Physics & Simulation',
      icon: <Cpu size={14} color="#c084fc" />,
      ready: models['heavy_coding'] ?? isOllamaAvailable,
    },
    {
      key: 'vision',
      name: 'Vision Model',
      modelId: 'moondream:latest',
      role: 'Industrial Anomaly & Defect',
      icon: <Eye size={14} color="#34d399" />,
      ready: models['vision'] ?? isOllamaAvailable,
    },
    {
      key: 'embedding',
      name: 'Embeddings Engine',
      modelId: 'nomic-embed-text:latest',
      role: 'Local Vector RAG',
      icon: <Hash size={14} color="#fbbf24" />,
      ready: models['embedding'] ?? isOllamaAvailable,
    },
  ];

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">
          <Server size={15} color="#38bdf8" />
          <span>System & Engine Status</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: 'var(--text-muted)' }}>
          <Clock size={12} />
          <span>{health?.timestamp ? new Date(health.timestamp).toLocaleTimeString() : 'N/A'}</span>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: '10px', marginBottom: '16px' }}>
        {/* Backend status */}
        <div
          style={{
            padding: '10px 12px',
            backgroundColor: 'var(--bg-panel-elevated)',
            borderRadius: '4px',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              FastAPI Core
            </span>
            {isBackendHealthy ? (
              <CheckCircle2 size={13} color="#10b981" />
            ) : (
              <XCircle size={13} color="#ef4444" />
            )}
          </div>
          <div style={{ fontSize: '14px', fontWeight: 700, color: isBackendHealthy ? '#10b981' : '#ef4444' }}>
            {isBackendHealthy ? 'ONLINE' : 'DISCONNECTED'}
          </div>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '2px' }}>
            {health?.environment || 'Air-Gapped Node'}
          </div>
        </div>

        {/* Ollama runtime */}
        <div
          style={{
            padding: '10px 12px',
            backgroundColor: 'var(--bg-panel-elevated)',
            borderRadius: '4px',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Ollama Host
            </span>
            {isOllamaAvailable ? (
              <CheckCircle2 size={13} color="#10b981" />
            ) : (
              <Activity size={13} color="#f59e0b" />
            )}
          </div>
          <div style={{ fontSize: '14px', fontWeight: 700, color: isOllamaAvailable ? '#10b981' : '#f59e0b' }}>
            {isOllamaAvailable ? 'AVAILABLE' : 'STANDBY / MOCK'}
          </div>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '2px' }}>
            Local Open-Weight Runtime
          </div>
        </div>

        {/* Network Mode */}
        <div
          style={{
            padding: '10px 12px',
            backgroundColor: 'rgba(16, 185, 129, 0.06)',
            borderRadius: '4px',
            border: '1px solid rgba(16, 185, 129, 0.25)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
            <span style={{ fontSize: '11px', color: '#34d399', textTransform: 'uppercase', fontWeight: 600 }}>
              Network Isolation
            </span>
            <CheckCircle2 size={13} color="#10b981" />
          </div>
          <div style={{ fontSize: '14px', fontWeight: 700, color: '#34d399' }}>
            LOCAL_ONLY
          </div>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '2px' }}>
            0 External AI Telemetry
          </div>
        </div>
      </div>

      {/* Models Status Grid */}
      <div style={{ fontSize: '11px', fontWeight: 700, letterSpacing: '0.05em', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '8px' }}>
        Open-Weight Model Registry
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '8px' }}>
        {modelSpecs.map((spec) => (
          <div
            key={spec.key}
            style={{
              padding: '8px 10px',
              backgroundColor: '#070b14',
              borderRadius: '4px',
              border: '1px solid var(--border-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {spec.icon}
              <div>
                <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {spec.modelId}
                </div>
                <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                  {spec.name} • {spec.role}
                </div>
              </div>
            </div>

            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                fontSize: '10px',
                fontWeight: 700,
                color: spec.ready ? '#10b981' : '#94a3b8',
                backgroundColor: spec.ready ? 'rgba(16, 185, 129, 0.1)' : 'rgba(148, 163, 184, 0.1)',
                padding: '2px 6px',
                borderRadius: '3px',
              }}
            >
              <span
                style={{
                  width: '5px',
                  height: '5px',
                  borderRadius: '50%',
                  backgroundColor: spec.ready ? '#10b981' : '#94a3b8',
                }}
              />
              {spec.ready ? 'READY' : 'OFFLINE'}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
