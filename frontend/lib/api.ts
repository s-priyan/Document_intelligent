/**
 * Typed client for the Chat With Your Docs backend API.
 *
 * All endpoints are mounted under the `/api` prefix (see backend `main.py`).
 * The backend surfaces domain errors as `{ "detail": string }` bodies, which
 * this client normalises into a thrown {@link ApiError}.
 */

import { API_BASE_URL } from "./config";
import type {
  BulkUploadResponse,
  KnowledgeIndex,
  QueryResponse,
} from "./types";

/** Error thrown for any non-2xx API response, carrying the HTTP status. */
export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/** Extract a meaningful message from a failed response body. */
async function extractErrorMessage(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (body && typeof body.detail === "string") {
      return body.detail;
    }
    if (Array.isArray(body?.detail) && body.detail[0]?.msg) {
      return String(body.detail[0].msg);
    }
  } catch {
    // Body was not JSON; fall through to a generic message.
  }
  return `Request failed with status ${response.status}.`;
}

/** Perform a JSON request and parse the typed response, throwing on failure. */
async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: { Accept: "application/json", ...init?.headers },
    });
  } catch (cause) {
    throw new ApiError(
      "Cannot reach the server. Check that the backend is running.",
      0,
    );
  }

  if (!response.ok) {
    throw new ApiError(await extractErrorMessage(response), response.status);
  }
  return (await response.json()) as T;
}

/** Create a new, named knowledge index (FR-19). */
export function createKnowledgeIndex(name: string): Promise<KnowledgeIndex> {
  return requestJson<KnowledgeIndex>("/knowledge-indexes", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
}

/** List all existing knowledge indexes. */
export function listKnowledgeIndexes(): Promise<KnowledgeIndex[]> {
  return requestJson<KnowledgeIndex[]>("/knowledge-indexes");
}

/** Retrieve a single knowledge index by id. */
export function getKnowledgeIndex(indexId: string): Promise<KnowledgeIndex> {
  return requestJson<KnowledgeIndex>(
    `/knowledge-indexes/${encodeURIComponent(indexId)}`,
  );
}

/**
 * Bulk-upload documents into an index (FR-1 to FR-5). The backend stores raw
 * files, parses them with Docling, chunks and embeds them into the index's
 * Chroma store, reporting a per-file outcome.
 */
export function uploadDocuments(
  indexId: string,
  files: File[],
): Promise<BulkUploadResponse> {
  const form = new FormData();
  for (const file of files) {
    form.append("files", file, file.name);
  }
  return requestJson<BulkUploadResponse>(
    `/knowledge-indexes/${encodeURIComponent(indexId)}/documents`,
    { method: "POST", body: form },
  );
}

/** Ask a grounded question against an index within a conversation session (FR-8). */
export function queryKnowledgeIndex(
  indexId: string,
  question: string,
  sessionId: string | null,
): Promise<QueryResponse> {
  return requestJson<QueryResponse>(
    `/knowledge-indexes/${encodeURIComponent(indexId)}/query`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, session_id: sessionId }),
    },
  );
}
