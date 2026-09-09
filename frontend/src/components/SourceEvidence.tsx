import React from 'react';
import { BookOpen, FileText } from 'lucide-react';
import { Card, CardBody, CardHead, EmptyState } from '../ui/primitives';
import { formatPercent } from '../lib/format';
import type { SourceReference } from '../types/api';

/** The retriever has used a few field spellings over time; accept them all. */
function readSource(source: SourceReference) {
  const record = source as Record<string, unknown>;
  return {
    document: (source.document ?? record.source ?? 'Local reference') as string,
    page: (source.page ?? record.page_number ?? null) as number | null,
    score: (typeof source.score === 'number'
      ? source.score
      : typeof record.relevance === 'number'
        ? record.relevance
        : null) as number | null,
    content: (source.content ?? record.text ?? record.snippet ?? '') as string,
  };
}

export const SourceEvidence: React.FC<{ sources: SourceReference[] }> = ({ sources }) => (
  <Card>
    <CardHead
      icon={<BookOpen size={16} />}
      title="Sources"
      subtitle={sources.length ? `${sources.length} passages retrieved from the local index` : undefined}
    />
    <CardBody>
      {sources.length === 0 ? (
        <EmptyState
          icon={<BookOpen size={20} />}
          title="No passages retrieved"
          text="When the agent consults the knowledge base, the exact passages it relied on are listed here with their similarity scores."
        />
      ) : (
        <div className="stack gap-10">
          {sources.map((source, index) => {
            const item = readSource(source);
            return (
              <div key={index} className="panel">
                <div className="row-between" style={{ marginBottom: 6 }}>
                  <span className="row gap-6 truncate">
                    <FileText size={13} className="muted shrink-0" />
                    <span className="text-sm strong truncate" style={{ fontWeight: 550 }}>
                      {item.document}
                    </span>
                    {item.page !== null && (
                      <span className="text-xs mono faint shrink-0">p.{item.page}</span>
                    )}
                  </span>
                  {item.score !== null && (
                    <span className="badge badge-brand badge-square shrink-0">
                      {formatPercent(item.score, 1)} match
                    </span>
                  )}
                </div>
                {item.content && (
                  <p className="text-sm" style={{ color: 'var(--text)' }}>
                    {item.content}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      )}
    </CardBody>
  </Card>
);
