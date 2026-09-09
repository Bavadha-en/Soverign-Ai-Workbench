import React, { useState } from 'react';
import { Database, FileText, RefreshCw, Search } from 'lucide-react';
import { Card, CardBody, CardHead, EmptyState, PageHeader, Spinner } from '../ui/primitives';
import { useToast } from '../ui/toast';
import { api } from '../services/api';
import { baseName, formatPercent } from '../lib/format';
import type { KnowledgeSearchResultItem } from '../types/api';

/** Absolute host paths make the provenance line unreadable; show the file only. */
function formatMetaValue(key: string, value: unknown): string {
  const text = String(value);
  return key.toLowerCase().includes('path') ? baseName(text) : text;
}

export const Knowledge: React.FC = () => {
  const toast = useToast();
  const [query, setQuery] = useState('procedure for replacing a corroded valve');
  const [topK, setTopK] = useState(5);
  const [results, setResults] = useState<KnowledgeSearchResultItem[] | null>(null);
  const [searching, setSearching] = useState(false);
  const [indexing, setIndexing] = useState(false);

  const search = async (event: React.FormEvent) => {
    event.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) return;

    setSearching(true);
    try {
      const response = await api.searchKnowledge(trimmed, topK);
      setResults(response.results ?? []);
      if (!response.results?.length) toast.info('No passages matched that query');
    } catch (error) {
      toast.error(`Search failed: ${(error as Error).message}`);
      setResults([]);
    } finally {
      setSearching(false);
    }
  };

  const reindex = async () => {
    setIndexing(true);
    try {
      const response = await api.ingestKnowledge('knowledge_base', true);
      toast.success(
        `Indexed ${response.documents_indexed} documents into ${response.chunks_created} chunks`,
      );
    } catch (error) {
      toast.error(`Indexing failed: ${(error as Error).message}`);
    } finally {
      setIndexing(false);
    }
  };

  return (
    <>
      <PageHeader
        title="Knowledge base"
        subtitle="Standard operating procedures, maintenance manuals and inspection guides, embedded locally and searched by meaning rather than keywords."
        actions={
          <button type="button" className="btn btn-secondary" onClick={reindex} disabled={indexing}>
            <RefreshCw size={14} className={indexing ? 'spin' : undefined} />
            {indexing ? 'Re-indexing…' : 'Re-index documents'}
          </button>
        }
      />

      <Card>
        <CardHead
          icon={<Search size={16} />}
          title="Search the index"
          subtitle="Embeddings are produced on this host by nomic-embed-text and ranked by cosine similarity."
        />
        <CardBody>
          <form onSubmit={search} className="row wrap gap-10">
            <div className="input-search">
              <Search size={15} />
              <input
                className="input"
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Describe what you need — clauses, thresholds, procedures…"
                aria-label="Search the knowledge base"
              />
            </div>

            <div className="row gap-6 shrink-0">
              <label className="text-sm muted" htmlFor="top-k">
                Results
              </label>
              <select
                id="top-k"
                className="select"
                style={{ width: 76 }}
                value={topK}
                onChange={(event) => setTopK(Number(event.target.value))}
              >
                <option value={3}>3</option>
                <option value={5}>5</option>
                <option value={10}>10</option>
              </select>
            </div>

            <button type="submit" className="btn btn-primary shrink-0" disabled={searching}>
              {searching ? <Spinner size={14} /> : <Search size={14} />}
              Search
            </button>
          </form>
        </CardBody>
      </Card>

      <Card>
        <CardHead
          icon={<Database size={16} />}
          title="Matching passages"
          subtitle={
            results ? `${results.length} passage${results.length === 1 ? '' : 's'} returned` : undefined
          }
        />
        <CardBody>
          {results === null ? (
            <EmptyState
              icon={<Database size={20} />}
              title="Run a search to inspect the index"
              text="Each result shows the source document, the page it came from and how closely it matched — the same provenance the agent uses when it cites a procedure."
            />
          ) : results.length === 0 ? (
            <EmptyState
              icon={<Search size={20} />}
              title="No passages matched"
              text="Try broader wording, or re-index the knowledge base if documents were added recently."
            />
          ) : (
            <div className="stack gap-10">
              {results.map((item, index) => (
                <article key={index} className="panel">
                  <div className="row-between" style={{ marginBottom: 8 }}>
                    <span className="row gap-8 truncate">
                      <FileText size={14} className="muted shrink-0" />
                      <span className="text-sm strong truncate" style={{ fontWeight: 600 }}>
                        {item.document}
                      </span>
                      {item.page != null && (
                        <span className="text-xs mono faint shrink-0">page {item.page}</span>
                      )}
                    </span>
                    <span className="badge badge-brand badge-square shrink-0">
                      {formatPercent(item.score, 1)} match
                    </span>
                  </div>

                  <p className="text-sm" style={{ color: 'var(--text)' }}>
                    {item.content}
                  </p>

                  {item.metadata && Object.keys(item.metadata).length > 0 && (
                    <div className="row wrap gap-12 text-xs faint" style={{ marginTop: 8 }}>
                      {Object.entries(item.metadata).map(([key, value]) => (
                        <span key={key} className="mono">
                          {key}: <span className="muted">{formatMetaValue(key, value)}</span>
                        </span>
                      ))}
                    </div>
                  )}
                </article>
              ))}
            </div>
          )}
        </CardBody>
      </Card>
    </>
  );
};
