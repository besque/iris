import { useEffect, useRef, useState } from "react";
import { downloadReport, isMockMode, runQuery, uploadImages } from "./api/client";
import type { QueryResponse, ValidationResult } from "./api/types";
import { QueryPanel } from "./components/QueryPanel";
import { ResultsPanel } from "./components/ResultsPanel";
import { UploadPanel } from "./components/UploadPanel";
import { ValidationStrip } from "./components/ValidationStrip";
import { errMessage, revokeUrls } from "./lib/utils";

type Busy = "idle" | "upload" | "query" | "download";

const CAPABILITIES = [
  {
    title: "Ask any scene",
    body: "Single-image VQA, captions, and grounding over optical or SAR inputs.",
  },
  {
    title: "See what changed",
    body: "Bi-temporal pairs answer where built-up, water, or vegetation shifted.",
  },
  {
    title: "Fuse optical + SAR",
    body: "Combine cloud-piercing radar with optical context when weather blocks a view.",
  },
  {
    title: "Trace every step",
    body: "Judges and operators see which models ran, with evidence and a downloadable report.",
  },
] as const;

const WORKFLOW = [
  {
    id: "upload",
    step: "01",
    title: "Upload imagery",
    body: "Drop 1–4 GeoTIFF, PNG, or JPEG scenes — single shot, two dates, or optical + SAR.",
  },
  {
    id: "validate",
    step: "02",
    title: "Validate inputs",
    body: "The preprocessor detects modality and pair type, then flags anything incompatible.",
  },
  {
    id: "ask",
    step: "03",
    title: "Ask in English",
    body: "Type a plain-language question. The agent controller picks the right specialist tools.",
  },
  {
    id: "evidence",
    step: "04",
    title: "Review evidence",
    body: "Get a text answer, confidence, highlighted overlays, and the full execution log.",
  },
  {
    id: "report",
    step: "05",
    title: "Download report",
    body: "Export JSON with query, answer, spatial evidence, confidence, and model trace.",
  },
] as const;

function scrollToId(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
}

export default function App() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [busy, setBusy] = useState<Busy>("idle");
  const [error, setError] = useState<string | null>(null);
  const [studioPulse, setStudioPulse] = useState(false);
  const previewRef = useRef<string[]>([]);
  const uploadAnchorRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    return () => revokeUrls(previewRef.current);
  }, []);

  function openStudio() {
    scrollToId("studio");
    setStudioPulse(true);
    window.setTimeout(() => setStudioPulse(false), 1600);
    window.setTimeout(() => {
      uploadAnchorRef.current?.focus({ preventScroll: true });
    }, 450);
  }

  function openWorkflow() {
    scrollToId("workflow");
  }

  const activeWorkflow =
    result != null
      ? "report"
      : busy === "query"
        ? "ask"
        : validation
          ? "ask"
          : busy === "upload"
            ? "upload"
            : "upload";

  async function handleFiles(files: File[]) {
    setError(null);
    setResult(null);
    setBusy("upload");
    try {
      const res = await uploadImages(files);
      revokeUrls(previewRef.current);
      previewRef.current = res.validation.preview_urls;
      setSessionId(res.session_id);
      setValidation(res.validation);
    } catch (err) {
      setError(errMessage(err, "Upload failed"));
    } finally {
      setBusy("idle");
    }
  }

  function clearUploads() {
    revokeUrls(previewRef.current);
    previewRef.current = [];
    setSessionId(null);
    setValidation(null);
    setResult(null);
    setError(null);
  }

  async function handleQuery() {
    if (!sessionId || !validation || !query.trim()) return;
    setError(null);
    setBusy("query");
    try {
      setResult(await runQuery(sessionId, query.trim(), validation));
    } catch (err) {
      setError(errMessage(err, "Query failed"));
    } finally {
      setBusy("idle");
    }
  }

  async function handleDownload() {
    if (!result || !validation) return;
    setBusy("download");
    try {
      await downloadReport({
        query,
        answer: result.answer,
        confidence: result.confidence,
        validation,
        trace: result.trace,
        spatial: result.spatial,
        generated_at: new Date().toISOString(),
      });
    } catch (err) {
      setError(errMessage(err, "Report download failed"));
    } finally {
      setBusy("idle");
    }
  }

  return (
    <div className="app">
      <header className="nav">
        <a className="logo" href="#top">
          iridis
        </a>
        <nav className="nav-links" aria-label="Primary">
          <a href="#capabilities">Capabilities</a>
          <a href="#workflow">Workflow</a>
          <a href="#studio">Studio</a>
        </nav>
        <div className="nav-actions">
          <span className="nav-status">{isMockMode ? "Mock mode" : "Live API"}</span>
          <button type="button" className="btn ghost" onClick={openWorkflow}>
            Workflow
          </button>
          <button type="button" className="btn accent" onClick={openStudio}>
            Open studio
          </button>
        </div>
      </header>

      <section className="hero" id="top">
        <div className="hero-media" aria-hidden="true">
          <img src="/earth-hero.jpg" alt="" />
          <div className="hero-shade" />
        </div>
        <div className="hero-grid">
          <div className="hero-copy">
            <p className="hero-brand">iridis</p>
            <h1>
              Turning satellite data
              <br />
              into clear answers
            </h1>
            <p className="hero-sub">
              An agentic vision studio for Earth observation. Upload scenes, ask in
              plain English, and receive evidence-backed answers—not just another map
              layer.
            </p>
            <div className="hero-ctas">
              <button type="button" className="btn accent" onClick={openStudio}>
                Enter the studio
              </button>
              <button type="button" className="btn ghost" onClick={openWorkflow}>
                See the workflow
              </button>
            </div>
            <p className="hero-cta-hint">
              <span>Enter the studio</span> jumps to the live tool ·{" "}
              <span>See the workflow</span> explains each step first
            </p>
          </div>
          <aside className="hero-card">
            <p className="hero-card-label">Built for decision-makers</p>
            <ul>
              <li>No GIS scripting required</li>
              <li>Optical, SAR, and change pairs</li>
              <li>Confidence + model execution log</li>
              <li>Downloadable evidence report</li>
            </ul>
          </aside>
        </div>
      </section>

      <section className="capabilities" id="capabilities">
        <div className="section-inner">
          <div className="section-head">
            <p className="eyebrow">What you can do</p>
            <h2>
              One studio.
              <span> Many specialists.</span>
            </h2>
            <p>
              iridis routes each question to the right remote-sensing tool, then
              returns one clear answer with proof.
            </p>
          </div>
          <div className="cap-grid">
            {CAPABILITIES.map((item) => (
              <article key={item.title} className="cap">
                <h3>{item.title}</h3>
                <p>{item.body}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="workflow" id="workflow">
        <div className="section-inner">
          <div className="section-head">
            <p className="eyebrow">How it works</p>
            <h2>The agent workflow</h2>
            <p>
              Five steps from raw imagery to a downloadable report. Use this map
              before you jump into the studio.
            </p>
          </div>

          <ol className="flow-track">
            {WORKFLOW.map((item, index) => (
              <li key={item.id} className="flow-step">
                <div className="flow-index">
                  <span>{item.step}</span>
                  {index < WORKFLOW.length - 1 ? <i aria-hidden="true" /> : null}
                </div>
                <div className="flow-body">
                  <h3>{item.title}</h3>
                  <p>{item.body}</p>
                </div>
              </li>
            ))}
          </ol>

          <div className="workflow-cta">
            <button type="button" className="btn accent" onClick={openStudio}>
              Continue to studio
            </button>
            <p>You’ll land on imagery upload — step 01 of the flow.</p>
          </div>
        </div>
      </section>

      <main className={`studio ${studioPulse ? "pulse" : ""}`} id="studio">
        <div className="section-inner">
          <div className="section-head studio-head">
            <p className="eyebrow">EO studio</p>
            <h2>Explore. Ask. Prove.</h2>
            <p>
              Live workspace for the workflow above. Progress updates as you upload,
              ask, and download.
            </p>
          </div>

          <div className="studio-progress" aria-label="Current workflow stage">
            {WORKFLOW.map((item) => {
              const done =
                (item.id === "upload" && !!validation) ||
                (item.id === "validate" && !!validation) ||
                (item.id === "ask" && !!result) ||
                (item.id === "evidence" && !!result) ||
                (item.id === "report" && !!result && busy !== "download");
              const current =
                item.id === activeWorkflow ||
                (item.id === "validate" && !!validation && !result && busy !== "query") ||
                (item.id === "evidence" && !!result);
              return (
                <div
                  key={item.id}
                  className={`progress-pill ${done ? "done" : ""} ${current ? "current" : ""}`}
                >
                  <span>{item.step}</span>
                  {item.title}
                </div>
              );
            })}
          </div>

          {error ? (
            <div className="banner error" role="alert">
              {error}
            </div>
          ) : null}

          <div className="grid">
            <div className="col left">
              <div ref={uploadAnchorRef} tabIndex={-1} className="upload-anchor">
                <UploadPanel
                  previews={validation?.preview_urls ?? []}
                  filenames={validation?.filenames}
                  busy={busy === "upload"}
                  onFiles={handleFiles}
                  onClear={clearUploads}
                />
              </div>
              <ValidationStrip validation={validation} />
              <QueryPanel
                query={query}
                disabled={!validation}
                busy={busy === "query" || busy === "upload"}
                onChange={setQuery}
                onSubmit={handleQuery}
              />
            </div>
            <div className="col right">
              <ResultsPanel
                result={result}
                onDownload={handleDownload}
                downloading={busy === "download"}
              />
            </div>
          </div>
        </div>
      </main>

      <footer className="foot">
        <div className="foot-brand">
          <strong>iridis</strong>
          <span>Satellite vision agent</span>
        </div>
        <span>Answer · evidence · confidence · execution log</span>
      </footer>
    </div>
  );
}
