import type { BoundingBox } from "../api/types";

type Props = {
  imageUrl: string | null;
  boxes?: BoundingBox[];
  note?: string;
};

export function EvidenceCanvas({ imageUrl, boxes = [], note }: Props) {
  if (!imageUrl) {
    return (
      <div className="evidence empty">
        <p>Evidence will appear here after a query.</p>
      </div>
    );
  }

  return (
    <div className="evidence">
      <div className="evidence-frame">
        <img src={imageUrl} alt="Query evidence" />
        {boxes.map((box) => (
          <div
            key={`${box.label}-${box.x}-${box.y}`}
            className="bbox"
            style={{
              left: `${box.x * 100}%`,
              top: `${box.y * 100}%`,
              width: `${box.w * 100}%`,
              height: `${box.h * 100}%`,
            }}
          >
            <span>{box.label}</span>
          </div>
        ))}
      </div>
      {note ? <p className="evidence-note">{note}</p> : null}
    </div>
  );
}
