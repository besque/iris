export type InputType =
  | "single_optical"
  | "single_sar"
  | "bitemporal_pair"
  | "crossmodal_pair";

export type BoundingBox = {
  label: string;
  x: number;
  y: number;
  w: number;
  h: number;
};

export type SpatialResult = {
  boxes?: BoundingBox[];
  mask_url?: string | null;
  change_map_url?: string | null;
  overlay_note?: string;
};

export type TraceStep = {
  tool: string;
  params: Record<string, unknown>;
  status: "ok" | "skipped" | "error";
  summary?: string;
};

export type ExecutionTrace = {
  task: string;
  input_type: InputType;
  tools_used: TraceStep[];
  latency_ms?: number;
  notes?: string[];
};

export type ValidationResult = {
  input_type: InputType;
  modalities: string[];
  compatible: boolean;
  warnings: string[];
  preview_urls: string[];
  file_count?: number;
  filenames?: string[];
};

export type QueryResponse = {
  answer: string;
  spatial: SpatialResult | null;
  confidence: number | null;
  trace: ExecutionTrace;
  evidence_image_url?: string | null;
};

export type UploadResponse = {
  session_id: string;
  validation: ValidationResult;
};

export type ReportPayload = {
  query: string;
  answer: string;
  confidence: number | null;
  validation: ValidationResult;
  trace: ExecutionTrace;
  spatial: SpatialResult | null;
  generated_at: string;
};
