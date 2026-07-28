/** Small presentation helpers shared across components. */

/** Render a byte count as a human-readable size (e.g. "2.4 MB"). */
export function formatFileSize(bytes: number): string {
  if (bytes <= 0) {
    return "0 B";
  }
  const units = ["B", "KB", "MB", "GB"];
  const exponent = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    units.length - 1,
  );
  const value = bytes / Math.pow(1024, exponent);
  const rounded = exponent === 0 ? value : Math.round(value * 10) / 10;
  return `${rounded} ${units[exponent]}`;
}

/** Format a citation into a short, human-readable label. */
export function formatCitationLabel(source: string, section: string | null): string {
  if (section && section.trim().length > 0) {
    return `${source} \u00b7 ${section}`;
  }
  return source;
}
