import type { ExecutionTrace } from "../api/types";

type Props = {
  trace: ExecutionTrace | null;
};

export function ExecutionTracePanel({ trace }: Props) {
  if (!trace) return null;

  return (
    <details className="trace" open>
      <summary>Task, tools, and parameters</summary>
      <dl className="trace-meta">
        <div>
          <dt>Task</dt>
          <dd>{trace.task}</dd>
        </div>
        <div>
          <dt>Input</dt>
          <dd>{trace.input_type}</dd>
        </div>
        {trace.latency_ms != null ? (
          <div>
            <dt>Latency</dt>
            <dd>{trace.latency_ms} ms</dd>
          </div>
        ) : null}
      </dl>

      <ol className="trace-steps">
        {trace.tools_used.map((step, i) => (
          <li key={`${step.tool}-${i}`}>
            <div className="step-head">
              <strong>{step.tool}</strong>
              <span>{step.status}</span>
            </div>
            {step.summary ? <p>{step.summary}</p> : null}
            <pre>{JSON.stringify(step.params, null, 2)}</pre>
          </li>
        ))}
      </ol>

      {trace.notes?.length ? (
        <ul className="trace-notes">
          {trace.notes.map((n) => (
            <li key={n}>{n}</li>
          ))}
        </ul>
      ) : null}
    </details>
  );
}
