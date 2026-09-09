import React from 'react';
import {
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  FileSearch,
  CheckCheck,
  AlertCircle,
} from 'lucide-react';
import { VerificationSummary, FactClaimVerification } from '../types/api';

interface VerificationPanelProps {
  verification: VerificationSummary | null;
}

export const VerificationPanel: React.FC<VerificationPanelProps> = ({ verification }) => {
  if (!verification) {
    return (
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <ShieldCheck size={14} color="#10b981" />
            <span>Fact & Physics Verifier Engine</span>
          </div>
        </div>
        <div style={{ textAlign: 'center', padding: '24px 20px', color: 'var(--text-muted)' }}>
          <FileSearch size={24} style={{ opacity: 0.3, marginBottom: '6px' }} />
          <div style={{ fontSize: '12px' }}>Verifier results will appear upon step completion.</div>
        </div>
      </div>
    );
  }

  const claims = verification.claims || [];
  const supported = claims.filter((c) => c.status === 'SUPPORTED');
  const needsReview = claims.filter((c) => c.status === 'NEEDS REVIEW' || c.status === ('NEEDS_REVIEW' as any));
  const unsupported = claims.filter((c) => c.status === 'UNSUPPORTED');

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">
          <ShieldCheck size={14} color="#10b981" />
          <span>Fact & Physics Verifier Engine</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {verification.is_valid ? (
            <span
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                color: '#10b981',
                fontSize: '11px',
                fontWeight: 700,
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                padding: '2px 8px',
                borderRadius: '4px',
              }}
            >
              <CheckCheck size={12} />
              <span>VALIDATED</span>
            </span>
          ) : (
            <span
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                color: '#f59e0b',
                fontSize: '11px',
                fontWeight: 700,
                backgroundColor: 'rgba(245, 158, 11, 0.1)',
                border: '1px solid rgba(245, 158, 11, 0.3)',
                padding: '2px 8px',
                borderRadius: '4px',
              }}
            >
              <AlertTriangle size={12} />
              <span>REVIEW REQUIRED</span>
            </span>
          )}
        </div>
      </div>

      {/* Verification Summary Counts */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', marginBottom: '14px' }}>
        <div
          style={{
            padding: '8px 10px',
            backgroundColor: 'rgba(16, 185, 129, 0.08)',
            border: '1px solid rgba(16, 185, 129, 0.25)',
            borderRadius: '4px',
          }}
        >
          <div style={{ fontSize: '10px', color: '#34d399', textTransform: 'uppercase', fontWeight: 600 }}>
            Supported Claims
          </div>
          <div style={{ fontSize: '16px', fontWeight: 700, color: '#34d399', marginTop: '2px' }}>
            {supported.length}
          </div>
        </div>

        <div
          style={{
            padding: '8px 10px',
            backgroundColor: 'rgba(245, 158, 11, 0.08)',
            border: '1px solid rgba(245, 158, 11, 0.25)',
            borderRadius: '4px',
          }}
        >
          <div style={{ fontSize: '10px', color: '#fbbf24', textTransform: 'uppercase', fontWeight: 600 }}>
            Needs Review
          </div>
          <div style={{ fontSize: '16px', fontWeight: 700, color: '#fbbf24', marginTop: '2px' }}>
            {needsReview.length}
          </div>
        </div>

        <div
          style={{
            padding: '8px 10px',
            backgroundColor: 'rgba(239, 68, 68, 0.08)',
            border: '1px solid rgba(239, 68, 68, 0.25)',
            borderRadius: '4px',
          }}
        >
          <div style={{ fontSize: '10px', color: '#f87171', textTransform: 'uppercase', fontWeight: 600 }}>
            Unsupported
          </div>
          <div style={{ fontSize: '16px', fontWeight: 700, color: '#f87171', marginTop: '2px' }}>
            {unsupported.length}
          </div>
        </div>
      </div>

      {/* Verified Claims List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '12px' }}>
        {claims.length > 0 ? (
          claims.map((claim: FactClaimVerification, idx: number) => {
            const isSupp = claim.status === 'SUPPORTED';
            const isRev = claim.status === 'NEEDS REVIEW' || claim.status === ('NEEDS_REVIEW' as any);
            const isUnsupp = claim.status === 'UNSUPPORTED';

            const borderColor = isSupp ? 'rgba(16, 185, 129, 0.3)' : isRev ? 'rgba(245, 158, 11, 0.3)' : 'rgba(239, 68, 68, 0.3)';
            const bgColor = isSupp ? 'rgba(16, 185, 129, 0.04)' : isRev ? 'rgba(245, 158, 11, 0.04)' : 'rgba(239, 68, 68, 0.04)';

            return (
              <div
                key={idx}
                style={{
                  padding: '10px 12px',
                  backgroundColor: bgColor,
                  border: `1px solid ${borderColor}`,
                  borderRadius: '4px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '8px', marginBottom: '4px' }}>
                  <div style={{ fontSize: '12.5px', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {claim.claim}
                  </div>
                  <div style={{ flexShrink: 0 }}>
                    {isSupp && (
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '10px', fontWeight: 700, color: '#10b981', backgroundColor: 'rgba(16, 185, 129, 0.15)', padding: '2px 6px', borderRadius: '3px' }}>
                        <CheckCircle2 size={11} />
                        <span>SUPPORTED</span>
                      </span>
                    )}
                    {isRev && (
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '10px', fontWeight: 700, color: '#f59e0b', backgroundColor: 'rgba(245, 158, 11, 0.15)', padding: '2px 6px', borderRadius: '3px' }}>
                        <AlertTriangle size={11} />
                        <span>NEEDS REVIEW</span>
                      </span>
                    )}
                    {isUnsupp && (
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '10px', fontWeight: 700, color: '#ef4444', backgroundColor: 'rgba(239, 68, 68, 0.15)', padding: '2px 6px', borderRadius: '3px' }}>
                        <XCircle size={11} />
                        <span>UNSUPPORTED</span>
                      </span>
                    )}
                  </div>
                </div>

                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', fontSize: '11px', color: 'var(--text-secondary)' }}>
                  {claim.source_document && (
                    <div>
                      Source: <strong style={{ color: 'var(--color-brand-light)' }}>{claim.source_document}</strong>
                      {claim.page && ` (p. ${claim.page})`}
                    </div>
                  )}
                  {claim.confidence !== undefined && (
                    <div style={{ fontFamily: 'var(--font-mono)' }}>
                      Confidence: {(claim.confidence * 100).toFixed(0)}%
                    </div>
                  )}
                </div>

                {claim.evidence && (
                  <div style={{ marginTop: '6px', fontSize: '11px', color: 'var(--text-muted)', fontStyle: 'italic', borderTop: '1px dashed var(--border-subtle)', paddingTop: '4px' }}>
                    Evidence: &ldquo;{claim.evidence}&rdquo;
                  </div>
                )}
              </div>
            );
          })
        ) : (
          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            No individual claims audited.
          </div>
        )}
      </div>

      {/* Physics / Calculation Checks */}
      {verification.calculation_valid !== undefined && verification.calculation_valid !== null && (
        <div
          style={{
            padding: '8px 10px',
            backgroundColor: '#070b14',
            border: '1px solid var(--border-subtle)',
            borderRadius: '4px',
            fontSize: '11.5px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '10px',
          }}
        >
          <span style={{ color: 'var(--text-secondary)' }}>
            Python Sandbox Physics & Thermodynamic Bounds Check:
          </span>
          <span style={{ color: verification.calculation_valid ? '#10b981' : '#ef4444', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
            {verification.calculation_valid ? 'PASS (0% ≤ η ≤ 100%)' : 'OUT OF BOUNDS'}
          </span>
        </div>
      )}

      {/* Mandatory Human Review Stipulation */}
      <div
        style={{
          padding: '8px 12px',
          backgroundColor: 'rgba(245, 158, 11, 0.06)',
          border: '1px solid rgba(245, 158, 11, 0.2)',
          borderRadius: '4px',
          fontSize: '11px',
          color: '#fbbf24',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
        }}
      >
        <AlertCircle size={13} />
        <span>
          <strong>Human Review Notice:</strong> AI-assisted draft — final engineering sign-off requires human confirmation.
        </span>
      </div>
    </div>
  );
};
