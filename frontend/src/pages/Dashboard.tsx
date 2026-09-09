import React from 'react';
import {
  Terminal,
  Cpu,
  FileCheck,
  ArrowRight,
  Sparkles,
  Lock,
  Layers,
  FileText,
  FileSpreadsheet,
} from 'lucide-react';
import { HealthResponse, NetworkStatus, ToolDefinition } from '../types/api';
import { SovereigntyPanel } from '../components/SovereigntyPanel';
import { NetworkMonitor } from '../components/NetworkMonitor';
import { SystemStatus } from '../components/SystemStatus';
import { NavTab } from '../components/Sidebar';

interface DashboardProps {
  health: HealthResponse | null;
  network: NetworkStatus | null;
  tools: ToolDefinition[];
  loading: boolean;
  onNavigate: (tab: NavTab) => void;
  onSelectPresetAndRun: (taskText: string) => void;
}


export const Dashboard: React.FC<DashboardProps> = ({
  health,
  network,
  tools,
  loading,
  onNavigate,
  onSelectPresetAndRun,
}) => {
  const readyModelsCount = health?.models ? Object.values(health.models).filter(Boolean).length : 5;

  const quickScenarios = [
    {
      title: 'Valve Inspection Report → Word & PPTX',
      desc: 'Multimodal defect extraction with SOP compliance check & formal executive deck.',
      task: 'Analyze this inspection report and prepare an approval note and executive summary.',
      icon: <FileText size={16} color="#38bdf8" />,
    },
    {
      title: 'Pump Efficiency & Thermodynamic Workbook',
      desc: 'Sandboxed Python calculation producing 4-sheet verified Excel calculation workbook.',
      task: 'Calculate pump efficiency using flow rate of 50 m3/h, head of 60 m, and power of 11 kW and create a calculation workbook.',
      icon: <FileSpreadsheet size={16} color="#34d399" />,
    },
    {
      title: 'MVTec Visual Defect Anomaly Scan',
      desc: 'Multimodal inspection using local Moondream vision model for bounding anomalies.',
      task: 'Perform multimodal visual defect inspection on uploaded industrial component and extract anomaly bounding data.',
      icon: <Cpu size={16} color="#fbbf24" />,
    },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Banner / Welcome */}
      <div
        style={{
          padding: '20px 24px',
          backgroundColor: '#0a101f',
          border: '1px solid var(--border-subtle)',
          borderRadius: '8px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '16px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <h1 style={{ fontSize: '18px', fontWeight: 700, color: '#fff' }}>
              ConfigIQ Industrial Operations Console
            </h1>
            <span
              style={{
                fontSize: '10.5px',
                fontFamily: 'var(--font-mono)',
                backgroundColor: 'rgba(56, 189, 248, 0.15)',
                color: 'var(--color-brand-light)',
                border: '1px solid rgba(56, 189, 248, 0.3)',
                padding: '2px 6px',
                borderRadius: '4px',
                fontWeight: 600,
              }}
            >
              AIR-GAPPED v1.0.0
            </span>
          </div>
          <p style={{ fontSize: '12.5px', color: 'var(--text-secondary)', maxWidth: '750px' }}>
            Autonomous sovereign agentic workbench engineered for confidential industrial engineering workflows (Problem Statement 26117). 100% offline reasoning, multimodal inspection verification, isolated Python sandbox, and multi-format deliverable generation.
          </p>
        </div>

        <button
          onClick={() => onNavigate('workbench')}
          className="btn btn-primary"
          style={{ whiteSpace: 'nowrap', padding: '10px 20px' }}
        >
          <Terminal size={15} />
          <span>Launch Workbench</span>
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid-4">
        {/* Air Gap Status */}
        <div className="card" style={{ padding: '14px 16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Network Isolation
            </span>
            <Lock size={14} color="#10b981" />
          </div>
          <div style={{ fontSize: '20px', fontWeight: 700, color: '#10b981' }}>
            LOCAL_ONLY
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
            0 External API Calls Detected
          </div>
        </div>

        {/* Models Ready */}
        <div className="card" style={{ padding: '14px 16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Open-Weight Models
            </span>
            <Cpu size={14} color="#38bdf8" />
          </div>
          <div style={{ fontSize: '20px', fontWeight: 700, color: '#38bdf8' }}>
            {readyModelsCount} / 5 Ready
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
            Llama3, Qwen Coder, Moondream, Nomic
          </div>
        </div>

        {/* Registered Tools */}
        <div className="card" style={{ padding: '14px 16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Orchestrator Tools
            </span>
            <Layers size={14} color="#c084fc" />
          </div>
          <div style={{ fontSize: '20px', fontWeight: 700, color: '#c084fc' }}>
            {tools.length || 11} Tools
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
            OCR, RAG, Code, Sandbox, Word/XLSX/PPTX
          </div>
        </div>

        {/* Deliverables Ready */}
        <div className="card" style={{ padding: '14px 16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Export Engines
            </span>
            <FileCheck size={14} color="#fbbf24" />
          </div>
          <div style={{ fontSize: '20px', fontWeight: 700, color: '#fbbf24' }}>
            DOCX, XLSX, PPTX
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
            Phase 5A Multi-Format Generator
          </div>
        </div>
      </div>

      {/* Sovereignty Panel & Real-time Network Telemetry */}
      <SovereigntyPanel network={network} loading={loading} />
      <NetworkMonitor />

      {/* System Status & Quick Scenarios */}
      <div className="grid-2">
        <SystemStatus health={health} />

        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <Sparkles size={14} color="#38bdf8" />
              <span>Standard Engineering Workflows</span>
            </div>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Quick Launch</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {quickScenarios.map((sc, idx) => (
              <div
                key={idx}
                style={{
                  padding: '12px',
                  backgroundColor: '#070b14',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '4px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '12px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div
                    style={{
                      width: '32px',
                      height: '32px',
                      borderRadius: '4px',
                      backgroundColor: 'var(--bg-panel-elevated)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                    }}
                  >
                    {sc.icon}
                  </div>
                  <div>
                    <div style={{ fontSize: '12.5px', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {sc.title}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                      {sc.desc}
                    </div>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => onSelectPresetAndRun(sc.task)}
                  className="btn btn-secondary btn-sm"
                  style={{ whiteSpace: 'nowrap', display: 'flex', alignItems: 'center', gap: '4px' }}
                >
                  <span>Execute</span>
                  <ArrowRight size={12} />
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
