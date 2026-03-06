export interface ApiErrorPayload {
  error?: string;
  details?: string;
  [key: string]: unknown;
}

export interface AuthenticatedUser {
  id: number;
  email: string;
  role: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  user: AuthenticatedUser;
}

export interface RegisterRequest {
  email: string;
  password: string;
}

export interface RegisterResponse {
  message: string;
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

export interface UploadAnomalyPayload {
  event_id: number;
  anomaly_type: string;
  severity: string;
  confidence: number;
  description: string;
}

export interface UploadParseErrorPayload {
  line_number: number;
  error: string;
  raw_line: string;
}

export interface UploadEventPreview {
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
  events_preview: UploadEventPreview[];
  summary: UploadSummaryPayload;
  anomalies: UploadAnomalyPayload[];
}
