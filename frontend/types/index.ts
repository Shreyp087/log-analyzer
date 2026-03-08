export interface ApiErrorPayload {
  error?: string;
  details?: string;
  [key: string]: unknown;
}

export interface AuthenticatedUser {
  id: string;
  username: string;
  name: string;
  role: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  access_token: string;
  user: AuthenticatedUser;
}

export interface RegisterRequest {
  name: string;
  username: string;
  password: string;
  role: "SOC Analyst" | "Security Admin" | "Threat Hunter" | "IR Analyst";
}

export interface RegisterResponse {
  token: string;
  access_token: string;
  user: AuthenticatedUser;
}

export interface AuthSession {
  token: string;
  user: AuthenticatedUser;
}

export interface CountValuePair {
  value: string;
  count: number;
}

export interface UploadSummaryPayload {
  total_events: number;
  total_anomalies: number;
  blocked_events: number;
  allowed_events: number;
  unique_ips: number;
  top_categories: CountValuePair[];
  top_destinations: CountValuePair[];
  top_source_ips: CountValuePair[];
}

export interface AiExecutiveSummaryPayload {
  riskLevel: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | string;
  executiveSummary: string;
  keyFindings: string[];
  recommendations: string[];
  immediateActions: string[];
}

export interface DetectionNoteSummaryEntry {
  what: string;
  why: string;
}

export interface DetectionNotesSummaryPayload {
  overview: string;
  entries: DetectionNoteSummaryEntry[];
  source?: "openai" | "fallback" | string;
}

export interface UploadAnomalyPayload {
  event_row?: number;
  event_id?: number;
  anomaly_type?: string;
  type?: string;
  severity: string;
  confidence: number;
  description?: string;
  explanation?: string;
  affectedLines?: number[];
  detectionMethod?: string;
}

export interface UploadParseErrorPayload {
  line_number: number;
  error: string;
  raw_line: string;
}

export interface UploadEventPreview {
  lineNumber?: number;
  raw?: string | null;
  sourceIp?: string | null;
  user?: string | null;
  url?: string | null;
  threat?: string | null;
  severity?: string | null;
  isAnomalous?: boolean;
  anomalies?: UploadAnomalyPayload[];
  event_time: string | null;
  username: string | null;
  source_ip: string | null;
  destination: string | null;
  action: string | null;
  category: string | null;
  bytes_transferred: number | null;
}

export interface UploadResponse {
  upload_id: number;
  filename: string;
  stored_file: string;
  status: string;
  events_saved: number;
  anomalies_detected: number;
  parse_errors_count: number;
  parse_errors: UploadParseErrorPayload[];
  detection_notes?: string[];
  detection_notes_summary?: DetectionNotesSummaryPayload;
  events_preview: UploadEventPreview[];
  summary: UploadSummaryPayload;
  ai_summary?: AiExecutiveSummaryPayload;
  anomalies: UploadAnomalyPayload[];
}
