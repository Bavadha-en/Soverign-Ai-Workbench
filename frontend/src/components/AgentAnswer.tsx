import React, { useState } from 'react';
import { Check, Copy, FileOutput } from 'lucide-react';
import { Card, CardBody, CardHead } from '../ui/primitives';
import { useToast } from '../ui/toast';

interface AgentAnswerProps {
  output: string | null;
  status: string;
}

/**
 * The agent's written conclusion. Shown above the raw plan because it is what a
 * reviewer reads first.
 */
export const AgentAnswer: React.FC<AgentAnswerProps> = ({ output, status }) => {
  const toast = useToast();
  const [copied, setCopied] = useState(false);

  if (!output || !output.trim()) return null;

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(output);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      toast.error('Clipboard is unavailable in this browser context');
    }
  };

  return (
    <Card>
      <CardHead
        icon={<FileOutput size={16} />}
        title="Result"
        subtitle={`Run ${status.toLowerCase()}`}
        actions={
          <button type="button" className="btn btn-secondary btn-sm" onClick={copy}>
            {copied ? <Check size={13} /> : <Copy size={13} />}
            {copied ? 'Copied' : 'Copy'}
          </button>
        }
      />
      <CardBody>
        <div
          style={{
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            fontSize: 13.5,
            lineHeight: 1.7,
            color: 'var(--text)',
          }}
        >
          {output}
        </div>
      </CardBody>
    </Card>
  );
};
