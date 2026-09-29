/**
 * Typed client for the Chat With Your Docs backend API.
 *
 * All endpoints are mounted under the `/api` prefix (see backend `main.py`).
 * The backend surfaces domain errors as `{ "detail": string }` bodies, which
 * this client normalises into a thrown {@link ApiError}.
 */

import { API_BASE_URL } from "./config";
import type {
  AudioChunk,
  BulkUploadResponse,
  Citation,
  HealthStatus,
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

/** Report service health and which optional features are configured (FR-21). */
export function getHealth(): Promise<HealthStatus> {
  return requestJson<HealthStatus>("/health");
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

/** Callbacks invoked as the streaming query endpoint publishes its events. */
export interface QueryStreamHandlers {
  onSession?: (sessionId: string) => void;
  onCitations?: (citations: Citation[]) => void;
  onDelta?: (text: string) => void;
  onDone?: (answer: string) => void;
  onAudio?: (audio: AudioChunk) => void;
}

/**
 * Ask a grounded question and consume the answer as server-sent events (FR-8).
 *
 * The browser `EventSource` API cannot issue a POST body, so the stream is read
 * off `fetch` manually. Resolves once the terminal `done` event arrives; a
 * transport failure, a non-2xx status or a terminal `error` event all surface as
 * a thrown {@link ApiError}.
 *
 * With `speak` set, the backend also emits an audio chunk per sentence. Speech
 * lags the text it belongs to, so `onAudio` can fire after `onDone`.
 */
export async function streamKnowledgeIndexQuery(
  indexId: string,
  question: string,
  sessionId: string | null,
  speak: boolean,
  handlers: QueryStreamHandlers,
): Promise<void> {
  let response: Response;
  try {
    response = await fetch(
      `${API_BASE_URL}/knowledge-indexes/${encodeURIComponent(indexId)}/query/stream`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
        },
        body: JSON.stringify({ question, session_id: sessionId, speak }),
      },
    );
  } catch {
    throw new ApiError(
      "Cannot reach the server. Check that the backend is running.",
      0,
    );
  }

  if (!response.ok || response.body === null) {
    throw new ApiError(await extractErrorMessage(response), response.status);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split(/\r\n\r\n|\n\n/);
    // The last element is an incomplete frame; keep it for the next chunk.
    buffer = frames.pop() ?? "";
    for (const frame of frames) {
      dispatchStreamFrame(frame, handlers);
    }
  }
}

/** Route one parsed SSE frame to its handler, ignoring keep-alives. */
function dispatchStreamFrame(frame: string, handlers: QueryStreamHandlers): void {
  let name = "message";
  const dataLines: string[] = [];

  for (const line of frame.split(/\r\n|\n/)) {
    if (line.startsWith("event:")) {
      name = line.slice("event:".length).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice("data:".length).trimStart());
    }
  }

  if (dataLines.length === 0) {
    return;
    // Comment-only frames (server pings) carry no payload.
  }

  const payload = JSON.parse(dataLines.join("\n"));
  switch (name) {
    case "session":
      handlers.onSession?.(payload.session_id as string);
      return;
    case "citations":
      handlers.onCitations?.(payload.citations as Citation[]);
      return;
    case "delta":
      handlers.onDelta?.(payload.text as string);
      return;
    case "done":
      handlers.onDone?.(payload.answer as string);
      return;
    case "audio":
      handlers.onAudio?.(payload as AudioChunk);
      return;
    case "error":
      // An in-band failure has no HTTP status of its own; 0 matches the
      // convention used for transport errors above.
      throw new ApiError(payload.detail as string, 0);
    default:
      return;
  }
}
