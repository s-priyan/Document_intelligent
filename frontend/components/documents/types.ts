/** UI-only types for the document staging area (client-side only, FR-1/FR-2). */

export interface StagedFile {
  id: string;
  file: File;
  /** Client-side validation error, or null when the file is acceptable. */
  error: string | null;
}

/** Outcome of the create-index + ingestion flow (FR-6). */
export type CreateStatus = "idle" | "creating" | "uploading" | "done" | "error";
