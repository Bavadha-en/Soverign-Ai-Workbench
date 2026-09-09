export type FactVerificationStatus =
  | 'SUPPORTED'
  | 'SUPPORTED_BY_IMAGE'
  | 'SUPPORTED_BY_OCR'
  | 'SUPPORTED_BY_RAG'
  | 'MODEL_INFERENCE'
  | 'UNSUPPORTED'
  | 'NEEDS REVIEW'
  | 'NEEDS_REVIEW';

export interface PidItem {
  id: string;
  label?: string;
  type?: string;
  confidence?: number;
  bbox?: [number, number, number, number];
  source?: string;
}

export interface PidConnection {
  source: string;
  target: string;
  line_type?: string;
  confidence?: number;
  status?: string;
  distance_px?: number;
}

export interface PidContext {
  equipment?: PidItem[];
  valves?: PidItem[];
  instruments?: PidItem[];
  connections?: PidConnection[];
  ocr_tags?: Array<{ text: string; confidence: number; bbox: [number, number, number, number]; source?: string }>;
  detected_symbols?: Array<{ symbol_type: string; category: string; confidence: number; bbox: [number, number, number, number] }>;
  uncertain_items?: PidItem[];
  pipeline_latency_sec?: number;
  has_dashed_instrument_lines?: boolean;
}

export interface HealthResponse {
  status: string;
  app_name: string;
  version: string;
  environment: string;
  timestamp: string;
  ollama: string | null;
  models: Record<string, boolean> | null;
  network?: string;
}

export interface NetworkStatus {
  internet_required: boolean;
  external_ai_calls: number;
  external_connections: number;
  status: 'LOCAL_ONLY' | 'WARNING_EXTERNAL_ATTEMPT_DETECTED' | string;
}

export interface NetworkConnectionEvent {
  id: string;
  timestamp: string;
  protocol: string;
  source: string;
  destination: string;
  process: string;
  status: string;
  is_external: boolean;
  bytes_transferred: number;
}

export interface NetworkInterfaceInfo {
  name: string;
  ip: string;
  type: string;
  status: string;
  egress_allowed: boolean;
}

export interface ListeningPortInfo {
  port: number;
  service: string;
  binding: string;
  scope: string;
  status: string;
}

export interface NetworkTelemetry {
  timestamp: string;
  status: string;
  air_gap_compliant: boolean;
  internet_required: boolean;
  external_ai_calls: number;
  external_connections: number;
  wan_egress_blocked: number;
  total_local_requests: number;
  active_listening_ports: ListeningPortInfo[];
  interfaces: NetworkInterfaceInfo[];
  recent_traffic: NetworkConnectionEvent[];
  integrity_hash: string;
}

export interface ToolDefinition {
  name: string;
  description: string;
  input_schema?: Record<string, unknown>;
  output_schema?: Record<string, unknown>;
}

export type ToolInfo = ToolDefinition;

/** Actual model names configured per role (GET /chat/registry). */
export interface ModelRegistryResponse {
  registry: Record<string, string>;
  status: string;
}

/** Aggregate counters rendered on the overview page (GET /stats). */
export interface SystemStats {
  tasks_completed: number;
  total_actions: number;
  external_attempts: number;
  kb_documents: number;
  chunks_indexed: number;
  deliverables_generated: number;
  ollama_available: boolean;
  models_loaded: number;
  uptime_status: string;
}

/** A bundled inspection asset that can be attached without a file dialog. */
export interface SampleDocument {
  filename: string;
  title: string;
  category: string;
  description: string;
  file_size: number;
  url: string;
}

export interface SampleDocumentList {
  samples: SampleDocument[];
}

export interface PlanStep {
  step: number;
  action: string;
  tool: string;
  description?: string;
  params?: Record<string, unknown>;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'retried' | string;
  result?: unknown;
  error?: string | null;
}

export interface FactClaimVerification {
  claim: string;
  status: FactVerificationStatus;
  source_document?: string | null;
  page?: number | null;
  confidence?: number;
  evidence?: string | null;
}

export interface VerificationSummary {
  is_valid: boolean;
  total_claims: number;
  supported_claims: number;
  unsupported_claims: number;
  needs_review_claims: number;
  claims: FactClaimVerification[];
  calculation_valid?: boolean | null;
  notes?: string[];
}

export interface SourceReference {
  document?: string;
  page?: number | null;
  content?: string;
  score?: number;
  metadata?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface Deliverable {
  filename: string;
  type: 'docx' | 'xlsx' | 'pptx' | 'pdf' | 'other';
  label: string;
  description: string;
  downloadUrl: string;
}

export interface AgentRunRequest {
  task: string;
  document_ids?: string[];
  parameters?: Record<string, unknown>;
}

export interface AgentRunResponse {
  task_id: string;
  status: string;
  plan: PlanStep[];
  steps_completed: number;
  final_output: string | null;
  sources: SourceReference[];
  generated_files: string[];
  verification: VerificationSummary | null;
  execution_trace: string[];
  local: boolean;
}

export interface AgentTaskState {
  task_id: string;
  status: 'PLANNING' | 'EXECUTING' | 'VERIFYING' | 'RETRYING' | 'COMPLETED' | 'FAILED' | string;
  current_step_index: number;
  plan: PlanStep[];
  completed_steps: Array<{
    step: number;
    action: string;
    tool: string;
    result?: unknown;
    error?: string;
  }>;
  retrieved_context: SourceReference[];
  intermediate_data: Record<string, unknown>;
  verification_results: VerificationSummary | null;
  final_output: string | null;
  generated_files: string[];
  execution_trace: string[];
  retry_count: number;
  created_at: string;
  updated_at: string;
  task?: string;
  document_ids?: string[];
}

export interface DocumentUploadResponse {
  document_id: string;
  filename: string;
  file_size: number;
  content_type: string;
  storage_path: string;
  uploaded_at: string;
  status: string;
  pages?: number | null;
  text_extracted: boolean;
  ocr_pages: number[];
  source: string;
}

export interface DocumentMetadataResponse {
  document_id: string;
  filename: string;
  file_size: number;
  content_type: string;
  storage_path: string;
  uploaded_at: string;
  status: string;
  pages?: number | null;
  text_extracted: boolean;
  ocr_pages: number[];
  source: string;
}

export interface AuditLogEntry {
  id: string;
  timestamp: string;
  task_id?: string | null;
  action: string;
  component: string;
  status: string;
  duration_ms: number;
  details?: Record<string, unknown> | null;
  is_external: boolean;
}

export interface AuditLogResponse {
  logs: AuditLogEntry[];
  total: number;
}

export interface KnowledgeSearchResultItem {
  document: string;
  page?: number | null;
  content: string;
  score: number;
  metadata?: Record<string, unknown> | null;
}

export interface KnowledgeSearchResponse {
  query: string;
  results: KnowledgeSearchResultItem[];
}

export interface KnowledgeIngestResponse {
  status: string;
  documents_indexed: number;
  chunks_created: number;
  message: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatConversationRequest {
  messages: ChatMessage[];
  system_prompt?: string;
  auto_route?: boolean;
}

export interface ChatConversationResponse {
  reply: string;
  model: string;
  task_type?: string | null;
  duration_ms: number;
  usage: Record<string, number>;
}
