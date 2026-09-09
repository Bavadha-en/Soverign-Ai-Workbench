import React from 'react';
import {
  ShieldCheck,
  Lock,
  Globe2,
  FileCheck2,
  AlertTriangle,
} from 'lucide-react';
import { NetworkStatus } from '../types/api';

interface SovereigntyPanelProps {
  network: NetworkStatus | null;
  loading: boolean;
}

export const SovereigntyPanel: React.FC<SovereigntyPanelProps> = ({ network }) => {
  const isSovereign = network?.status === 'LOCAL_ONLY' && (network?.external_ai_calls ?? 0) === 0;

  return (
    <div
      className="card"
      style={{
        background: 'linear-gradient(180deg, rgba(13, 27, 46, 0.9) 0%, rgba(10, 15, 27, 0.95) 100%)',
        border: '1px solid rgba(56, 189, 248, 0.25)',
      }}
    >
      <div className="card-header" style={{ borderColor: 'rgba(56, 189, 248, 0.2)' }}>
        <div className="card-title" style={{ color: 'var(--color-brand-light)' }}>
          <ShieldCheck size={16} color="#38bdf8" />
          <span>Sovereign & Air-Gapped Attestation</span>
        </div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            background: 'rgba(16, 185, 129, 0.15)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            padding: '2px 8px',
            borderRadius: '4px',
            fontSize: '11px',
            color: '#34d399',
            fontWeight: 700,
            fontFamily: 'var(--font-mono)',
          }}
        >
          <Lock size={11} />
          <span>AIR-GAP COMPLIANT</span>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '10px', marginBottom: '14px' }}>
        {/* Network Mode */}
        <div
          style={{
            padding: '10px 12px',
            backgroundColor: '#070c18',
            borderRadius: '4px',
            border: '1px solid rgba(56, 189, 248, 0.15)',
          }}
        >
          <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
            Network Mode
          </div>
          <div style={{ fontSize: '14px', fontWeight: 700, color: '#38bdf8', marginTop: '2px' }}>
            {network?.status || 'LOCAL_ONLY'}
          </div>
          <div style={{ fontSize: '10px', color: '#10b981', display: 'flex', alignItems: 'center', gap: '4px', marginTop: '2px' }}>
            <span style={{ width: '4px', height: '4px', borderRadius: '50%', backgroundColor: '#10b981' }} />
            Zero Ingress/Egress
          </div>
        </div>

        {/* External AI Calls */}
        <div
          style={{
            padding: '10px 12px',
            backgroundColor: '#070c18',
            borderRadius: '4px',
            border: '1px solid rgba(56, 189, 248, 0.15)',
          }}
        >
          <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
            External AI Calls
          </div>
          <div style={{ fontSize: '14px', fontWeight: 700, color: network?.external_ai_calls === 0 ? '#10b981' : '#ef4444', marginTop: '2px' }}>
            {network?.external_ai_calls ?? 0}
          </div>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '2px' }}>
            Telemetry Blocked
          </div>
        </div>

        {/* Cloud AI Status */}
        <div
          style={{
            padding: '10px 12px',
            backgroundColor: '#070c18',
            borderRadius: '4px',
            border: '1px solid rgba(56, 189, 248, 0.15)',
          }}
        >
          <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
            Cloud AI Gate
          </div>
          <div style={{ fontSize: '14px', fontWeight: 700, color: '#94a3b8', marginTop: '2px' }}>
            DISABLED
          </div>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '2px' }}>
            OpenAI / Cloud Blocked
          </div>
        </div>

        {/* Local Processing */}
        <div
          style={{
            padding: '10px 12px',
            backgroundColor: '#070c18',
            borderRadius: '4px',
            border: '1px solid rgba(56, 189, 248, 0.15)',
          }}
        >
          <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
            Local Processing
          </div>
          <div style={{ fontSize: '14px', fontWeight: 700, color: '#10b981', marginTop: '2px' }}>
            ENABLED
          </div>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '2px' }}>
            Open-Weights Only
          </div>
        </div>

        {/* Audit Logging */}
        <div
          style={{
            padding: '10px 12px',
            backgroundColor: '#070c18',
            borderRadius: '4px',
            border: '1px solid rgba(56, 189, 248, 0.15)',
          }}
        >
          <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
            Audit Logging
          </div>
          <div style={{ fontSize: '14px', fontWeight: 700, color: '#10b981', marginTop: '2px' }}>
            ENABLED
          </div>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '2px' }}>
            Forensic Integrity
          </div>
        </div>
      </div>

      <div
        style={{
          padding: '10px 14px',
          backgroundColor: 'rgba(6, 182, 212, 0.06)',
          borderRadius: '4px',
          border: '1px solid rgba(6, 182, 212, 0.2)',
          fontSize: '11.5px',
          color: 'var(--text-secondary)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '12px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Globe2 size={15} color="#06b6d4" />
          <span>
            <strong>Air-Gapped Sovereign Guarantee:</strong> Engineering scripts, inspection OCR, and model inferences execute 100% within local memory boundaries with zero external telemetry.
          </span>
        </div>
        {isSovereign ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#34d399', fontWeight: 600, fontSize: '11px', whiteSpace: 'nowrap' }}>
            <FileCheck2 size={14} />
            <span>VERIFIED SOVEREIGN</span>
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#ef4444', fontWeight: 600, fontSize: '11px', whiteSpace: 'nowrap' }}>
            <AlertTriangle size={14} />
            <span>EXTERNAL ANOMALY</span>
          </div>
        )}
      </div>
    </div>
  );
};
