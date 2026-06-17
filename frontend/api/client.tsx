import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';

// Base URL for API requests
const baseURL = process.env.NEXT_PUBLIC_API_URL || '';

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add JWT token
api.interceptors.request.use(
  (config) => {
    // Only run in browser environment
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle 401 errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login
      if (typeof window !== 'undefined') {
        localStorage.removeItem('token');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// TypeScript interfaces for API requests and responses

// Session related interfaces
export interface SessionCreateRequest {
  name: string;
  description?: string;
}

export interface SessionResponse {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
  user_id: string;
}

export interface SessionListResponse {
  sessions: SessionResponse[];
  total: number;
}

// File upload related interfaces
export interface FileUploadRequest {
  file: File;
}

export interface UploadedFileResponse {
  id: string;
  filename: string;
  file_path: string;
  file_size: number;
  mime_type: string;
  session_id: string;
  user_id: string;
  created_at: string;
  updated_at: string;
}

// AI related interfaces
export interface IngestRequest {
  session_id: string;
  file_ids: string[];
}

export interface IngestResponse {
  message: string;
  ingested_count: number;
  session_id: string;
}

export interface QueryRequest {
  session_id: string;
  query: string;
}

export interface SourceCitation {
  id: string;
  content: string;
  file_name: string;
  page_number?: number;
  similarity_score: number;
}

export interface QueryResponse {
  answer: string;
  citations: SourceCitation[];
  session_id: string;
  query_id: string;
}

// Auth related interfaces
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    name: string;
  };
}

// User related interfaces
export interface UserResponse {
  id: string;
  email: string;
  name: string;
  created_at: string;
  updated_at: string;
}

export interface UserUpdateRequest {
  name?: string;
  email?: string;
  password?: string;
}

// API functions

// Auth endpoints
export const login = async (data: LoginRequest): Promise<AuthResponse> => {
  const response: AxiosResponse<AuthResponse> = await api.post('/api/auth/login', data);
  return response.data;
};

export const register = async (data: RegisterRequest): Promise<AuthResponse> => {
  const response: AxiosResponse<AuthResponse> = await api.post('/api/auth/register', data);
  return response.data;
};

export const getCurrentUser = async (): Promise<UserResponse> => {
  const response: AxiosResponse<UserResponse> = await api.get('/api/auth/me');
  return response.data;
};

// Session endpoints
export const createSession = async (data: SessionCreateRequest): Promise<SessionResponse> => {
  const response: AxiosResponse<SessionResponse> = await api.post('/api/sessions', data);
  return response.data;
};

export const listSessions = async (): Promise<SessionListResponse> => {
  const response: AxiosResponse<SessionListResponse> = await api.get('/api/sessions');
  return response.data;
};

export const getSession = async (sessionId: string): Promise<SessionResponse> => {
  const response: AxiosResponse<SessionResponse> = await api.get(`/api/sessions/${sessionId}`);
  return response.data;
};

// File upload endpoints
export const uploadFile = async (
  sessionId: string,
  file: File
): Promise<UploadedFileResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response: AxiosResponse<UploadedFileResponse> = await api.post(
    `/api/sessions/${sessionId}/files`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );
  return response.data;
};

// AI endpoints
export const ingestDocuments = async (data: IngestRequest): Promise<IngestResponse> => {
  const response: AxiosResponse<IngestResponse> = await api.post('/api/ai/ingest', data);
  return response.data;
};

export const aiQuery = async (data: QueryRequest): Promise<QueryResponse> => {
  const response: AxiosResponse<QueryResponse> = await api.post('/api/ai/query', data);
  return response.data;
};

// Utility function to set token after login
export const setAuthToken = (token: string): void => {
  if (typeof window !== 'undefined') {
    localStorage.setItem('token', token);
  }
};

// Utility function to remove token on logout
export const removeAuthToken = (): void => {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('token');
  }
};

// Utility function to check if user is authenticated
export const isAuthenticated = (): boolean => {
  if (typeof window !== 'undefined') {
    return !!localStorage.getItem('token');
  }
  return false;
};

export default api;