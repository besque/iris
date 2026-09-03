import { useEffect, useRef, useState } from "react";
import { downloadReport, isMockMode, runQuery, uploadImages } from "./api/client";
import type { QueryResponse, ValidationResult } from "./api/types";
import { QueryPanel } from "./components/QueryPanel";
import { ResultsPanel } from "./components/ResultsPanel";
import { UploadPanel } from "./components/UploadPanel";
import { ValidationStrip } from "./components/ValidationStrip";
import { errMessage, revokeUrls } from "./lib/utils";

type Busy = "idle" | "upload" | "query" | "download";

const YOU_CAN = [
  {
    title: "Upload your own scenes",
    body: "Optical, SAR, or mixed pairs — no archive login required for the demo.",
  },
  {
    title: "Extract answers with proof",
    body: "Text answer, confidence, and highlighted regions on the imagery.",
  },
  {
    title: "Route specialist models",
    body: "The agent picks VQA, change, grounding, or fusion tools automatically.",
  },
  {
    title: "Keep a full audit trail",
    body: "Every run logs task, tools, params, and outputs for judging and review.",
  },
] as const;

const APART = [
  {
    title: "Browser-native",
    body: "No install. Open the studio, upload, and ask — API-ready when the backend lands.",
  },
  {
    title: "Multi-sensor ready",
    body: "Single image, bi-temporal change, and optical–SAR fusion in one flow.",
  },
  {
    title: "Agent, not a single model",
    body: "A controller routes questions to the right remote-sensing specialist.",
  },
  {
    title: "Transparent by design",
    body: "Execution summary and downloadable report are first-class outputs.",
  },
] as const;

const WORKFLOW = [
  {
    id: "upload",
    step: "01",
    title: "Upload imagery",
    body: "Drop 1–4 GeoTIFF, PNG, or JPEG scenes.",
  },
  {
    id: "validate",
    step: "02",
    title: "Validate inputs",
    body: "Detect modality and pair compatibility.",
  },
  {
    id: "ask",
    step: "03",
    title: "Ask in English",
    body: "The controller selects the right tools.",
  },
  {
    id: "evidence",
    step: "04",
    title: "Review evidence",
    body: "Answer, overlays, confidence, and trace.",
  },
  {
    id: "report",
    step: "05",
    title: "Download report",
    body: "Export JSON for demos and judging.",
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
    result != null ? "report" : busy === "query" || validation ? "ask" : "upload";

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
          <a href="#apart">Why iridis</a>
          <a href="#workflow">Workflow</a>
          <a href="#studio">Studio</a>
        </nav>
        <div className="nav-actions">
          <span className="nav-status">{isMockMode ? "Mock mode" : "Live API"}</span>
          <button type="button" className="btn ghost" onClick={openWorkflow}>
            See workflow
          </button>
          <button type="button" className="btn accent" onClick={openStudio}>
            Open studio
          </button>
        </div>
      </header>

      {/* Hero — Aurora-style centered pitch */}
      <section className="hero" id="top">
        <div className="hero-media" aria-hidden="true">
          <img src="/earth-hero.jpg" alt="" />
          <div className="hero-shade" />
        </div>
        <div className="hero-center">
          <p className="kicker">Earth observation studio</p>
          <h1>
            iridis: turning satellite data
            <br />
            into real answers
          </h1>
          <p className="hero-sub">
            A no-code agent that bridges complex imagery and confident decisions —
            ask in plain English, get evidence, confidence, and a full model log.
          </p>
          <div className="hero-ctas">
            <button type="button" className="btn accent lg" onClick={openStudio}>
              Enter the studio
            </button>
            <button type="button" className="btn ghost lg" onClick={openWorkflow}>
              See the workflow
            </button>
          </div>
        </div>
      </section>

      {/* Split headline band */}
      <section className="band band-split">
        <div className="section-inner narrow">
          <h2>
            <span className="line-soft">Endless questions.</span>
            <span className="line-hard">One agent.</span>
          </h2>
          <p>
            iridis brings optical, SAR, and change analysis behind a single natural-language
            interface — so district officers and scientists can get answers without GIS
            scripting.
          </p>
          <button type="button" className="btn ghost" onClick={openStudio}>
            Enquire in the studio
          </button>
        </div>
      </section>

      {/* With iridis, you can */}
      <section className="capabilities" id="capabilities">
        <div className="section-inner">
          <div className="section-head center">
            <h2>With iridis, you can</h2>
          </div>
          <div className="you-can-grid">
            {YOU_CAN.map((item, i) => (
              <article key={item.title} className="you-can">
                <span className="you-can-num">{String(i + 1).padStart(2, "0")}</span>
                <h3>{item.title}</h3>
                <p>{item.body}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* Dive in CTA */}
      <section className="band band-cta">
        <div className="section-inner narrow center">
          <h2>
            Dive into the
            <br />
            iridis experience
          </h2>
          <p>No install. Browser-only. Mock backend ready until the API is live.</p>
          <button type="button" className="btn accent lg" onClick={openStudio}>
            Start in the studio
          </button>
        </div>
      </section>

      {/* What sets us apart */}
      <section className="apart" id="apart">
        <div className="section-inner">
          <div className="section-head center">
            <h2>What sets iridis apart</h2>
          </div>
          <div className="apart-grid">
            {APART.map((item) => (
              <article key={item.title} className="apart-card">
                <h3>{item.title}</h3>
                <p>{item.body}</p>
              </article>
            ))}
          </div>
          <div className="apart-actions">
            <button type="button" className="btn ghost" onClick={openWorkflow}>
              Request the walkthrough
            </button>
          </div>
        </div>
      </section>

      {/* Workflow */}
      <section className="workflow" id="workflow">
        <div className="section-inner">
          <div className="section-head center">
            <p className="eyebrow">See what you can do</p>
            <h2>Explore → ask → prove → report</h2>
            <p>A clear path from raw scenes to a judge-ready execution log.</p>
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
          <div className="workflow-cta center">
            <button type="button" className="btn accent lg" onClick={openStudio}>
              Continue to studio
            </button>
          </div>
        </div>
      </section>

      {/* Studio */}
      <main className={`studio ${studioPulse ? "pulse" : ""}`} id="studio">
        <div className="section-inner">
          <div className="section-head studio-head">
            <p className="eyebrow">Live studio</p>
            <h2>Transform how you work with satellite data</h2>
            <p>
              Upload imagery, ask a question, and leave with answer, evidence, confidence,
              and a downloadable report.
            </p>
          </div>

          <div className="studio-progress" aria-label="Current workflow stage">
            {WORKFLOW.map((item) => {
              const done =
                (item.id === "upload" && !!validation) ||
                (item.id === "validate" && !!validation) ||
                (item.id === "ask" && !!result) ||
                (item.id === "evidence" && !!result) ||
                (item.id === "report" && !!result);
              const current =
                item.id === activeWorkflow ||
                (item.id === "validate" && !!validation && !result) ||
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

      <section className="band band-footer">
        <div className="section-inner narrow center">
          <h2>
            See what others miss.
            <br />
            Act when it matters.
          </h2>
          <button type="button" className="btn accent lg" onClick={openStudio}>
            Get in touch with the imagery
          </button>
        </div>
      </section>

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
