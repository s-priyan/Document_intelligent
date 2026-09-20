"use client";
import { useSyncExternalStore } from "react";
import { uploadDocuments } from "./api";
import type { BulkUploadResponse } from "./types";
interface IngestionJob { pending: boolean; result?: BulkUploadResponse; error?: string }
const jobs = new Map<string, IngestionJob>();
const listeners = new Set<() => void>();
function publish(id: string, job: IngestionJob) { jobs.set(id, job); listeners.forEach((listener) => listener()); }
export function startIngestion(id: string, files: File[]) {
  publish(id, { pending: true });
  void uploadDocuments(id, files).then(
    (result) => publish(id, { pending: false, result }),
    (error: unknown) => publish(id, { pending: false, error: error instanceof Error ? error.message : "Upload failed." }),
  );
}
export function useIngestion(id: string) {
  return useSyncExternalStore(
    (listener) => { listeners.add(listener); return () => { listeners.delete(listener); }; },
    () => jobs.get(id), () => undefined,
  );
}
