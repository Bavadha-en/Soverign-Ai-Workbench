import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Bot,
  User,
  Clock,
  Cpu,
  Loader2,
  Trash2,
  Shield,
} from 'lucide-react';
import { api } from '../services/api';
import { ChatMessage } from '../types/api';

const SUGGESTIONS = [
  'What is the SOP for replacing a corroded high-pressure control valve?',
  'Explain the LOTO procedure for electrical isolation per NFPA 70E.',
  'What are the critical thresholds for pipe wall thickness in corrosion inspection?',
  'Calculate pump efficiency for flow rate 50 m3/h, head 60m, power 11kW.',
  'What is the tube plugging threshold for shell-and-tube heat exchangers?',
];

interface DisplayMessage {
  role: 'user' | 'assistant';
  content: string;
  model?: string;
  taskType?: string | null;
  durationMs?: number;
  timestamp: string;
}

export const Chat: React.FC = () => {
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || isLoading) return;

    const userMsg: DisplayMessage = {
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };
    const updatedMessages = [...messages, userMsg];
    setMessages(updatedMessages);
    setInput('');
    setIsLoading(true);

    try {
      const apiMessages: ChatMessage[] = updatedMessages.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const response = await api.chatConversation({
        messages: apiMessages,
        auto_route: true,
      });

      const assistantMsg: DisplayMessage = {
        role: 'assistant',
        content: response.reply,
        model: response.model,
        taskType: response.task_type,
        durationMs: response.duration_ms,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : String(err);
      const errorReply: DisplayMessage = {
        role: 'assistant',
        content: `Error: ${errMsg}`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorReply]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSuggestion = (text: string) => {
    setInput(text);
    inputRef.current?.focus();
  };

  const handleClear = () => {
    setMessages([]);
    setInput('');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 80px)', gap: '0' }}>
      {/* Header */}
      <div className="card" style={{ borderRadius: '6px 6px 0 0', marginBottom: '0', flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Bot size={18} color="#38bdf8" />
            <div>
              <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)' }}>
                ConfigIQ Chat
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Shield size={10} color="#10b981" />
                <span>Sovereign Local LLM — Zero External Calls</span>
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {messages.length > 0 && (
              <button
                onClick={handleClear}
                style={{
                  display: 'flex', alignItems: 'center', gap: '4px',
                  padding: '4px 10px', fontSize: '11px', borderRadius: '4px',
                  backgroundColor: 'var(--bg-panel-elevated)', border: '1px solid var(--border-subtle)',
                  color: 'var(--text-secondary)', cursor: 'pointer',
                }}
              >
                <Trash2 size={11} />
                <span>Clear</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div
        style={{
          flex: 1, overflowY: 'auto', padding: '16px',
          backgroundColor: '#030712',
          borderLeft: '1px solid var(--border-subtle)',
          borderRight: '1px solid var(--border-subtle)',
        }}
      >
        {messages.length === 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: '20px' }}>
            <div style={{ textAlign: 'center' }}>
              <Bot size={40} color="#38bdf8" style={{ opacity: 0.3, marginBottom: '12px' }} />
              <div style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px' }}>
                Sovereign Industrial AI Assistant
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', maxWidth: '400px' }}>
                Ask about SOPs, engineering calculations, inspection procedures, or any industrial topic. All inference runs on your local GPU.
              </div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', width: '100%', maxWidth: '520px' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
                Try asking:
              </div>
              {SUGGESTIONS.map((s, i) => (
                <button
                  key={i}
                  onClick={() => handleSuggestion(s)}
                  style={{
                    textAlign: 'left', padding: '8px 12px', fontSize: '12px',
                    backgroundColor: 'var(--bg-panel-elevated)', border: '1px solid var(--border-subtle)',
                    borderRadius: '6px', color: 'var(--text-secondary)', cursor: 'pointer',
                    transition: 'border-color 0.15s',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'rgba(56,189,248,0.4)')}
                  onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--border-subtle)')}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {messages.map((msg, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex', gap: '10px',
                  flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
                }}
              >
                <div style={{
                  width: '28px', height: '28px', borderRadius: '50%', flexShrink: 0,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  backgroundColor: msg.role === 'user' ? 'rgba(56,189,248,0.15)' : 'rgba(16,185,129,0.15)',
                  border: `1px solid ${msg.role === 'user' ? 'rgba(56,189,248,0.3)' : 'rgba(16,185,129,0.3)'}`,
                }}>
                  {msg.role === 'user' ? <User size={14} color="#38bdf8" /> : <Bot size={14} color="#10b981" />}
                </div>
                <div style={{
                  maxWidth: '75%', padding: '10px 14px', borderRadius: '8px',
                  backgroundColor: msg.role === 'user' ? 'rgba(56,189,248,0.08)' : 'var(--bg-panel-elevated)',
                  border: `1px solid ${msg.role === 'user' ? 'rgba(56,189,248,0.2)' : 'var(--border-subtle)'}`,
                }}>
                  <div style={{
                    fontSize: '13px', color: 'var(--text-primary)', lineHeight: '1.6',
                    whiteSpace: 'pre-wrap', wordBreak: 'break-word',
                  }}>
                    {msg.content}
                  </div>
                  {msg.role === 'assistant' && (msg.model || msg.durationMs) && (
                    <div style={{
                      display: 'flex', alignItems: 'center', gap: '10px', marginTop: '8px',
                      paddingTop: '6px', borderTop: '1px solid var(--border-subtle)',
                      fontSize: '10px', color: 'var(--text-muted)',
                    }}>
                      {msg.model && (
                        <span style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
                          <Cpu size={9} /> {msg.model}
                        </span>
                      )}
                      {msg.taskType && (
                        <span style={{
                          padding: '1px 5px', borderRadius: '3px', fontSize: '9px', fontWeight: 600,
                          backgroundColor: 'rgba(56,189,248,0.1)', color: '#38bdf8',
                        }}>
                          {msg.taskType}
                        </span>
                      )}
                      {msg.durationMs !== undefined && (
                        <span style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
                          <Clock size={9} /> {msg.durationMs.toFixed(0)}ms
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {isLoading && (
              <div style={{ display: 'flex', gap: '10px' }}>
                <div style={{
                  width: '28px', height: '28px', borderRadius: '50%', flexShrink: 0,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  backgroundColor: 'rgba(16,185,129,0.15)', border: '1px solid rgba(16,185,129,0.3)',
                }}>
                  <Loader2 size={14} color="#10b981" className="spin" />
                </div>
                <div style={{
                  padding: '10px 14px', borderRadius: '8px',
                  backgroundColor: 'var(--bg-panel-elevated)', border: '1px solid var(--border-subtle)',
                  fontSize: '12px', color: 'var(--text-muted)', fontStyle: 'italic',
                }}>
                  Processing on local LLM...
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div
        className="card"
        style={{ borderRadius: '0 0 6px 6px', marginTop: '0', flexShrink: 0 }}
      >
        <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-end' }}>
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask ConfigIQ anything... (Shift+Enter for newline)"
            disabled={isLoading}
            rows={2}
            style={{
              flex: 1, resize: 'none', padding: '10px 12px',
              backgroundColor: '#070b14', border: '1px solid var(--border-active)',
              borderRadius: '6px', color: 'var(--text-primary)', fontSize: '13px',
              fontFamily: 'inherit', lineHeight: '1.5',
              outline: 'none',
            }}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="btn btn-primary"
            style={{
              height: '42px', width: '42px', padding: '0',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
};
