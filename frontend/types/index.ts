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
