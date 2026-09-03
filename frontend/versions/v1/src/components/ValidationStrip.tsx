import type { ValidationResult } from "../api/types";

const TYPE_LABEL: Record<ValidationResult["input_type"], string> = {
  single_optical: "Single optical",
  single_sar: "Single SAR",
  bitemporal_pair: "Bi-temporal pair",
  crossmodal_pair: "Optical–SAR pair",
};

type Props = {
  validation: ValidationResult | null;
};

export function ValidationStrip({ validation }: Props) {
  if (!validation) return null;

  const count = validation.file_count ?? validation.preview_urls.length;

  return (
    <div className="validation" role="status">
      <p>
        <strong>{TYPE_LABEL[validation.input_type]}</strong>
        <span>
          {" "}
          · {validation.modalities.join(", ")}
          {count ? ` · ${count} file${count === 1 ? "" : "s"}` : ""}
          {validation.compatible ? " · compatible" : ""}
        </span>
      </p>
      {validation.warnings.length > 0 ? (
        <ul>
          {validation.warnings.map((w) => (
            <li key={w}>{w}</li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
