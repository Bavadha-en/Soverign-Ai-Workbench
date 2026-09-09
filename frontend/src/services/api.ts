import type {
  AgentRunRequest,
  AgentRunResponse,
  AgentTaskState,
  AuditLogResponse,
  ChatConversationRequest,
  ChatConversationResponse,
  DocumentMetadataResponse,
  DocumentUploadResponse,
  HealthResponse,
  KnowledgeIngestResponse,
  KnowledgeSearchResponse,
  NetworkStatus,
  NetworkTelemetry,
  SampleDocumentList,
  SystemStats,
  ToolDefinition,
} from '../types/api';

const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/+$/, '') ||
  'http://localhost:8000';

/** Long enough for a local model to answer, short enough to surface a hung backend. */
const DEFAULT_TIMEOUT_MS = 180_000;
const QUICK_TIMEOUT_MS = 8_000;

class ApiService {
  constructor(private readonly baseUrl: string) {}

  getBaseUrl(): string {
    return this.baseUrl;
  }

  /** Reads the error detail FastAPI returns, falling back to the status line. */
  private static async readError(response: Response): Promise<string> {
    try {
      const body = await response.json();
      if (body?.detail) {
        return typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
      }
    } catch {
      /* body was not JSON */
    }
    return `HTTP ${response.status} ${response.statusText}`;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    timeoutMs: number = DEFAULT_TIMEOUT_MS,
  ): Promise<T> {
    const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(`${this.baseUrl}${path}`, {
        ...options,
        signal: controller.signal,
        headers: { Accept: 'application/json', ...(options.headers ?? {}) },
      });

      if (!response.ok) throw new Error(await ApiService.readError(response));
      return (await response.json()) as T;
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') {
        throw new Error(`Request to ${path} timed out after ${Math.round(timeoutMs / 1000)}s`);
      }
      throw error instanceof Error ? error : new Error(String(error));
    } finally {
      window.clearTimeout(timer);
    }
  }

  private postJson<T>(endpoint: string, body: unknown, timeoutMs?: number): Promise<T> {
    return this.request<T>(
      endpoint,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      },
      timeoutMs,
    );
  }

  /* ---- health and sovereignty ---- */

  getHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health', {}, QUICK_TIMEOUT_MS);
  }

  getNetworkStatus(): Promise<NetworkStatus> {
    return this.request<NetworkStatus>('/network/status', {}, QUICK_TIMEOUT_MS);
  }

  getNetworkTelemetry(): Promise<NetworkTelemetry> {
    return this.request<NetworkTelemetry>('/network/telemetry', {}, QUICK_TIMEOUT_MS);
  }

  getSystemStats(): Promise<SystemStats> {
    return this.request<SystemStats>('/stats', {}, QUICK_TIMEOUT_MS);
  }

  /* ---- agent ---- */

  getAgentTools(): Promise<ToolDefinition[]> {
    return this.request<ToolDefinition[]>('/agent/tools', {}, QUICK_TIMEOUT_MS);
  }

  runAgent(request: AgentRunRequest): Promise<AgentRunResponse> {
    return this.postJson<AgentRunResponse>('/agent/run', request);
  }

  getAgentTask(taskId: string): Promise<AgentTaskState> {
    return this.request<AgentTaskState>(
      `/agent/${encodeURIComponent(taskId)}`,
      {},
      QUICK_TIMEOUT_MS,
    );
  }

  /* ---- deliverables ---- */

  /**
   * The agent reports generated files as absolute host paths. The download
   * endpoint rejects anything containing a drive letter or a leading slash, so
   * reduce the path to the part below the outputs directory before building
   * the URL. Segments are encoded individually so nested folders survive.
   */
  private static toOutputPath(filename: string): string {
    const normalized = filename.replace(/\\/g, '/');
    const marker = normalized.toLowerCase().lastIndexOf('outputs/');
    const relative =
      marker >= 0 ? normalized.slice(marker + 'outputs/'.length) : normalized.split('/').pop() || normalized;

    return relative
      .replace(/^[a-zA-Z]:/, '')
      .replace(/^\/+/, '')
      .split('/')
      .filter(Boolean)
      .map(encodeURIComponent)
      .join('/');
  }

  getOutputFileUrl(filename: string): string {
    return `${this.baseUrl}/outputs/${ApiService.toOutputPath(filename)}`;
  }

  downloadOutputFile(filename: string): void {
    const link = document.createElement('a');
    link.href = this.getOutputFileUrl(filename);
    link.download = filename.split(/[/\\]/).pop() || filename;
    link.rel = 'noopener';
    document.body.appendChild(link);
    link.click();
    link.remove();
  }

  /* ---- documents ---- */

  async uploadDocument(file: File): Promise<DocumentUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/documents/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) throw new Error(await ApiService.readError(response));
    return (await response.json()) as DocumentUploadResponse;
  }

  getDocument(documentId: string): Promise<DocumentMetadataResponse> {
    return this.request<DocumentMetadataResponse>(`/documents/${encodeURIComponent(documentId)}`);
  }

  listSampleDocuments(): Promise<SampleDocumentList> {
    return this.request<SampleDocumentList>('/documents/samples/list', {}, QUICK_TIMEOUT_MS);
  }

  loadSampleDocument(filename: string): Promise<DocumentUploadResponse> {
    return this.request<DocumentUploadResponse>(
      `/documents/samples/load/${encodeURIComponent(filename)}`,
      { method: 'POST' },
    );
  }

  /* ---- knowledge base ---- */

  searchKnowledge(query: string, topK = 5): Promise<KnowledgeSearchResponse> {
    return this.postJson<KnowledgeSearchResponse>('/knowledge/search', { query, top_k: topK });
  }

  ingestKnowledge(directoryPath = 'knowledge_base', forceReindex = false): Promise<KnowledgeIngestResponse> {
    return this.postJson<KnowledgeIngestResponse>('/knowledge/ingest', {
      directory_path: directoryPath,
      force_reindex: forceReindex,
    });
  }

  /* ---- chat ---- */

  chatConversation(request: ChatConversationRequest): Promise<ChatConversationResponse> {
    return this.postJson<ChatConversationResponse>('/chat/conversation', request);
  }

  /* ---- audit ---- */

  getAuditLogs(taskId?: string, limit = 100): Promise<AuditLogResponse> {
    const params = new URLSearchParams();
    if (taskId) params.set('task_id', taskId);
    params.set('limit', String(limit));
    return this.request<AuditLogResponse>(`/logs?${params.toString()}`, {}, QUICK_TIMEOUT_MS);
  }
}

export const api = new ApiService(API_BASE_URL);
export default api;
