import { EXAMPLE_QUERIES } from "../lib/utils";

type Props = {
  query: string;
  disabled: boolean;
  busy: boolean;
  onChange: (value: string) => void;
  onSubmit: () => void;
};

export function QueryPanel({ query, disabled, busy, onChange, onSubmit }: Props) {
  return (
    <section className={`panel ${disabled ? "dim" : ""}`}>
      <header className="panel-head">
        <h3>Query</h3>
        <p>Ask in plain English about the validated imagery.</p>
      </header>

      <div className="examples">
        {EXAMPLE_QUERIES.map((ex) => (
          <button
            key={ex}
            type="button"
            className={`chip ${query === ex ? "on" : ""}`}
            disabled={disabled || busy}
            onClick={() => onChange(ex)}
          >
            {ex}
          </button>
        ))}
      </div>

      <textarea
        value={query}
        onChange={(e) => onChange(e.target.value)}
        placeholder={disabled ? "Upload imagery first" : "Which areas are underwater?"}
        rows={4}
        disabled={disabled || busy}
        onKeyDown={(e) => {
          if (
            e.key === "Enter" &&
            (e.metaKey || e.ctrlKey) &&
            !disabled &&
            !busy &&
            query.trim()
          ) {
            onSubmit();
          }
        }}
      />

      <div className="row">
        <span className="hint">Ctrl / ⌘ + Enter</span>
        <button
          type="button"
          className="btn solid"
          disabled={disabled || busy || !query.trim()}
          onClick={onSubmit}
        >
          {busy ? "Running…" : "Run query"}
        </button>
      </div>
    </section>
  );
}
