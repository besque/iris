# iridis AI

An agentic vision-language assistant for satellite imagery. Ask questions in plain English about single images, optical–SAR pairs, or before/after image pairs — the system picks the right specialist model, runs it, and returns an answer with visual evidence, a confidence score, an execution trace, and a downloadable report.

## What it does

| Input | Tasks | Engine |
|---|---|---|
| Single image (optical or SAR) | VQA, captioning, region grounding | GeoChat-7B (remote-sensing VLM, 4-bit) |
| Bi-temporal pair (two dates) | Change description, change VQA, change map | edge-difference map + GeoChat on both dates |
| Optical + SAR pair (co-registered) | Water and built-up mapping | SAR/optical rules + CLIP fine-tuned on BigEarthNet |

## How it works

```
User query + images
      │
      ▼
[Input Validator]  ── reads GeoTIFF/PNG, detects optical vs SAR, checks pair compatibility
      │
      ▼
[Agent Controller] ── classifies the task, picks tools from the fixed registry
      │
      ▼
[Specialist Tools] ── vqa / caption / grounding / change / fusion
      │
      ▼
[API + Reporting]  ── draws evidence, aggregates confidence (weakest tool), builds the trace
      │
      ▼
Answer + evidence image + execution summary + JSON report
```

## Running the demo

Needs: a laptop with Python 3.10+ and Node 18+ (macOS, Linux, or Windows via Git Bash), plus a free Colab GPU for the model.

```bash
scripts/run_demo.sh        # first run also sets up the venv and frontend packages
open http://127.0.0.1:5173
scripts/run_demo.sh stop
```

The model server is a Colab notebook. If `run_demo.sh` says the model is **not reachable**, the Colab runtime has restarted: open `notebooks/geochat_colab.ipynb` in Colab (Runtime → T4 GPU), run section 1 then section 2, copy the `https://....trycloudflare.com` URL it prints, and paste it into `COLAB_URL` at the top of `scripts/run_demo.sh`. Keep the Colab tab open while demoing. Without a reachable model the app still runs, but only the fusion tool and the change map answer. To use your own GPU machine instead, see `scripts/geochat_remote.sh`.

Useful checks:

```bash
PYTHONPATH=. .venv/bin/python -m pytest tests/ -q
PYTHONPATH=. .venv/bin/python scripts/run_controller_demo.py       # five example queries through the controller
PYTHONPATH=. .venv/bin/python scripts/test_fusion.py               # optical + SAR on a synthetic pair
```

## Remote-sensing adaptation (mandatory)

Needs the GPU extras: `pip install -r requirements-train.txt`. `training/finetune_clip.py` LoRA-tunes CLIP ViT-B/32 on BigEarthNet patches (Sentinel-1 + Sentinel-2 via ben-ge-8k) with land-cover labels, then on the BigEarthNet.txt captions joined to the same patches. Numbers live in `evaluation/results/adaptation.md`. Data prep: `scripts/prepare_bigearthnet.py`, `scripts/prepare_bigearthnet_txt.py`.

## Evaluation

`evaluation/results/` holds the benchmark runs: RSVQA-LR (`rsvqa_lr.md`), VRSBench VQA + captioning (`vrsbench.md`), BigEarthNet.txt QA (`bigearthnet_txt_qa.md`), grounding phrasing study, change-map separation on LEVIR-CC (`scripts/eval_change_map.py`).

## Repo structure

```
├── frontend/            # React + Vite web app
├── backend/
│   ├── api/             # FastAPI: /upload, /query, /report, /files
│   ├── agent/           # controller (routing), registry, confidence
│   ├── tools/           # one folder per task, all implement tools/base.py
│   ├── preprocessing/   # validator + GeoTIFF/SAR to RGB
│   └── reporting/       # evidence overlays
├── training/            # fine-tuning scripts
├── evaluation/results/  # benchmark numbers
├── scripts/             # data prep, evals, demo helpers, remote model control
├── docs/                # ARCHITECTURE.md (decisions), RESEARCH.md (background)
├── team_tasks/          # per-person briefs used during the build
└── tests/
```

## Team conventions

- Each tool follows `backend/tools/base.py` (`Tool`, `ToolResult`) and is registered in `backend/agent/registry.py`.
- Datasets and checkpoints are gitignored; download scripts live in `scripts/`.
- Every decision gets a line in `docs/ARCHITECTURE.md`.
