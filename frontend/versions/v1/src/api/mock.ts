import type {
  InputType,
  QueryResponse,
  ReportPayload,
  UploadResponse,
  ValidationResult,
} from "./types";

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

const SAR_HINT = /sar|s1|sentinel-1|\bvh\b|\bvv\b/;
const GEO_TIFF = /\.tiff?$/i;

function guessInputType(fileCount: number, names: string[]): InputType {
  const joined = names.join(" ").toLowerCase();
  const hasSar = SAR_HINT.test(joined);

  if (fileCount >= 2) return hasSar ? "crossmodal_pair" : "bitemporal_pair";
  return hasSar ? "single_sar" : "single_optical";
}

function modalitiesFor(type: InputType, count: number): string[] {
  if (type === "single_optical") return ["optical"];
  if (type === "single_sar") return ["SAR"];
  if (type === "crossmodal_pair") {
    return Array.from({ length: count }, (_, i) => (i % 2 === 0 ? "optical" : "SAR"));
  }
  return Array.from({ length: count }, () => "optical");
}

type TaskPlan = {
  task: string;
  tools: string[];
  answer: string;
  confidence: number;
};

function planTask(query: string, inputType: InputType): TaskPlan {
  const q = query.toLowerCase();

  if (inputType === "bitemporal_pair" || /change|increased|decreased/.test(q)) {
    return {
      task: "change",
      tools: ["change"],
      confidence: 0.78,
      answer:
        "Between the dates, built-up expanded along the eastern edge (~+12%). A cleared patch appears southwest of the reservoir; vegetation decreased there.",
    };
  }
  if (inputType === "crossmodal_pair" || /sar|water|flood/.test(q)) {
    return {
      task: "fusion",
      tools: ["fusion"],
      confidence: 0.84,
      answer:
        "Optical + SAR fusion marks open water (dark SAR + blue/green optical) in the lower-left basin; built-up stays bright in both modalities.",
    };
  }
  if (/where|highlight|locate|bounding/.test(q)) {
    return {
      task: "grounding",
      tools: ["grounding"],
      confidence: 0.84,
      answer:
        "Water bodies sit in the northwest quadrant and along the central drainage channel. Boxes mark primary open-water extents.",
    };
  }
  if (/describe|caption|scene/.test(q)) {
    return {
      task: "caption",
      tools: ["captioning"],
      confidence: 0.84,
      answer:
        "Peri-urban mix: agricultural parcels, a meandering watercourse, and clustered rooftops along the corridor.",
    };
  }
  return {
    task: "vqa",
    tools: ["vqa"],
    confidence: 0.84,
    answer:
      "Built-up covers the central corridor, denser near the river bend; surrounding parcels look mostly vegetated.",
  };
}

function boxesFor(task: string) {
  if (task === "grounding" || task === "fusion") {
    return [
      { label: "water", x: 0.08, y: 0.12, w: 0.28, h: 0.22 },
      { label: "built-up", x: 0.42, y: 0.35, w: 0.34, h: 0.3 },
    ];
  }
  if (task === "change") {
    return [{ label: "new built-up", x: 0.55, y: 0.2, w: 0.3, h: 0.25 }];
  }
  return undefined;
}

export async function mockUpload(files: File[]): Promise<UploadResponse> {
  await delay(350);
  const names = files.map((f) => f.name);
  const input_type = guessInputType(files.length, names);
  const warnings: string[] = [];

  if (files.some((f) => GEO_TIFF.test(f.name))) {
    warnings.push("GeoTIFF preview is approximate until rasterio conversion lands.");
  }
  if (files.length >= 2) {
    warnings.push(`Mock validator: treating ${files.length} files as ${input_type}.`);
  }

  return {
    session_id: `mock-${Date.now()}`,
    validation: {
      input_type,
      modalities: modalitiesFor(input_type, files.length),
      compatible: true,
      warnings,
      preview_urls: files.map((f) => URL.createObjectURL(f)),
      file_count: files.length,
      filenames: names,
    },
  };
}

export async function mockQuery(
  query: string,
  validation: ValidationResult,
): Promise<QueryResponse> {
  await delay(500);
  const { task, tools, answer, confidence } = planTask(query, validation.input_type);

  return {
    answer,
    confidence,
    spatial: {
      boxes: boxesFor(task),
      overlay_note: "Mock spatial evidence — swap when real tools land",
    },
    evidence_image_url: validation.preview_urls[0] ?? null,
    trace: {
      task,
      input_type: validation.input_type,
      latency_ms: 520 + Math.floor(Math.random() * 180),
      tools_used: tools.map((tool) => ({
        tool,
        params: { query, file_count: validation.file_count ?? validation.preview_urls.length, mock: true },
        status: "ok" as const,
        summary: `Mock ${tool} completed`,
      })),
      notes: ["Frontend mock backend (VITE_USE_MOCK=true)."],
    },
  };
}

export function buildReportJson(payload: ReportPayload): Blob {
  return new Blob([JSON.stringify(payload, null, 2)], {
    type: "application/json",
  });
}

export function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.rel = "noopener";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
