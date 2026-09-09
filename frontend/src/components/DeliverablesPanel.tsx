import React from 'react';
import {
  Download,
  FileCheck,
  FileText,
  FileSpreadsheet,
  Presentation,
  CheckCircle2,
  FolderDown,
} from 'lucide-react';
import { api } from '../services/api';

interface DeliverablesPanelProps {
  files: string[];
}

export const DeliverablesPanel: React.FC<DeliverablesPanelProps> = ({ files }) => {
  if (!files || files.length === 0) {
    return (
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <FileCheck size={14} color="#34d399" />
            <span>Generated Sovereign Deliverables</span>
          </div>
        </div>
        <div style={{ textAlign: 'center', padding: '24px 20px', color: 'var(--text-muted)' }}>
          <FolderDown size={24} style={{ opacity: 0.3, marginBottom: '6px' }} />
          <div style={{ fontSize: '12px' }}>No deliverables produced yet.</div>
          <div style={{ fontSize: '11px', marginTop: '2px' }}>
            DOCX, XLSX, and PPTX reports will be generated upon task completion.
          </div>
        </div>
      </div>
    );
  }

  const getDeliverableInfo = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase();

    if (ext === 'docx') {
      return {
        label: 'Word Approval Note',
        extLabel: '.DOCX',
        icon: <FileText size={18} color="#38bdf8" />,
        color: '#38bdf8',
        bg: 'rgba(56, 189, 248, 0.1)',
        border: 'rgba(56, 189, 248, 0.3)',
        desc: '8-Section formal audit approval note with inspection findings & SOP references',
      };
    } else if (ext === 'xlsx') {
      return {
        label: 'Excel Calculation Workbook',
        extLabel: '.XLSX',
        icon: <FileSpreadsheet size={18} color="#34d399" />,
        color: '#34d399',
        bg: 'rgba(16, 185, 129, 0.1)',
        border: 'rgba(16, 185, 129, 0.3)',
        desc: '4-Sheet verified engineering workbook (Inputs, Calculation, Verification, Sources)',
      };
    } else if (ext === 'pptx') {
      return {
        label: 'Executive Summary Deck',
        extLabel: '.PPTX',
        icon: <Presentation size={18} color="#f59e0b" />,
        color: '#f59e0b',
        bg: 'rgba(245, 158, 11, 0.1)',
        border: 'rgba(245, 158, 11, 0.3)',
        desc: '8 Widescreen audit slides for executive presentation & sign-off requirements',
      };
    } else {
      return {
        label: 'Engineering Deliverable',
        extLabel: `.${ext?.toUpperCase() || 'FILE'}`,
        icon: <FileCheck size={18} color="#c084fc" />,
        color: '#c084fc',
        bg: 'rgba(192, 132, 252, 0.1)',
        border: 'rgba(192, 132, 252, 0.3)',
        desc: 'Exported local deliverable asset',
      };
    }
  };

  const handleDownload = (file: string) => {
    api.downloadOutputFile(file);
  };

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">
          <FileCheck size={14} color="#34d399" />
          <span>Generated Sovereign Deliverables ({files.length})</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', color: '#34d399', fontWeight: 600 }}>
          <CheckCircle2 size={12} />
          <span>CERTIFIED LOCAL</span>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {files.map((file: string, idx: number) => {
          const info = getDeliverableInfo(file);
          const cleanName = file.split(/[/\\]/).pop() || file;

          return (
            <div
              key={idx}
              style={{
                padding: '12px 14px',
                backgroundColor: '#070b14',
                border: `1px solid ${info.border}`,
                borderRadius: '6px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: '12px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', minWidth: 0 }}>
                <div
                  style={{
                    width: '36px',
                    height: '36px',
                    borderRadius: '6px',
                    backgroundColor: info.bg,
                    border: `1px solid ${info.border}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}
                >
                  {info.icon}
                </div>
                <div style={{ minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)' }}>
                      {info.label}
                    </span>
                    <span
                      style={{
                        fontSize: '10px',
                        fontFamily: 'var(--font-mono)',
                        fontWeight: 700,
                        color: info.color,
                        backgroundColor: info.bg,
                        padding: '1px 5px',
                        borderRadius: '3px',
                      }}
                    >
                      {info.extLabel}
                    </span>
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginTop: '2px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {cleanName}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                    {info.desc}
                  </div>
                </div>
              </div>

              <button
                type="button"
                onClick={() => handleDownload(file)}
                className="btn btn-primary btn-sm"
                style={{
                  flexShrink: 0,
                  padding: '6px 14px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  backgroundColor: info.bg,
                  borderColor: info.color,
                  color: '#fff',
                }}
              >
                <Download size={13} />
                <span>Download</span>
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
};
