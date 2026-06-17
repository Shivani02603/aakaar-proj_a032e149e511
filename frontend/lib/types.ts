export interface Session {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
  user_id: string;
}

export interface UploadedFileResponse {
  id: string;
  filename: string;
  file_path: string;
  session_id: string;
  uploaded_at: string;
}

export interface Citation {
  text: string;
  source: string;
  page?: number;
  confidence: number;
}

export interface QueryResponse {
  answer: string;
  citations: Citation[];
  session_id: string;
  query: string;
}

export interface IngestResponse {
  message: string;
  session_id: string;
  file_ids: string[];
  chunks_created: number;
}