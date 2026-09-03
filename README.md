# SatQuery AI

An agentic vision-language assistant for satellite imagery. Ask questions in plain English about single images, optical–SAR pairs, or before/after image pairs — the system picks the right specialist model, runs it, and returns an answer with visual evidence.

## What it does

| Input | Tasks |
|---|---|
| Single image (optical or SAR) | VQA, captioning, region grounding |
| Bi-temporal pair (two dates) | Change description, change VQA |
| Optical + SAR pair (co-registered) | Joint analysis (built-up areas, water, etc.) |

## How it works (high level)

```
User query + images
      │
      ▼
[Input Validator]  ── checks format, modality, pair compatibility
      │
      ▼
[Agent Controller] ── classifies the task, picks tools from the registry
      │
      ▼
[Specialist Tools] ── VQA / caption / grounding / change / fusion models
      │
      ▼
[Output Combiner]  ── merges text + spatial outputs, confidence, evidence
      │
      ▼
Answer + visual evidence + execution summary + downloadable report
```

## Repo structure

```
satquery/
├── frontend/        # Web UI (upload images, type queries, see results)
├── backend/
│   ├── api/         # FastAPI server — endpoints the frontend calls
│   ├── agent/       # The "brain": query understanding, task routing, planning
│   ├── tools/       # Specialist model wrappers, one folder per task
│   │   ├── vqa/         # single-image visual question answering
│   │   ├── captioning/  # scene description
│   │   ├── grounding/   # "highlight the water body" → bounding box/mask
│   │   ├── change/      # bi-temporal change description / change VQA
│   │   └── fusion/      # optical + SAR joint analysis
│   ├── preprocessing/   # GeoTIFF reading, band handling, validation, co-registration checks
│   └── reporting/       # evidence overlays, confidence, execution trace, PDF/JSON reports
├── training/        # Fine-tuning scripts (BigEarthNet adaptation) — the mandatory RS adaptation
├── evaluation/      # Benchmark eval: VRSBench, RSVQA, CDVQA
├── data/            # Datasets (gitignored — download scripts live in scripts/)
├── models/          # Model checkpoints (gitignored)
├── scripts/         # Dataset download, setup, demo helpers
├── notebooks/       # Experiments and exploration
├── docs/            # Architecture decisions, meeting notes, references
└── tests/           # Unit tests
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Team workflow

- Work on feature branches, PR into `main`.
- Each tool in `backend/tools/` follows the same interface (`backend/tools/base.py`) so they plug into the agent registry without touching the controller.
- Big files (datasets, checkpoints) never go in git — put download scripts in `scripts/` instead.
