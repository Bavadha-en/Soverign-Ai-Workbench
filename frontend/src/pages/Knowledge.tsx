import React, { useState } from 'react';
import {
  Database,
  Search,
  RefreshCw,
  FileText,
  Bookmark,
  CheckCircle2,
  AlertCircle,
  Layers,
} from 'lucide-react';
import { api } from '../services/api';
import { KnowledgeSearchResultItem, KnowledgeIngestResponse } from '../types/api';

export const Knowledge: React.FC = () => {
  const [query, setQuery] = useState<string>('procedure for replacing a corroded valve');
  const [topK, setTopK] = useState<number>(5);
  const [results, setResults] = useState<KnowledgeSearchResultItem[]>([]);
  const [isSearching, setIsSearching] = useState<boolean>(false);
  const [isIngesting, setIsIngesting] = useState<boolean>(false);
  const [ingestStatus, setIngestStatus] = useState<KnowledgeIngestResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setIsSearching(true);
    setErrorMsg(null);

    try {
      const resp = await api.searchKnowledge(query.trim(), topK);
      setResults(resp.results || []);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setErrorMsg(`Search failed: ${msg}`);
    } finally {
      setIsSearching(false);
    }
  };

  const handleIngest = async () => {
    setIsIngesting(true);
    setErrorMsg(null);
    setIngestStatus(null);

    try {
      const resp = await api.ingestKnowledge('knowledge_base', true);
      setIngestStatus(resp);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setErrorMsg(`Knowledge base indexing error: ${msg}`);
    } finally {
      setIsIngesting(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
      {/* Header */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <Database size={15} color="#38bdf8" />
            <span>Local On-Premise Vector Store & SOP Knowledge Base</span>
          </div>
          <button
            onClick={handleIngest}
            disabled={isIngesting}
            className="btn btn-secondary btn-sm"
            style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <RefreshCw size={12} className={isIngesting ? 'spin' : ''} />
            <span>{isIngesting ? 'Re-Indexing Chunks...' : 'Re-Index Knowledge Directory'}</span>
          </button>
        </div>

        <p style={{ fontSize: '12.5px', color: 'var(--text-secondary)', marginBottom: '14px' }}>
          ConfigIQ indexes engineering SOPs, maintenance manuals, and technical specifications locally into an offline embedding store using <strong style={{ color: 'var(--color-brand-light)' }}>nomic-embed-text:latest</strong>. All queries execute offline with cosine similarity.
        </p>

        {ingestStatus && (
          <div
            style={{
              padding: '10px 14px',
              backgroundColor: 'rgba(16, 185, 129, 0.08)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              borderRadius: '4px',
              fontSize: '12px',
              color: '#34d399',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '14px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <CheckCircle2 size={15} />
              <span>{ingestStatus.message}</span>
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px' }}>
              {ingestStatus.documents_indexed} Docs / {ingestStatus.chunks_created} Chunks
            </div>
          </div>
        )}

        {/* Search Query Form */}
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <Search size={14} style={{ position: 'absolute', left: '12px', top: '11px', color: 'var(--text-muted)' }} />
            <input
              type="text"
              className="input-text"
              style={{ paddingLeft: '34px' }}
              placeholder="Search local SOP clauses, equipment specifications, maintenance procedures..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', whiteSpace: 'nowrap', fontSize: '12px', color: 'var(--text-muted)' }}>
            <span>Top K:</span>
            <select
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              style={{
                backgroundColor: 'var(--bg-panel-elevated)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '4px',
                padding: '6px 8px',
                fontSize: '12px',
              }}
            >
              <option value={3}>3</option>
              <option value={5}>5</option>
              <option value={10}>10</option>
            </select>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={isSearching}
            style={{ minWidth: '110px' }}
          >
            {isSearching ? (
              <>
                <RefreshCw size={13} className="spin" />
                <span>Searching...</span>
              </>
            ) : (
              <>
                <Search size={13} />
                <span>RAG Query</span>
              </>
            )}
          </button>
        </form>
      </div>

      {errorMsg && (
        <div
          style={{
            padding: '10px 14px',
            backgroundColor: 'var(--color-danger-bg)',
            border: '1px solid var(--color-danger)',
            borderRadius: '4px',
            fontSize: '12px',
            color: '#f87171',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <AlertCircle size={15} />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Search Results List */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <Bookmark size={14} color="#38bdf8" />
            <span>Retrieved Chunks & Provenance ({results.length})</span>
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            Vector Similarity Ranking
          </div>
        </div>

        {results.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {results.map((item, idx) => (
              <div
                key={idx}
                style={{
                  padding: '12px 14px',
                  backgroundColor: '#070b14',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '6px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <FileText size={14} color="#38bdf8" />
                    <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {item.document}
                    </span>
                    {item.page && (
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                        [Page {item.page}]
                      </span>
                    )}
                  </div>

                  <div
                    style={{
                      fontSize: '11px',
                      fontFamily: 'var(--font-mono)',
                      fontWeight: 700,
                      color: '#38bdf8',
                      backgroundColor: 'rgba(56, 189, 248, 0.1)',
                      padding: '2px 8px',
                      borderRadius: '4px',
                    }}
                  >
                    Cosine: {(item.score * 100).toFixed(1)}%
                  </div>
                </div>

                <div
                  style={{
                    fontSize: '12px',
                    color: 'var(--text-secondary)',
                    lineHeight: '1.6',
                    backgroundColor: 'rgba(0, 0, 0, 0.3)',
                    padding: '10px 12px',
                    borderRadius: '4px',
                  }}
                >
                  {item.content}
                </div>

                {item.metadata && Object.keys(item.metadata).length > 0 && (
                  <div style={{ marginTop: '8px', display: 'flex', gap: '12px', fontSize: '10.5px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                    {Object.entries(item.metadata).map(([k, v]) => (
                      <span key={k}>
                        {k}: <strong style={{ color: 'var(--text-secondary)' }}>{String(v)}</strong>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '36px 20px', color: 'var(--text-muted)' }}>
            <Layers size={28} style={{ opacity: 0.3, marginBottom: '8px' }} />
            <div style={{ fontSize: '13px' }}>Perform a RAG search above to inspect vector embeddings.</div>
          </div>
        )}
      </div>
    </div>
  );
};
