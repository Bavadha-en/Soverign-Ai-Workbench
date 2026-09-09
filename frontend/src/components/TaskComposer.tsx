import React, { useEffect, useRef, useState } from 'react';
import {
  FileSpreadsheet,
  FileText,
  Image as ImageIcon,
  Paperclip,
  Play,
  ScanSearch,
  SquareCode,
  Upload,
  X,
} from 'lucide-react';
import { Card, CardBody, CardHead, SectionLabel, Spinner } from '../ui/primitives';
import { useToast } from '../ui/toast';
import { api } from '../services/api';
import { baseName, formatBytes } from '../lib/format';
import type { DocumentUploadResponse, SampleDocument } from '../types/api';

interface Preset {
  id: string;
  label: string;
  task: string;
  icon: React.ReactNode;
}

const PRESETS: Preset[] = [
  {
    id: 'approval-note',
    label: 'Inspection → approval note',
    task: 'Analyse the attached inspection report, check the findings against the maintenance SOPs, and prepare an approval note with an executive summary.',
    icon: <FileText size={13} />,
  },
  {
    id: 'pump-efficiency',
    label: 'Pump efficiency workbook',
    task: 'Calculate pump efficiency for a flow rate of 50 m3/h, a head of 60 m and a shaft power of 11 kW, then produce a calculation workbook showing the working.',
    icon: <FileSpreadsheet size={13} />,
  },
  {
    id: 'defect-scan',
    label: 'Visual defect inspection',
    task: 'Run a visual defect inspection on the attached component image, classify the anomaly and rank it by severity against the inspection guide.',
    icon: <ImageIcon size={13} />,
  },
  {
    id: 'sop-deviation',
    label: 'SOP deviation review',
    task: 'Review the attached technical documentation against the internal maintenance SOP standards and flag every deviation with its source clause.',
    icon: <ScanSearch size={13} />,
  },
  {
    id: 'thermal-sim',
    label: 'Sandboxed simulation',
    task: 'Generate and run a sandboxed Python simulation that computes thermal stress limits under cyclic loading, then verify the result stays within physical bounds.',
    icon: <SquareCode size={13} />,
  },
];

const FALLBACK_SAMPLES: Array<Pick<SampleDocument, 'filename' | 'title'>> = [
  { filename: 'metal_nut_surface_scratch.png', title: 'Nut — surface scratch' },
  { filename: 'metal_nut_bent_deformation.png', title: 'Nut — bent deformation' },
  { filename: 'cable_insulation_cut.png', title: 'Cable — insulation cut' },
  { filename: 'structural_surface_crack.png', title: 'Structure — surface crack' },
  { filename: 'scanned_inspection_sheet.png', title: 'Scanned inspection sheet' },
];

interface TaskComposerProps {
  onRun: (task: string, documentIds: string[]) => void;
  running: boolean;
  activeTaskId: string | null;
  presetTask?: string;
}

export const TaskComposer: React.FC<TaskComposerProps> = ({
  onRun,
  running,
  activeTaskId,
  presetTask,
}) => {
  const toast = useToast();
  const [task, setTask] = useState(PRESETS[0].task);
  const [attachments, setAttachments] = useState<DocumentUploadResponse[]>([]);
  const [samples, setSamples] = useState<Array<Pick<SampleDocument, 'filename' | 'title'>>>(
    FALLBACK_SAMPLES,
  );
  const [busyFile, setBusyFile] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (presetTask) setTask(presetTask);
  }, [presetTask]);

  useEffect(() => {
    let cancelled = false;
    api
      .listSampleDocuments()
      .then((response) => {
        if (!cancelled && response.samples?.length) setSamples(response.samples);
      })
      .catch(() => {
        /* the bundled fallback list is good enough when the endpoint is unavailable */
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const addAttachment = (document: DocumentUploadResponse) => {
    setAttachments((current) =>
      current.some((item) => item.document_id === document.document_id)
        ? current
        : [...current, document],
    );
  };

  const uploadFiles = async (files: FileList | File[]) => {
    for (const file of Array.from(files)) {
      setBusyFile(file.name);
      try {
        addAttachment(await api.uploadDocument(file));
        toast.success(`Attached ${file.name}`);
      } catch (error) {
        toast.error(`Could not attach ${file.name}: ${(error as Error).message}`);
      }
    }
    setBusyFile(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const loadSample = async (filename: string, title: string) => {
    setBusyFile(filename);
    try {
      addAttachment(await api.loadSampleDocument(filename));
      toast.success(`Loaded sample: ${title}`);
    } catch (error) {
      toast.error(`Could not load ${title}: ${(error as Error).message}`);
    } finally {
      setBusyFile(null);
    }
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    const trimmed = task.trim();
    if (!trimmed || running) return;
    onRun(
      trimmed,
      attachments.map((item) => item.document_id),
    );
  };

  return (
    <Card>
      <CardHead
        icon={<Play size={16} />}
        title="New task"
        subtitle="Describe an objective in plain English — the agent plans and executes the tool chain."
        actions={
          activeTaskId ? (
            <span className="text-xs mono muted">Run {activeTaskId}</span>
          ) : undefined
        }
      />

      <CardBody>
        <form onSubmit={handleSubmit} className="stack gap-16">
          <div>
            <SectionLabel>Start from a template</SectionLabel>
            <div className="row wrap gap-6">
              {PRESETS.map((preset) => (
                <button
                  key={preset.id}
                  type="button"
                  className="chip"
                  aria-pressed={task === preset.task}
                  onClick={() => setTask(preset.task)}
                  disabled={running}
                >
                  {preset.icon}
                  {preset.label}
                </button>
              ))}
            </div>
          </div>

          <div className="field">
            <label className="label" htmlFor="task-objective">
              Objective
            </label>
            <textarea
              id="task-objective"
              className="textarea"
              rows={4}
              value={task}
              onChange={(event) => setTask(event.target.value)}
              disabled={running}
              placeholder="e.g. Review the attached valve inspection report and prepare an approval note."
            />
          </div>

          <div className="stack gap-10">
            <SectionLabel
              right={
                <span className="text-xs muted">
                  {attachments.length} attached
                </span>
              }
            >
              Evidence
            </SectionLabel>

            <label
              className={`dropzone${dragging ? ' is-dragging' : ''}`}
              onDragOver={(event) => {
                event.preventDefault();
                setDragging(true);
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={(event) => {
                event.preventDefault();
                setDragging(false);
                if (!running && event.dataTransfer.files.length) uploadFiles(event.dataTransfer.files);
              }}
            >
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".pdf,.docx,.txt,.png,.jpg,.jpeg"
                className="sr-only"
                disabled={running || busyFile !== null}
                onChange={(event) => event.target.files && uploadFiles(event.target.files)}
              />
              <span className="row gap-8" style={{ justifyContent: 'center' }}>
                {busyFile ? <Spinner size={15} /> : <Upload size={15} className="muted" />}
                <span className="text-sm">
                  {busyFile ? (
                    <>Uploading {busyFile}…</>
                  ) : (
                    <>
                      <strong className="strong">Drop files</strong> or browse — PDF, DOCX, TXT, PNG,
                      JPG
                    </>
                  )}
                </span>
              </span>
              <p className="text-xs faint" style={{ marginTop: 4 }}>
                Files stay on this machine. Nothing is uploaded off-host.
              </p>
            </label>

            {attachments.length > 0 && (
              <div className="row wrap gap-6">
                {attachments.map((doc) => (
                  <span key={doc.document_id} className="file-tag">
                    <Paperclip size={12} className="muted shrink-0" />
                    <span className="truncate" title={doc.filename}>
                      {baseName(doc.filename)}
                    </span>
                    <span className="text-xs faint shrink-0">{formatBytes(doc.file_size)}</span>
                    {!running && (
                      <button
                        type="button"
                        className="file-tag-remove"
                        aria-label={`Remove ${doc.filename}`}
                        onClick={() =>
                          setAttachments((current) =>
                            current.filter((item) => item.document_id !== doc.document_id),
                          )
                        }
                      >
                        <X size={12} />
                      </button>
                    )}
                  </span>
                ))}
              </div>
            )}

            <div className="panel">
              <p className="text-xs muted" style={{ marginBottom: 8 }}>
                Sample inspection assets — one click, no file dialog
              </p>
              <div className="row wrap gap-6">
                {samples.map((sample) => (
                  <button
                    key={sample.filename}
                    type="button"
                    className="chip"
                    disabled={running || busyFile !== null}
                    onClick={() => loadSample(sample.filename, sample.title)}
                  >
                    {sample.title}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="row-between" style={{ paddingTop: 2 }}>
            <p className="text-sm muted">
              {attachments.length === 0
                ? 'No evidence attached — the agent will fall back to the local knowledge base.'
                : `${attachments.length} document${attachments.length === 1 ? '' : 's'} will be read by the agent.`}
            </p>
            <button type="submit" className="btn btn-primary btn-lg" disabled={!task.trim() || running}>
              {running ? (
                <>
                  <Spinner size={15} />
                  Running…
                </>
              ) : (
                <>
                  <Play size={15} />
                  Run task
                </>
              )}
            </button>
          </div>
        </form>
      </CardBody>
    </Card>
  );
};
