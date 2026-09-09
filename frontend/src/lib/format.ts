/** Shared formatting helpers. Kept dependency-free so they work offline. */

export function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  const exp = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const value = bytes / Math.pow(1024, exp);
  return `${value.toFixed(exp === 0 ? 0 : 1)} ${units[exp]}`;
}

export function formatDuration(ms: number): string {
  if (!Number.isFinite(ms) || ms < 0) return '—';
  if (ms < 1000) return `${Math.round(ms)} ms`;
  if (ms < 60_000) return `${(ms / 1000).toFixed(1)} s`;
  const minutes = Math.floor(ms / 60_000);
  const seconds = Math.round((ms % 60_000) / 1000);
  return `${minutes}m ${seconds}s`;
}

export function formatTime(iso?: string | null): string {
  if (!iso) return '—';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '—';
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

export function formatDateTime(iso?: string | null): string {
  if (!iso) return '—';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '—';
  return date.toLocaleString([], {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

export function formatPercent(ratio?: number | null, digits = 0): string {
  if (typeof ratio !== 'number' || Number.isNaN(ratio)) return '—';
  return `${(ratio * 100).toFixed(digits)}%`;
}

/** Strips any directory prefix from a backend-supplied path. */
export function baseName(path: string): string {
  return path.split(/[\\/]/).pop() || path;
}

export function fileExtension(path: string): string {
  const name = baseName(path);
  const dot = name.lastIndexOf('.');
  return dot === -1 ? '' : name.slice(dot + 1).toLowerCase();
}

/** Shortens long identifiers for display without losing the distinguishing tail. */
export function shortId(id?: string | null, head = 8, tail = 4): string {
  if (!id) return '—';
  if (id.length <= head + tail + 1) return id;
  return `${id.slice(0, head)}…${id.slice(-tail)}`;
}

export function pluralize(count: number, singular: string, plural?: string): string {
  return count === 1 ? singular : plural ?? `${singular}s`;
}

/** Normalises the claim-status spellings the backend can emit. */
export function normalizeClaimStatus(
  status: string,
):
  | 'SUPPORTED'
  | 'SUPPORTED_BY_IMAGE'
  | 'SUPPORTED_BY_OCR'
  | 'SUPPORTED_BY_RAG'
  | 'MODEL_INFERENCE'
  | 'NEEDS REVIEW'
  | 'UNSUPPORTED' {
  const value = (status || '').toUpperCase().trim();
  if (value.includes('IMAGE')) return 'SUPPORTED_BY_IMAGE';
  if (value.includes('OCR')) return 'SUPPORTED_BY_OCR';
  if (value.includes('RAG')) return 'SUPPORTED_BY_RAG';
  if (value.includes('INFERENCE')) return 'MODEL_INFERENCE';
  if (value === 'SUPPORTED') return 'SUPPORTED';
  if (value === 'UNSUPPORTED') return 'UNSUPPORTED';
  return 'NEEDS REVIEW';
}
