"use client";

import { useCallback, useRef, useState } from "react";

import { ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB } from "@/lib/config";
import { UploadIcon } from "@/components/ui/Icons";

interface UploadDropzoneProps {
  onFilesAdded: (files: File[]) => void;
  disabled?: boolean;
}

/** Drag-and-drop + click-to-browse area for staging documents (FR-1). */
export function UploadDropzone({ onFilesAdded, disabled }: UploadDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFiles = useCallback(
    (fileList: FileList | null) => {
      if (!fileList || fileList.length === 0) {
        return;
      }
      onFilesAdded(Array.from(fileList));
    },
    [onFilesAdded],
  );

  const onDrop = useCallback(
    (event: React.DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      setIsDragging(false);
      if (disabled) {
        return;
      }
      handleFiles(event.dataTransfer.files);
    },
    [disabled, handleFiles],
  );

  return (
    <div
      onDragOver={(event) => {
        event.preventDefault();
        if (!disabled) setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={onDrop}
      onClick={() => !disabled && inputRef.current?.click()}
      role="button"
      tabIndex={disabled ? -1 : 0}
      onKeyDown={(event) => {
        if ((event.key === "Enter" || event.key === " ") && !disabled) {
          event.preventDefault();
          inputRef.current?.click();
        }
      }}
      aria-disabled={disabled}
      className={[
        "flex cursor-pointer flex-col items-center justify-center gap-3 rounded-card border-2 border-dashed px-6 py-12 text-center transition-colors",
        disabled ? "cursor-not-allowed opacity-60" : "hover:border-accent/60 hover:bg-accent-faint/40",
        isDragging ? "border-accent bg-accent-faint/60" : "border-line-strong bg-canvas-raised",
      ].join(" ")}
    >
      <span className="flex h-12 w-12 items-center justify-center rounded-full bg-accent-faint text-accent">
        <UploadIcon className="h-6 w-6" />
      </span>
      <div>
        <p className="text-sm font-medium text-ink">
          Drag &amp; drop documents here, or{" "}
          <span className="text-accent">browse</span>
        </p>
        <p className="mt-1 text-xs text-ink-muted">
          {ALLOWED_EXTENSIONS.join(", ")} &middot; up to {MAX_FILE_SIZE_MB} MB each
        </p>
      </div>
      <input
        ref={inputRef}
        type="file"
        multiple
        accept={ALLOWED_EXTENSIONS.join(",")}
        className="hidden"
        disabled={disabled}
        onChange={(event) => {
          handleFiles(event.target.files);
          event.target.value = "";
        }}
      />
    </div>
  );
}
