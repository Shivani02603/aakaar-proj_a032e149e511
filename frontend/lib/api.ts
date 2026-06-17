import { Session, UploadedFileResponse, QueryResponse, IngestResponse } from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API error (${response.status}): ${errorText}`);
  }
  return response.json();
}

// Sessions
export async function createSession(name: string): Promise<Session> {
  const response = await fetch(`${API_BASE}/api/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  });
  return handleResponse<Session>(response);
}

export async function listSessions(): Promise<Session[]> {
  const response = await fetch(`${API_BASE}/api/sessions`);
  return handleResponse<Session[]>(response);
}

export async function getSession(sessionId: string): Promise<Session> {
  const response = await fetch(`${API_BASE}/api/sessions/${sessionId}`);
  return handleResponse<Session>(response);
}

// Files
export async function uploadFile(sessionId: string, file: File): Promise<UploadedFileResponse> {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(`${API_BASE}/api/sessions/${sessionId}/files`, {
    method: 'POST',
    body: formData,
  });
  return handleResponse<UploadedFileResponse>(response);
}

// AI
export async function ingestDocuments(sessionId: string, fileIds: string[]): Promise<IngestResponse> {
  const response = await fetch(`${API_BASE}/api/ai/ingest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, file_ids: fileIds }),
  });
  return handleResponse<IngestResponse>(response);
}

export async function aiQuery(sessionId: string, query: string): Promise<QueryResponse> {
  const response = await fetch(`${API_BASE}/api/ai/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, query }),
  });
  return handleResponse<QueryResponse>(response);
}