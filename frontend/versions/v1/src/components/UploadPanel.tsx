import { useId, useState, type DragEvent } from "react";
import { IMAGE_ACCEPT, MAX_UPLOAD_FILES, previewLabel, takeUploadFiles } from "../lib/utils";

type Props = {
  previews: string[];
  filenames?: string[];
  busy: boolean;
  onFiles: (files: File[]) => void;
  onClear: () => void;
};

export function UploadPanel({ previews, filenames, busy, onFiles, onClear }: Props) {
  const inputId = useId();
  const [dragging, setDragging] = useState(false);

  function accept(list: FileList | null) {
    const files = takeUploadFiles(list);
    if (files.length) onFiles(files);
  }

  return (
    <section className="panel">
      <header className="panel-head">
        <h3>Imagery</h3>
        <p>Up to {MAX_UPLOAD_FILES} files · GeoTIFF, PNG, or JPEG</p>
      </header>

      <label
        htmlFor={inputId}
        className={`dropzone ${dragging ? "dragging" : ""} ${busy ? "busy" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e: DragEvent) => {
          e.preventDefault();
          setDragging(false);
          accept(e.dataTransfer.files);
        }}
      >
        <input
          id={inputId}
          type="file"
          accept={IMAGE_ACCEPT}
          multiple
          disabled={busy}
          onChange={(e) => {
            accept(e.target.files);
            e.target.value = "";
          }}
        />
        <strong>{busy ? "Validating…" : "Drop imagery here"}</strong>
        <span>or browse files</span>
      </label>

      {previews.length > 0 ? (
        <div className="preview-row">
          {previews.map((url, i) => (
            <figure key={url} className="preview">
              <img src={url} alt={filenames?.[i] ?? previewLabel(i)} />
              <figcaption title={filenames?.[i]}>
                {previewLabel(i)}
                {filenames?.[i] ? ` · ${filenames[i]}` : ""}
              </figcaption>
            </figure>
          ))}
          <button type="button" className="btn ghost sm" onClick={onClear} disabled={busy}>
            Clear
          </button>
        </div>
      ) : null}
    </section>
  );
}
