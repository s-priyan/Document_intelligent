"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useMemo, useState } from "react";

import {
  AlertIcon,
  CheckIcon,
  SparkleIcon,
  SpinnerIcon,
} from "@/components/ui/Icons";
import { ApiError, createKnowledgeIndex, uploadDocuments } from "@/lib/api";
import { useKnowledgeIndexes } from "@/lib/useKnowledgeIndexes";
import { validateFile } from "@/lib/validation";
import type { BulkUploadResponse } from "@/lib/types";
import { KnowledgeIndexSelector } from "./KnowledgeIndexSelector";
import { StagedFileList } from "./StagedFileList";
import { UploadDropzone } from "./UploadDropzone";
import type { CreateStatus, StagedFile } from "./types";

function createId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

/**
 * Screen 1: build a knowledge index by staging documents client-side, then
 * creating the index and ingesting the files in one action (FR-1/FR-2/FR-6).
 */
export function DocumentManager() {
  const router = useRouter();
  const {
    indexes,
    isLoading: indexesLoading,
    error: indexesError,
    reload: reloadIndexes,
  } = useKnowledgeIndexes();

  const [name, setName] = useState("");
  const [staged, setStaged] = useState<StagedFile[]>([]);
  const [status, setStatus] = useState<CreateStatus>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [result, setResult] = useState<BulkUploadResponse | null>(null);
  const [createdIndexId, setCreatedIndexId] = useState<string | null>(null);
  const [selectedExistingId, setSelectedExistingId] = useState<string | null>(null);

  const validFiles = useMemo(
    () => staged.filter((entry) => entry.error === null),
    [staged],
  );
  const isBusy = status === "creating" || status === "uploading";
  const canSubmit = name.trim().length > 0 && validFiles.length > 0 && !isBusy;

  const addFiles = useCallback((files: File[]) => {
    setStaged((prev) => {
      const existing = new Set(prev.map((entry) => `${entry.file.name}:${entry.file.size}`));
      const additions = files
        .filter((file) => !existing.has(`${file.name}:${file.size}`))
        .map<StagedFile>((file) => ({ id: createId(), file, error: validateFile(file) }));
      return [...prev, ...additions];
    });
  }, []);

  const removeFile = useCallback((id: string) => {
    setStaged((prev) => prev.filter((entry) => entry.id !== id));
  }, []);

  const handleCreate = useCallback(async () => {
    if (!canSubmit) {
      return;
    }
    setErrorMessage(null);
    setResult(null);
    setCreatedIndexId(null);

    try {
      setStatus("creating");
      const index = await createKnowledgeIndex(name.trim());

      setStatus("uploading");
      const uploadResult = await uploadDocuments(
        index.id,
        validFiles.map((entry) => entry.file),
      );

      setResult(uploadResult);
      setCreatedIndexId(index.id);
      setStatus(uploadResult.ingested > 0 ? "done" : "error");
      if (uploadResult.ingested === 0) {
        setErrorMessage("No documents could be ingested. Review the errors below.");
      } else {
        void reloadIndexes();
      }
    } catch (error) {
      setStatus("error");
      setErrorMessage(
        error instanceof ApiError
          ? error.message
          : "Failed to create the knowledge index.",
      );
    }
  }, [canSubmit, name, validFiles, reloadIndexes]);

  const resetForm = useCallback(() => {
    setName("");
    setStaged([]);
    setStatus("idle");
    setErrorMessage(null);
    setResult(null);
    setCreatedIndexId(null);
  }, []);

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col gap-6">
      <header className="flex flex-col gap-2 text-center">
        <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-accent-faint text-accent">
          <SparkleIcon className="h-6 w-6" />
        </span>
        <h1 className="text-2xl font-semibold text-ink">Chat With Your Docs</h1>
        <p className="text-sm text-ink-muted">
          Upload your documents, build a knowledge index, and start a conversation.
        </p>
      </header>

      <section className="surface flex flex-col gap-5 p-6">
        <div className="flex flex-col gap-1.5">
          <label htmlFor="index-name" className="text-sm font-medium text-ink-soft">
            Knowledge index name
          </label>
          <input
            id="index-name"
            type="text"
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="e.g. Product Handbook"
            disabled={isBusy}
            maxLength={100}
            className="w-full rounded-xl border border-line bg-canvas px-4 py-2.5 text-sm text-ink placeholder:text-ink-faint focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/30 disabled:opacity-60"
          />
        </div>

        <UploadDropzone onFilesAdded={addFiles} disabled={isBusy} />

        <StagedFileList files={staged} onRemove={removeFile} disabled={isBusy} />

        {errorMessage ? (
          <p className="flex items-start gap-2 rounded-xl bg-danger/5 px-3 py-2.5 text-sm text-danger">
            <AlertIcon className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{errorMessage}</span>
          </p>
        ) : null}

        {result ? <IngestionSummary result={result} /> : null}

        {status === "done" && createdIndexId ? (
          <div className="flex flex-col gap-3 sm:flex-row">
            <Link
              href={`/chat/${encodeURIComponent(createdIndexId)}`}
              className="btn-primary flex-1"
            >
              <SparkleIcon className="h-4 w-4" />
              Talk with document
            </Link>
            <button type="button" onClick={resetForm} className="btn-ghost">
              Start over
            </button>
          </div>
        ) : (
          <button
            type="button"
            onClick={handleCreate}
            disabled={!canSubmit}
            className="btn-primary w-full"
          >
            {isBusy ? (
              <>
                <SpinnerIcon className="h-4 w-4" />
                {status === "creating" ? "Creating index\u2026" : "Ingesting documents\u2026"}
              </>
            ) : (
              "Create Knowledge Index"
            )}
          </button>
        )}
      </section>

      <div className="flex items-center gap-3" aria-hidden>
        <span className="h-px flex-1 bg-line" />
        <span className="text-xs font-medium uppercase tracking-wide text-ink-faint">or</span>
        <span className="h-px flex-1 bg-line" />
      </div>

      <section className="surface flex flex-col gap-4 p-6">
        <div className="flex flex-col gap-1">
          <h2 className="text-sm font-semibold text-ink">Chat with an existing index</h2>
          <p className="text-xs text-ink-muted">
            Pick a knowledge index you have already created and start a conversation.
          </p>
        </div>

        <KnowledgeIndexSelector
          indexes={indexes}
          isLoading={indexesLoading}
          error={indexesError}
          selectedId={selectedExistingId}
          onSelect={setSelectedExistingId}
        />

        <button
          type="button"
          onClick={() => {
            if (selectedExistingId) {
              router.push(`/chat/${encodeURIComponent(selectedExistingId)}`);
            }
          }}
          disabled={!selectedExistingId}
          className="btn-primary w-full"
        >
          <SparkleIcon className="h-4 w-4" />
          Talk with document
        </button>
      </section>
    </div>
  );
}

/** Per-file ingestion outcome after upload (FR-6). */
function IngestionSummary({ result }: { result: BulkUploadResponse }) {
  return (
    <div className="flex flex-col gap-2 rounded-xl border border-line bg-canvas px-4 py-3">
      <p className="text-sm font-medium text-ink-soft">
        {result.ingested} of {result.total} document(s) ingested
      </p>
      <ul className="flex flex-col gap-1.5">
        {result.results.map((item) => {
          const ok = item.status === "ingested";
          return (
            <li key={item.filename} className="flex items-center gap-2 text-sm">
              <span className={ok ? "text-success" : "text-danger"}>
                {ok ? <CheckIcon className="h-4 w-4" /> : <AlertIcon className="h-4 w-4" />}
              </span>
              <span className="truncate text-ink">{item.filename}</span>
              <span className="ml-auto shrink-0 text-xs text-ink-muted">
                {ok
                  ? `${item.chunk_count ?? 0} chunks`
                  : (item.error ?? "failed")}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
