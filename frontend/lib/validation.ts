/** Client-side upload validation mirroring the backend rules (FR-2). */

import {
  ALLOWED_EXTENSIONS,
  MAX_FILE_SIZE_BYTES,
  MAX_FILE_SIZE_MB,
} from "./config";

/** Return the lowercased file extension including the leading dot, or "". */
export function getExtension(filename: string): string {
  const dot = filename.lastIndexOf(".");
  return dot === -1 ? "" : filename.slice(dot).toLowerCase();
}

/**
 * Validate a file's type and size against backend constraints.
 * Returns a human-readable error message, or null when the file is valid.
 */
export function validateFile(file: File): string | null {
  const extension = getExtension(file.name);
  if (!ALLOWED_EXTENSIONS.includes(extension as (typeof ALLOWED_EXTENSIONS)[number])) {
    return `Unsupported type. Allowed: ${ALLOWED_EXTENSIONS.join(", ")}.`;
  }
  if (file.size === 0) {
    return "File is empty.";
  }
  if (file.size > MAX_FILE_SIZE_BYTES) {
    return `Exceeds the ${MAX_FILE_SIZE_MB} MB limit.`;
  }
  return null;
}
