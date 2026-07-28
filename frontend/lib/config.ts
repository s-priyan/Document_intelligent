/** Client-side runtime configuration derived from public environment variables. */

const DEFAULT_API_BASE_URL = "http://localhost:8000/api";

/** Base URL of the backend API, including the `/api` prefix, without a trailing slash. */
export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE_URL
).replace(/\/+$/, "");

/**
 * Upload constraints mirrored from the backend validator (FR-2).
 * Kept in sync with `backend/app/core/config.py`.
 */
export const ALLOWED_EXTENSIONS = [".pdf", ".docx", ".txt", ".md"] as const;
export const MAX_FILE_SIZE_MB = 100;
export const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;
