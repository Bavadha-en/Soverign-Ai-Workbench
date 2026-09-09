import React from 'react';
import { AlertTriangle, BadgeCheck, CheckCircle2, ShieldCheck, UserCheck, XCircle } from 'lucide-react';
import { Card, CardBody, CardHead, EmptyState } from '../ui/primitives';
import { formatPercent, normalizeClaimStatus } from '../lib/format';
import type { FactClaimVerification, VerificationSummary } from '../types/api';

const CLAIM_STYLES = {
  SUPPORTED: {
    tone: 'success',
    label: 'Supported',
    icon: <CheckCircle2 size={12} />,
    border: '#a7f3d0',
    background: 'var(--success-50)',
  },
  'NEEDS REVIEW': {
    tone: 'warning',
    label: 'Needs review',
    icon: <AlertTriangle size={12} />,
    border: '#fde68a',
    background: 'var(--warning-50)',
  },
  UNSUPPORTED: {
    tone: 'danger',
    label: 'Unsupported',
    icon: <XCircle size={12} />,
    border: '#fecaca',
    background: 'var(--danger-50)',
  },
} as const;

export const VerificationReport: React.FC<{ verification: VerificationSummary | null }> = ({
  verification,
}) => {
  if (!verification) {
    return (
      <Card>
        <CardHead icon={<ShieldCheck size={16} />} title="Verification" />
        <CardBody>
          <EmptyState
            icon={<ShieldCheck size={20} />}
            title="Not yet verified"
            text="After the agent produces an answer, every claim is checked against retrieved sources and every number against its physical bounds."
          />
        </CardBody>
      </Card>
    );
  }

  const claims = verification.claims ?? [];
  const counts = claims.reduce(
    (acc, claim) => {
      acc[normalizeClaimStatus(claim.status)] += 1;
      return acc;
    },
    { SUPPORTED: 0, 'NEEDS REVIEW': 0, UNSUPPORTED: 0 } as Record<
      keyof typeof CLAIM_STYLES,
      number
    >,
  );

  return (
    <Card>
      <CardHead
        icon={<ShieldCheck size={16} />}
        title="Verification"
        subtitle={`${claims.length} claim${claims.length === 1 ? '' : 's'} checked against retrieved sources`}
        actions={
          verification.is_valid ? (
            <span className="badge badge-success">
              <BadgeCheck size={13} />
              Passed
            </span>
          ) : (
            <span className="badge badge-warning">
              <AlertTriangle size={13} />
              Review required
            </span>
          )
        }
      />

      <CardBody className="stack gap-16">
        <div className="grid grid-3" style={{ gap: 10 }}>
          {(Object.keys(CLAIM_STYLES) as Array<keyof typeof CLAIM_STYLES>).map((key) => {
            const style = CLAIM_STYLES[key];
            return (
              <div
                key={key}
                className="panel"
                style={{ background: style.background, borderColor: style.border }}
              >
                <p className="text-xs" style={{ fontWeight: 600 }}>
                  {style.label}
                </p>
                <p className="stat-value stat-value-sm num" style={{ fontSize: 22 }}>
                  {counts[key]}
                </p>
              </div>
            );
          })}
        </div>

        {claims.length > 0 && (
          <div className="stack gap-8">
            {claims.map((claim: FactClaimVerification, index) => {
              const status = normalizeClaimStatus(claim.status);
              const style = CLAIM_STYLES[status];
              return (
                <div
                  key={index}
                  className="panel"
                  style={{ background: style.background, borderColor: style.border }}
                >
                  <div className="row-top gap-10">
                    <p className="text-sm strong grow" style={{ fontWeight: 550 }}>
                      {claim.claim}
                    </p>
                    <span className={`badge badge-${style.tone} shrink-0`}>
                      {style.icon}
                      {style.label}
                    </span>
                  </div>

                  <div className="row wrap gap-12 text-xs muted" style={{ marginTop: 6 }}>
                    {claim.source_document && (
                      <span>
                        Source: <span className="strong">{claim.source_document}</span>
                        {claim.page ? ` · p.${claim.page}` : ''}
                      </span>
                    )}
                    {typeof claim.confidence === 'number' && (
                      <span className="mono">Confidence {formatPercent(claim.confidence)}</span>
                    )}
                  </div>

                  {claim.evidence && (
                    <p
                      className="text-xs muted"
                      style={{
                        marginTop: 6,
                        paddingTop: 6,
                        borderTop: '1px dashed var(--border-strong)',
                        fontStyle: 'italic',
                      }}
                    >
                      “{claim.evidence}”
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {verification.calculation_valid !== undefined && verification.calculation_valid !== null && (
          <div className="panel row-between">
            <span className="text-sm">Numerical bounds check</span>
            <span
              className={`badge badge-${verification.calculation_valid ? 'success' : 'danger'}`}
            >
              {verification.calculation_valid ? 'Within physical limits' : 'Out of bounds'}
            </span>
          </div>
        )}

        <div className="notice notice-warning">
          <UserCheck size={16} />
          <span>
            <strong>Sign-off required.</strong> This is an AI-assisted draft. A qualified engineer
            must approve it before it is issued.
          </span>
        </div>
      </CardBody>
    </Card>
  );
};
