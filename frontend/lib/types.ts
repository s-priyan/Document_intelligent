/**
 * Shared TypeScript types mirroring the backend Pydantic schemas.
 * Keep these in sync with `backend/app/schemas/*`.
 */

export interface KnowledgeIndex {
  id: string;
  name: string;
  created_at: string;
  document_count: number;
}

export type DocumentStatus = "ingested" | "failed";

export interface DocumentResult {
  filename: string;
  status: DocumentStatus;
  size_bytes: number | null;
  stored_path: string | null;
  parsed_path: string | null;
  chunk_count: number | null;
  error: string | null;
}

export interface BulkUploadResponse {
  index_id: string;
  total: number;
  ingested: number;
  failed: number;
  results: DocumentResult[];
}

export interface Citation {
  source: string;
  section: string | null;
  start_index: number | null;
  snippet: string | null;
}

export interface QueryRequest {
  question: string;
  session_id?: string | null;
}

export interface QueryResponse {
  answer: string;
  citations: Citation[];
  session_id: string;
}

export type ChatRole = "user" | "assistant";

/** A single rendered turn in the chat thread. */
export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  citations?: Citation[];
  /** True while an assistant turn is awaiting its response. */
  pending?: boolean;
  /** True when the turn failed to produce an answer. */
  error?: boolean;
}
