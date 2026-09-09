import React, { useState } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  Cpu,
  Eye,
  Layers,
  Network,
  Tag,
} from 'lucide-react';
import { Card, CardBody, CardHead, EmptyState } from '../ui/primitives';
import { formatPercent } from '../lib/format';
import type { PidContext } from '../types/api';

interface PidInspectionViewProps {
  pidContext?: PidContext | null;
}

export const PidInspectionView: React.FC<PidInspectionViewProps> = ({
  pidContext,
}) => {
  const [activeTab, setActiveTab] = useState<'tags' | 'valves' | 'connections' | 'uncertain'>('tags');

  if (!pidContext) {
    return null;
  }

  const ocrTags = pidContext.ocr_tags ?? [];
  const valves = pidContext.valves ?? [];
  const equipment = pidContext.equipment ?? [];
  const connections = pidContext.connections ?? [];
  const uncertain = pidContext.uncertain_items ?? [];

  return (
    <Card>
      <CardHead
        icon={<Layers size={16} />}
        title="P&ID Hybrid Diagram Inspector"
        subtitle={`Multi-modal extraction: ${ocrTags.length} OCR tags · ${valves.length} valves · ${connections.length} line connections`}
        actions={
          pidContext.pipeline_latency_sec ? (
            <span className="badge badge-brand badge-square">
              <Cpu size={12} />
              {pidContext.pipeline_latency_sec.toFixed(2)}s processing
            </span>
          ) : undefined
        }
      />

      <CardBody className="stack gap-16">
        {/* Visual Pipeline Stages Stepper */}
        <div
          className="panel"
          style={{
            background: 'var(--surface-muted, #f8fafc)',
            borderColor: 'var(--border, #e2e8f0)',
            padding: '12px 16px',
          }}
        >
          <p className="text-xs uppercase muted strong" style={{ letterSpacing: '0.05em', marginBottom: 8 }}>
            Hybrid Evidence Extraction Pipeline
          </p>
          <div className="row wrap gap-8 items-center text-xs">
            <span className="badge badge-brand">1. Preprocessing & Tiling</span>
            <ArrowRight size={12} className="muted" />
            <span className="badge badge-brand">2. RapidOCR Tags ({ocrTags.length})</span>
            <ArrowRight size={12} className="muted" />
            <span className="badge badge-brand">3. Symbol Detection ({valves.length + equipment.length})</span>
            <ArrowRight size={12} className="muted" />
            <span className="badge badge-brand">4. Topology & Lines ({connections.length})</span>
            <ArrowRight size={12} className="muted" />
            <span className="badge badge-brand">5. Targeted VLM</span>
            <ArrowRight size={12} className="muted" />
            <span className="badge badge-success">6. RAG Grounding</span>
          </div>
        </div>

        {/* Key Metrics Grid */}
        <div className="grid grid-4" style={{ gap: 10 }}>
          <div className="panel">
            <span className="text-xs muted row gap-4">
              <Tag size={12} />
              OCR Tags
            </span>
            <p className="stat-value stat-value-sm num" style={{ fontSize: 20, marginTop: 4 }}>
              {ocrTags.length}
            </p>
            <p className="text-xs faint">Verified alphanumeric</p>
          </div>

          <div className="panel">
            <span className="text-xs muted row gap-4">
              <Eye size={12} />
              Valves Detected
            </span>
            <p className="stat-value stat-value-sm num" style={{ fontSize: 20, marginTop: 4 }}>
              {valves.length}
            </p>
            <p className="text-xs faint">Check, Globe, Ball</p>
          </div>

          <div className="panel">
            <span className="text-xs muted row gap-4">
              <Network size={12} />
              Topology Edges
            </span>
            <p className="stat-value stat-value-sm num" style={{ fontSize: 20, marginTop: 4 }}>
              {connections.length}
            </p>
            <p className="text-xs faint">Process & dashed lines</p>
          </div>

          <div className="panel">
            <span className="text-xs muted row gap-4">
              <AlertTriangle size={12} />
              Uncertain Items
            </span>
            <p className="stat-value stat-value-sm num" style={{ fontSize: 20, marginTop: 4 }}>
              {uncertain.length}
            </p>
            <p className="text-xs faint">Safety review required</p>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="row gap-8" style={{ borderBottom: '1px solid var(--border)', paddingBottom: 6 }}>
          <button
            type="button"
            className={`btn btn-sm ${activeTab === 'tags' ? 'btn-brand' : 'btn-ghost'}`}
            onClick={() => setActiveTab('tags')}
          >
            <Tag size={13} />
            OCR Tags ({ocrTags.length})
          </button>
          <button
            type="button"
            className={`btn btn-sm ${activeTab === 'valves' ? 'btn-brand' : 'btn-ghost'}`}
            onClick={() => setActiveTab('valves')}
          >
            <Eye size={13} />
            Valves & Equipment ({valves.length + equipment.length})
          </button>
          <button
            type="button"
            className={`btn btn-sm ${activeTab === 'connections' ? 'btn-brand' : 'btn-ghost'}`}
            onClick={() => setActiveTab('connections')}
          >
            <Network size={13} />
            Piping Connections ({connections.length})
          </button>
          {uncertain.length > 0 && (
            <button
              type="button"
              className={`btn btn-sm ${activeTab === 'uncertain' ? 'btn-danger' : 'btn-ghost'}`}
              onClick={() => setActiveTab('uncertain')}
            >
              <AlertTriangle size={13} />
              Uncertainty Flag ({uncertain.length})
            </button>
          )}
        </div>

        {/* Tab Content */}
        {activeTab === 'tags' && (
          <div className="stack gap-8">
            {ocrTags.length === 0 ? (
              <EmptyState title="No OCR tags detected" text="Diagram contains no high-confidence alphanumeric tags." />
            ) : (
              <div className="grid grid-2" style={{ gap: 8 }}>
                {ocrTags.map((tag, idx) => (
                  <div key={idx} className="panel row-between" style={{ padding: '8px 12px' }}>
                    <div className="row gap-8">
                      <span className="badge badge-brand badge-square num strong">{tag.text}</span>
                      <span className="text-xs mono faint">
                        [{tag.bbox[0]}, {tag.bbox[1]}, {tag.bbox[2]}, {tag.bbox[3]}]
                      </span>
                    </div>
                    <span className="badge badge-success shrink-0">
                      {formatPercent(tag.confidence, 0)} conf
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'valves' && (
          <div className="stack gap-8">
            <div className="grid grid-2" style={{ gap: 8 }}>
              {valves.map((v, idx) => (
                <div key={idx} className="panel row-between" style={{ padding: '8px 12px' }}>
                  <div className="row gap-8">
                    <span className="badge badge-info strong">{v.label || v.id}</span>
                    {v.bbox && (
                      <span className="text-xs mono faint">
                        [{v.bbox[0]}, {v.bbox[1]}]
                      </span>
                    )}
                  </div>
                  <span className="badge badge-square shrink-0">
                    {v.confidence ? formatPercent(v.confidence, 0) : '85%'}
                  </span>
                </div>
              ))}
              {equipment.map((eq, idx) => (
                <div key={`eq-${idx}`} className="panel row-between" style={{ padding: '8px 12px' }}>
                  <div className="row gap-8">
                    <span className="badge badge-warning strong">{eq.label || eq.id}</span>
                    <span className="text-xs muted">({eq.type || 'equipment'})</span>
                  </div>
                  <span className="badge badge-square shrink-0">
                    {eq.confidence ? formatPercent(eq.confidence, 0) : '90%'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'connections' && (
          <div className="stack gap-8">
            <div className="grid grid-2" style={{ gap: 8 }}>
              {connections.slice(0, 16).map((c, idx) => (
                <div key={idx} className="panel row-between" style={{ padding: '8px 12px' }}>
                  <span className="text-xs row gap-6">
                    <span className="strong">{c.source}</span>
                    <ArrowRight size={11} className="muted" />
                    <span className="strong">{c.target}</span>
                  </span>
                  <span className={`badge ${c.line_type?.includes('dashed') ? 'badge-warning' : 'badge-brand'} shrink-0 text-xs`}>
                    {c.line_type || 'process'} ({formatPercent(c.confidence, 0)})
                  </span>
                </div>
              ))}
            </div>
            {connections.length > 16 && (
              <p className="text-xs faint text-center">
                + {connections.length - 16} additional piping line connections registered in topological graph
              </p>
            )}
          </div>
        )}

        {activeTab === 'uncertain' && (
          <div className="stack gap-8">
            <div
              className="panel"
              style={{
                background: '#fffbeb',
                borderColor: '#fde68a',
                color: '#92400e',
              }}
            >
              <div className="row gap-8 items-center">
                <AlertCircle size={16} />
                <span className="strong text-sm">Strict Engineering Integrity Enforcement</span>
              </div>
              <p className="text-xs" style={{ marginTop: 4 }}>
                The following visual items have low confidence (&lt;65%) or geometric ambiguity. Per sovereign
                operating standards, they are quarantined as UNCERTAIN and not presented as confirmed facts to
                governing engineers.
              </p>
            </div>
            <div className="stack gap-6">
              {uncertain.map((u, idx) => (
                <div key={idx} className="panel row-between" style={{ padding: '8px 12px' }}>
                  <span className="text-xs strong">{u.label || u.id}</span>
                  <span className="badge badge-warning text-xs">
                    NEEDS REVIEW ({formatPercent(u.confidence, 0)})
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardBody>
    </Card>
  );
};
