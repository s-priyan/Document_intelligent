"use client";

/**
 * Load the list of existing knowledge indexes (GET /api/knowledge-indexes).
 * Exposes a `reload` action so callers can refresh after creating a new index.
 */

import { useCallback, useEffect, useState } from "react";

import { ApiError, listKnowledgeIndexes } from "./api";
import type { KnowledgeIndex } from "./types";

export interface UseKnowledgeIndexesResult {
  indexes: KnowledgeIndex[];
  isLoading: boolean;
  error: string | null;
  reload: () => Promise<void>;
}

export function useKnowledgeIndexes(): UseKnowledgeIndexesResult {
  const [indexes, setIndexes] = useState<KnowledgeIndex[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async (): Promise<void> => {
    setIsLoading(true);
    setError(null);
    try {
      setIndexes(await listKnowledgeIndexes());
    } catch (cause) {
      setError(
        cause instanceof ApiError ? cause.message : "Failed to load knowledge indexes.",
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { indexes, isLoading, error, reload };
}
