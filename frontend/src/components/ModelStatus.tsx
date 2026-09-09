import React from 'react';
import { Cpu, Brain, Eye, Hash, ArrowRightLeft, Sparkles, Check } from 'lucide-react';

interface ModelStatusProps {
  currentTask?: string;
  activeModel?: string;
}

export const ModelStatus: React.FC<ModelStatusProps> = ({ currentTask = '', activeModel }) => {
  // Infer routed model based on task keywords if not explicitly specified
  const getRoutedModel = () => {
    if (activeModel) return activeModel;
    const lower = currentTask.toLowerCase();
    if (lower.includes('calculate') || lower.includes('efficiency') || lower.includes('physics') || lower.includes('pump')) {
      return 'qwen2.5-coder:7b / qwen2.5-coder:14b';
    }
    if (lower.includes('image') || lower.includes('defect') || lower.includes('visual') || lower.includes('anomaly')) {
      return 'moondream:latest';
    }
    if (lower.includes('code') || lower.includes('script') || lower.includes('python')) {
      return 'qwen2.5-coder:7b';
    }
    return 'llama3:latest';
  };

  const routed = getRoutedModel();

  const routes = [
    {
      role: 'General Reasoning & Reports',
      model: 'llama3:latest',
      desc: 'SOP analysis, structured synthesis, approval note drafting',
      icon: <Brain size={14} color="#38bdf8" />,
      active: routed.includes('llama3'),
    },
    {
      role: 'Standard Engineering Scripts',
      model: 'qwen2.5-coder:7b',
      desc: 'Python code sandbox generation & formula execution',
      icon: <Cpu size={14} color="#818cf8" />,
      active: routed.includes('qwen2.5-coder:7b'),
    },
    {
      role: 'Heavy Simulation & Physics',
      model: 'qwen2.5-coder:14b',
      desc: 'Numerical simulation & thermodynamic boundary auditing',
      icon: <Cpu size={14} color="#c084fc" />,
      active: routed.includes('14b'),
    },
    {
      role: 'Multimodal Vision & Defect',
      model: 'moondream:latest',
      desc: 'Visual inspection & anomaly bounding box extraction',
      icon: <Eye size={14} color="#34d399" />,
      active: routed.includes('moondream'),
    },
    {
      role: 'Local Vector Embeddings',
      model: 'nomic-embed-text:latest',
      desc: 'Offline cosine similarity index & sliding chunk search',
      icon: <Hash size={14} color="#fbbf24" />,
      active: true,
    },
  ];

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">
          <ArrowRightLeft size={14} color="#38bdf8" />
          <span>Open-Weight Model Router Matrix</span>
        </div>
        <div
          style={{
            fontSize: '11px',
            color: 'var(--color-brand-light)',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            fontFamily: 'var(--font-mono)',
          }}
        >
          <Sparkles size={11} />
          <span>DYNAMIC ROUTING</span>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {routes.map((r, idx) => (
          <div
            key={idx}
            style={{
              padding: '8px 12px',
              backgroundColor: r.active ? 'rgba(56, 189, 248, 0.08)' : '#070b14',
              border: `1px solid ${r.active ? 'rgba(56, 189, 248, 0.35)' : 'var(--border-subtle)'}`,
              borderRadius: '4px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div
                style={{
                  width: '28px',
                  height: '28px',
                  borderRadius: '4px',
                  backgroundColor: 'var(--bg-panel-elevated)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                }}
              >
                {r.icon}
              </div>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {r.role}
                  </span>
                  <span
                    style={{
                      fontSize: '10.5px',
                      fontFamily: 'var(--font-mono)',
                      color: 'var(--color-brand-light)',
                      backgroundColor: 'rgba(56, 189, 248, 0.1)',
                      padding: '1px 5px',
                      borderRadius: '3px',
                      fontWeight: 600,
                    }}
                  >
                    {r.model}
                  </span>
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  {r.desc}
                </div>
              </div>
            </div>

            {r.active && (
              <div
                style={{
                  fontSize: '10px',
                  fontWeight: 700,
                  color: '#10b981',
                  backgroundColor: 'rgba(16, 185, 129, 0.15)',
                  padding: '2px 6px',
                  borderRadius: '3px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  fontFamily: 'var(--font-mono)',
                }}
              >
                <Check size={11} />
                <span>ROUTED</span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
