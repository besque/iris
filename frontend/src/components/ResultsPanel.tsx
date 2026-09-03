import type { QueryResponse } from "../api/types";
import { EvidenceCanvas } from "./EvidenceCanvas";
import { ExecutionTracePanel } from "./ExecutionTrace";

type Props = {
  result: QueryResponse | null;
  onDownload: () => void;
  downloading: boolean;
};

export function ResultsPanel({ result, onDownload, downloading }: Props) {
  if (!result) {
    return (
      <section className="panel results">
        <header className="panel-head">
          <h3>Results</h3>
          <p>Answer, evidence, confidence, execution log, and report.</p>
        </header>
        <div className="empty">
          Upload imagery and run a query to see output here.
        </div>
      </section>
    );
  }

  const confidence =
    result.confidence == null ? "—" : `${Math.round(result.confidence * 100)}%`;

  return (
    <section className="panel results">
      <header className="panel-head split">
        <div>
          <h3>Results</h3>
          <p>Answer, evidence, confidence, execution log, and report.</p>
        </div>
        <button
          type="button"
          className="btn solid"
          onClick={onDownload}
          disabled={downloading}
        >
          {downloading ? "Preparing…" : "Download report"}
        </button>
      </header>

      <div className="result-block">
        <h4>Answer</h4>
        <p className="confidence">Confidence {confidence}</p>
        <p className="answer">{result.answer}</p>
      </div>

      <div className="result-block">
        <h4>Visual evidence</h4>
        <EvidenceCanvas
          imageUrl={result.evidence_image_url ?? null}
          boxes={result.spatial?.boxes}
          note={result.spatial?.overlay_note}
        />
      </div>

      <div className="result-block">
        <h4>Execution summary</h4>
        <ExecutionTracePanel trace={result.trace} />
      </div>

      <div className="result-block">
        <h4>Report</h4>
        <p className="muted">
          JSON with query, answer, confidence, spatial evidence, and full trace.
        </p>
        <button
          type="button"
          className="btn solid"
          onClick={onDownload}
          disabled={downloading}
        >
          {downloading ? "Preparing…" : "Download report"}
        </button>
      </div>
    </section>
  );
}
