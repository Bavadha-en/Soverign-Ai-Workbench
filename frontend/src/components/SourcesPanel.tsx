import React from 'react';
import { Database, FileText, Bookmark } from 'lucide-react';
import { SourceReference } from '../types/api';

interface SourcesPanelProps {
  sources: SourceReference[];
}

export const SourcesPanel: React.FC<SourcesPanelProps> = ({ sources }) => {
  if (!sources || sources.length === 0) {
    return (
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <Database size={14} color="#38bdf8" />
            <span>Retrieved SOP & Knowledge Provenance</span>
          </div>
        </div>
        <div style={{ textAlign: 'center', padding: '24px 20px', color: 'var(--text-muted)' }}>
          <Bookmark size={24} style={{ opacity: 0.3, marginBottom: '6px' }} />
          <div style={{ fontSize: '12px' }}>No local knowledge chunks retrieved for this task.</div>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">
          <Database size={14} color="#38bdf8" />
          <span>Retrieved SOP & Knowledge Provenance ({sources.length})</span>
        </div>
        <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
          Local Vector Index
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {sources.map((src: SourceReference, idx: number) => {
          const docName = src.document || (src as any).source || 'Technical Reference';
          const page = src.page !== undefined && src.page !== null ? src.page : (src as any).page_number;
          const rawScore = typeof src.score === 'number' ? src.score : typeof (src as any).relevance === 'number' ? (src as any).relevance : null;
          const score = rawScore !== null ? (rawScore * 100).toFixed(1) : null;
          const content = src.content || (src as any).text || (src as any).snippet || '';

          return (
            <div
              key={idx}
              style={{
                padding: '10px 12px',
                backgroundColor: '#070b14',
                border: '1px solid var(--border-subtle)',
                borderRadius: '4px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <FileText size={13} color="#38bdf8" />
                  <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {docName}
                  </span>
                  {page && (
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                      [Page {page}]
                    </span>
                  )}
                </div>

                {score !== null && (
                  <div
                    style={{
                      fontSize: '10.5px',
                      fontFamily: 'var(--font-mono)',
                      color: '#38bdf8',
                      backgroundColor: 'rgba(56, 189, 248, 0.1)',
                      padding: '2px 6px',
                      borderRadius: '3px',
                      fontWeight: 600,
                    }}
                  >
                    Cosine: {score}%
                  </div>
                )}
              </div>

              {content && (
                <div
                  style={{
                    fontSize: '11.5px',
                    color: 'var(--text-secondary)',
                    backgroundColor: 'rgba(0, 0, 0, 0.25)',
                    padding: '8px',
                    borderRadius: '3px',
                    fontFamily: 'inherit',
                    lineHeight: '1.5',
                  }}
                >
                  {content}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
