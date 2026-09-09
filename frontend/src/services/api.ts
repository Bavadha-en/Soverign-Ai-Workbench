import {
  HealthResponse,
  NetworkStatus,
  ToolDefinition,
  AgentRunRequest,
  AgentRunResponse,
  AgentTaskState,
  DocumentUploadResponse,
  DocumentMetadataResponse,
  AuditLogResponse,
  KnowledgeSearchResponse,
  KnowledgeIngestResponse,
} from '../types/api';

const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/+$/, '') ||
  'http://localhost:8000';

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  public getBaseUrl(): string {
    return this.baseUrl;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          Accept: 'application/json',
          ...(options.headers || {}),
        },
      });

      if (!response.ok) {
        let errorDetail = `HTTP ${response.status} ${response.statusText}`;
        try {
          const errJson = await response.json();
          if (errJson && errJson.detail) {
            errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
          }
        } catch {
          // fallback to status text
        }
        throw new Error(errorDetail);
      }

      return (await response.json()) as T;
    } catch (err: unknown) {
      if (err instanceof Error) {
        throw err;
      }
      throw new Error(String(err));
    }
  }

  // --- Health & Sovereignty ---

  public async getHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health');
  }

  public async getNetworkStatus(): Promise<NetworkStatus> {
    return this.request<NetworkStatus>('/network/status');
  }

  public async getNetworkTelemetry(): Promise<import('../types/api').NetworkTelemetry> {
    return this.request<import('../types/api').NetworkTelemetry>('/network/telemetry');
  }


  // --- Agent & Tools ---

  public async getAgentTools(): Promise<ToolDefinition[]> {
    return this.request<ToolDefinition[]>('/agent/tools');
  }

  public async runAgent(request: AgentRunRequest): Promise<AgentRunResponse> {
    return this.request<AgentRunResponse>('/agent/run', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
  }

  public async getAgentTask(taskId: string): Promise<AgentTaskState> {
    return this.request<AgentTaskState>(`/agent/${encodeURIComponent(taskId)}`);
  }

  // --- Deliverables & Files ---

  public getOutputFileUrl(filename: string): string {
    // Return relative or absolute URL to backend secure output endpoint
    const cleanFilename = filename.replace(/^outputs[/\\]/, '');
    return `${this.baseUrl}/outputs/${encodeURIComponent(cleanFilename)}`;
  }

  public async downloadOutputFile(filename: string): Promise<void> {
    const url = this.getOutputFileUrl(filename);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename.split('/').pop() || filename);
    link.target = '_blank';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  // --- Documents & Upload ---

  public async uploadDocument(file: File): Promise<DocumentUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const url = `${this.baseUrl}/documents/upload`;
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      let errorDetail = `Upload failed with status ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson && errJson.detail) {
          errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
        }
      } catch {
        // ignore json parse error
      }
      throw new Error(errorDetail);
    }

    return (await response.json()) as DocumentUploadResponse;
  }

  public async getDocument(documentId: string): Promise<DocumentMetadataResponse> {
    return this.request<DocumentMetadataResponse>(`/documents/${encodeURIComponent(documentId)}`);
  }

  public async listSampleDocuments(): Promise<{ samples: Array<{ filename: string; title: string; category: string; description: string; file_size: number; url: string }> }> {
    return this.request<{ samples: Array<{ filename: string; title: string; category: string; description: string; file_size: number; url: string }> }>('/documents/samples/list');
  }

  public async loadSampleDocument(filename: string): Promise<DocumentUploadResponse> {
    return this.request<DocumentUploadResponse>(`/documents/samples/load/${encodeURIComponent(filename)}`, {
      method: 'POST',
    });
  }

  // --- Knowledge Base ---

  public async searchKnowledge(query: string, topK: number = 5): Promise<KnowledgeSearchResponse> {
    return this.request<KnowledgeSearchResponse>('/knowledge/search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query, top_k: topK }),
    });
  }

  public async ingestKnowledge(directoryPath: string = 'knowledge_base', forceReindex: boolean = false): Promise<KnowledgeIngestResponse> {
    return this.request<KnowledgeIngestResponse>('/knowledge/ingest', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ directory_path: directoryPath, force_reindex: forceReindex }),
    });
  }

  // --- Audit Logs ---

  public async getAuditLogs(taskId?: string, limit: number = 100): Promise<AuditLogResponse> {
    const params = new URLSearchParams();
    if (taskId) params.append('task_id', taskId);
    if (limit) params.append('limit', limit.toString());
    const queryStr = params.toString() ? `?${params.toString()}` : '';
    return this.request<AuditLogResponse>(`/logs${queryStr}`);
  }
}

export const api = new ApiService(API_BASE_URL);
export default api;
