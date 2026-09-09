import React, { useState, useEffect, useRef } from 'react';
import {
  Play,
  Upload,
  FileText,
  Image,
  Trash2,
  Sparkles,
  AlertCircle,
  FileSpreadsheet,
  FileCode2,
} from 'lucide-react';
import { api } from '../services/api';
import { DocumentUploadResponse } from '../types/api';

interface Preset {
  id: string;
  title: string;
  task: string;
  icon: React.ReactNode;
  category: string;
}

const PRESETS: Preset[] = [
  {
    id: 'inspection_note',
    title: 'Inspection Report → Approval Note',
    task: 'Analyze this inspection report and prepare an approval note and executive summary.',
    icon: <FileText size={13} color="#38bdf8" />,
    category: 'Inspection & Compliance',
  },
  {
    id: 'eng_calculation',
    title: 'Engineering Calculation',
    task: 'Calculate pump efficiency using flow rate of 50 m3/h, head of 60 m, and power of 11 kW and create a calculation workbook.',
    icon: <FileSpreadsheet size={13} color="#34d399" />,
    category: 'Physics & Sandbox',
  },
  {
    id: 'image_inspection',
    title: 'Industrial Image Inspection',
    task: 'Perform multimodal visual defect inspection on uploaded industrial component and extract anomaly bounding data.',
    icon: <Image size={13} color="#fbbf24" />,
    category: 'Vision & Moondream',
  },
  {
    id: 'confidential_analysis',
    title: 'Confidential Document Analysis',
    task: 'Review confidential technical documentation against internal maintenance SOP standards and flag deviations.',
    icon: <Sparkles size={13} color="#c084fc" />,
    category: 'RAG & Verification',
  },
  {
    id: 'coding_task',
    title: 'Coding / Engineering Task',
    task: 'Generate and execute a sandboxed Python simulation script to compute thermal stress limits under cyclic loading.',
    icon: <FileCode2 size={13} color="#f43f5e" />,
    category: 'Qwen Coder Sandbox',
  },
];

interface TaskInputProps {
  onRunAgent: (task: string, documentIds: string[]) => Promise<void>;
  isRunning: boolean;
  activeTaskId?: string | null;
  initialTask?: string;
}

export const TaskInput: React.FC<TaskInputProps> = ({
  onRunAgent,
  isRunning,
  activeTaskId,
  initialTask,
}) => {
  const [taskText, setTaskText] = useState<string>(initialTask || PRESETS[0].task);
  const [uploadedDocs, setUploadedDocs] = useState<DocumentUploadResponse[]>([]);
  const [availableSamples, setAvailableSamples] = useState<Array<{ filename: string; title: string; category?: string }>>([]);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (initialTask) {
      setTaskText(initialTask);
    }
  }, [initialTask]);

  useEffect(() => {
    const fetchSamples = async () => {
      try {
        const resp = await api.listSampleDocuments();
        if (resp && resp.samples && resp.samples.length > 0) {
          setAvailableSamples(resp.samples);
        }
      } catch (err) {
        console.warn('Could not load sample documents list', err);
      }
    };
    fetchSamples();
  }, []);

  const handleSelectPreset = (preset: Preset) => {
    setTaskText(preset.task);
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setIsUploading(true);
    setUploadError(null);

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      try {
        const uploaded = await api.uploadDocument(file);
        setUploadedDocs((prev) => [...prev, uploaded]);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : String(err);
        setUploadError(`Failed to upload ${file.name}: ${msg}`);
      }
    }

    setIsUploading(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleRemoveDoc = (docId: string) => {
    setUploadedDocs((prev) => prev.filter((d) => d.document_id !== docId));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!taskText.trim() || isRunning) return;
    const docIds = uploadedDocs.map((d) => d.document_id);
    onRunAgent(taskText.trim(), docIds);
  };

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">
          <Play size={14} color="#38bdf8" />
          <span>Autonomous Industrial Agent Task</span>
        </div>
        {activeTaskId && (
          <div style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
            Task ID: <span style={{ color: 'var(--color-brand-light)' }}>{activeTaskId}</span>
          </div>
        )}
      </div>

      {/* Task Presets */}
      <div style={{ marginBottom: '12px' }}>
        <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600, marginBottom: '6px' }}>
          Quick Industrial Presets:
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
          {PRESETS.map((preset) => (
            <button
              key={preset.id}
              type="button"
              onClick={() => handleSelectPreset(preset)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '5px 10px',
                borderRadius: '4px',
                fontSize: '11.5px',
                fontWeight: 500,
                backgroundColor: taskText === preset.task ? 'rgba(56, 189, 248, 0.15)' : 'var(--bg-panel-elevated)',
                border: `1px solid ${taskText === preset.task ? 'rgba(56, 189, 248, 0.4)' : 'var(--border-subtle)'}`,
                color: taskText === preset.task ? 'var(--color-brand-light)' : 'var(--text-secondary)',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              {preset.icon}
              <span>{preset.title}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Task Input Form */}
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '12px' }}>
          <textarea
            className="input-textarea"
            rows={3}
            placeholder="Describe the engineering, inspection, calculation, or deliverable objective..."
            value={taskText}
            onChange={(e) => setTaskText(e.target.value)}
            disabled={isRunning}
          />
        </div>

        {/* Uploaded Documents List */}
        <div style={{ marginBottom: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Attached Local Documents ({uploadedDocs.length})
            </div>
            <label
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '4px 10px',
                borderRadius: '4px',
                backgroundColor: 'var(--bg-panel-elevated)',
                border: '1px solid var(--border-active)',
                color: 'var(--text-primary)',
                fontSize: '11.5px',
                cursor: isUploading || isRunning ? 'not-allowed' : 'pointer',
                opacity: isUploading || isRunning ? 0.6 : 1,
              }}
            >
              <Upload size={12} />
              <span>{isUploading ? 'Uploading...' : 'Upload PDF / Image / Doc'}</span>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".pdf,.docx,.txt,.png,.jpg,.jpeg"
                onChange={handleFileChange}
                disabled={isUploading || isRunning}
                style={{ display: 'none' }}
              />
            </label>
          </div>

          {uploadError && (
            <div
              style={{
                padding: '6px 10px',
                backgroundColor: 'var(--color-danger-bg)',
                border: '1px solid var(--color-danger)',
                borderRadius: '4px',
                fontSize: '11px',
                color: '#f87171',
                marginBottom: '8px',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <AlertCircle size={12} />
              <span>{uploadError}</span>
            </div>
          )}

          {uploadedDocs.length > 0 ? (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '8px' }}>
              {uploadedDocs.map((doc) => (
                <div
                  key={doc.document_id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '4px 8px',
                    backgroundColor: '#070b14',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: '4px',
                    fontSize: '11px',
                  }}
                >
                  <FileText size={12} color="#38bdf8" />
                  <span style={{ color: 'var(--text-primary)', maxWidth: '160px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {doc.filename}
                  </span>
                  <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', fontSize: '10px' }}>
                    ({doc.document_id})
                  </span>
                  {!isRunning && (
                    <button
                      type="button"
                      onClick={() => handleRemoveDoc(doc.document_id)}
                      style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', display: 'flex', padding: 0 }}
                      title="Remove"
                    >
                      <Trash2 size={11} />
                    </button>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontStyle: 'italic', marginBottom: '8px' }}>
              No document attached. Agent will search local Knowledge Base SOPs if needed.
            </div>
          )}

          {/* Quick 1-Click Sample Inspection Images for Demos */}
          <div style={{ marginTop: '6px', padding: '8px 10px', backgroundColor: 'rgba(0, 0, 0, 0.25)', borderRadius: '4px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '10.5px', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '5px' }}>
              <Sparkles size={11} color="#fbbf24" />
              <span>Sample Inspection Attachments (1-Click Load):</span>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
              {(availableSamples.length > 0
                ? availableSamples
                : [
                    { filename: 'metal_nut_surface_scratch.png', title: 'Nut Scratch Defect' },
                    { filename: 'metal_nut_bent_deformation.png', title: 'Nut Bent Defect' },
                    { filename: 'cable_insulation_cut.png', title: 'Cable Cut Defect' },
                    { filename: 'structural_surface_crack.png', title: 'Surface Crack' },
                    { filename: 'scanned_inspection_sheet.png', title: 'Scanned Log' },
                  ]
              ).map((sample) => (
                <button
                  key={sample.filename}
                  type="button"
                  disabled={isUploading || isRunning}
                  onClick={async () => {
                    setIsUploading(true);
                    setUploadError(null);
                    try {
                      const loaded = await api.loadSampleDocument(sample.filename);
                      setUploadedDocs((prev) => {
                        if (prev.some((d) => d.filename === sample.filename)) return prev;
                        return [...prev, loaded];
                      });
                    } catch (err: unknown) {
                      const msg = err instanceof Error ? err.message : String(err);
                      setUploadError(`Failed to load sample ${sample.filename}: ${msg}`);
                    } finally {
                      setIsUploading(false);
                    }
                  }}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                    padding: '3px 8px',
                    borderRadius: '3px',
                    fontSize: '10.5px',
                    backgroundColor: 'var(--bg-panel-elevated)',
                    border: '1px solid var(--border-subtle)',
                    color: 'var(--text-secondary)',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <span>{sample.title}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Action Button Bar */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid var(--border-subtle)', paddingTop: '12px' }}>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            Target Pipeline: <strong style={{ color: 'var(--color-brand-light)' }}>Open-Weight Multi-Tool Orchestration</strong>
          </div>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={!taskText.trim() || isRunning}
            style={{ minWidth: '140px' }}
          >
            {isRunning ? (
              <>
                <span className="status-dot pulse" style={{ backgroundColor: '#fff' }} />
                <span>EXECUTING AGENT...</span>
              </>
            ) : (
              <>
                <Play size={14} fill="#fff" />
                <span>RUN AGENT</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
