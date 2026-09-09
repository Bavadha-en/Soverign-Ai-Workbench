import React from 'react';
import { AlertCircle, Inbox, Loader2 } from 'lucide-react';

/* ------------------------------------------------------------------ *
 * Card
 * ------------------------------------------------------------------ */

interface CardProps {
  children: React.ReactNode;
  className?: string;
  id?: string;
}

export const Card: React.FC<CardProps> = ({ children, className, id }) => (
  <section id={id} className={className ? `card ${className}` : 'card'}>
    {children}
  </section>
);

interface CardHeadProps {
  icon?: React.ReactNode;
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  actions?: React.ReactNode;
}

export const CardHead: React.FC<CardHeadProps> = ({ icon, title, subtitle, actions }) => (
  <header className="card-head">
    <div className="card-head-title">
      {icon}
      <div className="grow">
        <div className="truncate">{title}</div>
        {subtitle && <div className="card-head-sub">{subtitle}</div>}
      </div>
    </div>
    {actions && <div className="card-head-actions">{actions}</div>}
  </header>
);

export const CardBody: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className,
}) => <div className={className ? `card-body ${className}` : 'card-body'}>{children}</div>;

/* ------------------------------------------------------------------ *
 * Page header
 * ------------------------------------------------------------------ */

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
}

export const PageHeader: React.FC<PageHeaderProps> = ({ title, subtitle, actions }) => (
  <div className="page-head">
    <div>
      <h1 className="page-title">{title}</h1>
      {subtitle && <p className="page-subtitle">{subtitle}</p>}
    </div>
    {actions && <div className="page-head-actions">{actions}</div>}
  </div>
);

/* ------------------------------------------------------------------ *
 * Badge
 * ------------------------------------------------------------------ */

export type Tone = 'neutral' | 'brand' | 'success' | 'warning' | 'danger' | 'violet';

interface BadgeProps {
  children: React.ReactNode;
  tone?: Tone;
  square?: boolean;
  icon?: React.ReactNode;
  title?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  tone = 'neutral',
  square = false,
  icon,
  title,
}) => (
  <span className={`badge badge-${tone}${square ? ' badge-square' : ''}`} title={title}>
    {icon}
    {children}
  </span>
);

/* ------------------------------------------------------------------ *
 * Stat card
 * ------------------------------------------------------------------ */

const TONE_COLORS: Record<Tone, { fg: string; bg: string }> = {
  neutral: { fg: 'var(--text-muted)', bg: 'var(--surface-sunken)' },
  brand: { fg: 'var(--brand-600)', bg: 'var(--brand-50)' },
  success: { fg: 'var(--success-600)', bg: 'var(--success-50)' },
  warning: { fg: 'var(--warning-600)', bg: 'var(--warning-50)' },
  danger: { fg: 'var(--danger-600)', bg: 'var(--danger-50)' },
  violet: { fg: 'var(--violet-600)', bg: 'var(--violet-50)' },
};

interface StatCardProps {
  label: string;
  value: React.ReactNode;
  unit?: string;
  footnote?: React.ReactNode;
  icon: React.ReactNode;
  tone?: Tone;
  /** Use for text values (e.g. status words) that need a smaller type size. */
  compact?: boolean;
  loading?: boolean;
}

export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  unit,
  footnote,
  icon,
  tone = 'brand',
  compact = false,
  loading = false,
}) => {
  const colors = TONE_COLORS[tone];
  return (
    <div className="stat">
      <div className="stat-head">
        <span className="stat-label">{label}</span>
        <span className="stat-icon" style={{ background: colors.bg, color: colors.fg }}>
          {icon}
        </span>
      </div>
      {loading ? (
        <div className="skeleton" style={{ height: 30, width: '60%' }} />
      ) : (
        <div
          className={compact ? 'stat-value stat-value-sm' : 'stat-value'}
          style={{ color: tone === 'neutral' ? undefined : colors.fg }}
        >
          {value}
          {unit && <span className="stat-unit">{unit}</span>}
        </div>
      )}
      {footnote && <div className="stat-foot">{footnote}</div>}
    </div>
  );
};

/* ------------------------------------------------------------------ *
 * Empty state
 * ------------------------------------------------------------------ */

interface EmptyStateProps {
  title: string;
  text?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ title, text, icon, action }) => (
  <div className="empty">
    <div className="empty-icon">{icon ?? <Inbox size={20} />}</div>
    <p className="empty-title">{title}</p>
    {text && <p className="empty-text">{text}</p>}
    {action && <div style={{ marginTop: 12 }}>{action}</div>}
  </div>
);

/* ------------------------------------------------------------------ *
 * Notice
 * ------------------------------------------------------------------ */

interface NoticeProps {
  children: React.ReactNode;
  tone?: 'info' | 'success' | 'warning' | 'danger';
  icon?: React.ReactNode;
  actions?: React.ReactNode;
}

export const Notice: React.FC<NoticeProps> = ({ children, tone = 'info', icon, actions }) => (
  <div className={`notice notice-${tone}`} role={tone === 'danger' ? 'alert' : 'status'}>
    {icon ?? <AlertCircle size={16} />}
    <div className="grow">{children}</div>
    {actions && <div className="notice-actions">{actions}</div>}
  </div>
);

/* ------------------------------------------------------------------ *
 * Spinner
 * ------------------------------------------------------------------ */

export const Spinner: React.FC<{ size?: number; label?: string }> = ({ size = 15, label }) => (
  <span className="row gap-6" role="status">
    <Loader2 size={size} className="spin" aria-hidden />
    {label && <span className="text-sm muted">{label}</span>}
    {!label && <span className="sr-only">Loading</span>}
  </span>
);

/* ------------------------------------------------------------------ *
 * Section label — small heading used inside cards
 * ------------------------------------------------------------------ */

export const SectionLabel: React.FC<{ children: React.ReactNode; right?: React.ReactNode }> = ({
  children,
  right,
}) => (
  <div className="row-between" style={{ marginBottom: 8 }}>
    <span className="eyebrow">{children}</span>
    {right}
  </div>
);
