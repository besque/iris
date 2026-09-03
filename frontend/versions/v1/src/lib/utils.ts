/** Shared frontend limits / labels — keep upload + mock in sync. */
export const MAX_UPLOAD_FILES = 4;

export const IMAGE_ACCEPT = ".tif,.tiff,.png,.jpg,.jpeg,image/*";

export const EXAMPLE_QUERIES = [
  "What changed between these two dates?",
  "Has built-up area increased, decreased, or stayed the same?",
  "Where is the water body in this scene?",
  "Use optical and SAR to identify built-up and water regions.",
  "Describe this satellite scene.",
] as const;

export function previewLabel(index: number): string {
  return `Image ${String.fromCharCode(65 + index)}`;
}

export function errMessage(err: unknown, fallback: string): string {
  return err instanceof Error ? err.message : fallback;
}

export function takeUploadFiles(list: FileList | null, max = MAX_UPLOAD_FILES): File[] {
  if (!list?.length) return [];
  return Array.from(list).slice(0, max);
}

export function revokeUrls(urls: string[] | undefined) {
  urls?.forEach((url) => URL.revokeObjectURL(url));
}
