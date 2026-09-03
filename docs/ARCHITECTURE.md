# Architecture

## Flow

1. **Upload** → `backend/preprocessing/validator.py` classifies the input:
   single_optical | single_sar | bitemporal_pair | crossmodal_pair
2. **Query** → `backend/agent/controller.py`:
   - classifies the task from the query + input config
   - picks tool(s) from `backend/agent/registry.py`
   - runs them in order
3. **Tools** (`backend/tools/*`) each wrap one specialist model behind the
   shared `Tool` interface in `backend/tools/base.py`
4. **Reporting** (`backend/reporting/`) merges outputs, draws evidence,
   builds the execution trace and downloadable report
5. **API** (`backend/api/main.py`) exposes this to the frontend

## Rules we agreed on

- Controller never imports models directly — only through the registry.
- Every tool returns a `ToolResult` (text + optional spatial + confidence + metadata).
- Every query produces an execution trace (this is what judges evaluate).
- Big files never in git.

## Decisions made

- [x] Routing: LLM function-call first, keyword rules as fallback; input config (pair type) overrides keywords. Trace records which path fired. (Person 1)
- [x] Confidence: top-level score = minimum across tools used, see backend/agent/confidence.py. Weakest link sets the ceiling. (Person 1)
- [x] Input config names: canonical enum lives in controller.py CONFIG_ALIASES; if the validator emits different names, add an alias there, do not rename. (Person 1)
- [x] ToolResult contract unchanged from the skeleton: text/spatial/confidence/metadata. API maps text -> answer. (Person 1)

- [x] Modality detection: filename hints first, else band count + dtype (1-2 bands or non-uint8 = SAR). Reasons recorded in warnings. (Person 4)
- [x] Fusion v1: rule-based. Water = dark SAR AND NDWI>0, built-up = bright SAR minus vegetation minus water; confidence = sensor agreement on water. Upgrade path: fine-tuned CLIP tile classification. (Person 4)
- [x] Adaptation: LoRA on openai CLIP ViT-B/32, BigEarthNet subset streamed from HF (BIFOLD-BigEarthNetv2-0/BigEarthNet.txt), before/after zero-shot numbers in evaluation/results/adaptation.md. (Person 4)

- [x] Single-image VLM: GeoChat-7B 4-bit (RS-trained, does VQA + caption + grounding in one model), Qwen2-VL-2B as fallback. Runs on Colab behind a tunnel for now, the tools only talk to backend/tools/geochat_backend.py so moving it to the 5070 Ti is an env var. (Person 2)
- [x] Second single-image task is grounding, via GeoChat's [refer] tag phrased as "give me the location of X" ("where is X?" returns prose, verified on the 5070 Ti). Boxes come back as {<x1><y1><x2><y2>|<angle>} in 0-100, <delim> between boxes, and are converted to pixels in box_parser.py; angle is dropped. A yes/no VQA presence check runs first because [refer] boxes something even when the object is absent (seen on an airport image). Confidence is a fixed 0.7 because the model gives no score. (Person 2)
- [x] Single-image numbers: GeoChat-7B 4-bit zero-shot on RSVQA-LR test, 700 questions: presence 91.0%, comparison 86.7%, rural/urban 94.0%, overall 89.6% (paper fp16: 91.1/90.3/94.0). Grounding phrasing study over 6 templates in evaluation/results/grounding_phrasings.md; "give me the location of X" boxes 7/7, "[grounding] highlight X" 3/7. (Person 2)
- [x] Frontend: React + Vite (not Streamlit). Mock API until live `/upload` `/query` `/report`. Response contract matches below. (Person 5)

## API response shape (Person 5: confirm this works for you)

```json
{"answer": str, "spatial": dict|null, "confidence": float, "trace": {...}}
```

## Open decisions (fill in as we decide)

- [ ] Which change-VQA model

## Integration decisions (final day)

- Change tool: classical edge-difference map (WHERE) + GeoChat descriptions of both dates (WHAT). Verdict = map above 15.5% (cut-off from LEVIR-CC, scripts/eval_change_map.py) or a land-cover theme mentioned 2+ times more/less. Confidence 0.7 when map and descriptions agree, 0.5 otherwise. CDChat wrapper kept in backend/tools/change/tool.py for a later upgrade.
- API (backend/api/main.py) adapts the controller output to the React app's types: boxes normalised 0-1, masks rendered to evidence PNGs served from /files, trace as {task, input_type, tools_used[{tool, params, status, summary}], latency_ms, notes}.
- GeoChat runs on the GPU box only on demand (scripts/geochat_remote.sh start/stop) behind an ssh tunnel; nothing runs there permanently. No paid APIs, no local LLM; routing is rule-based.
- BigEarthNet.txt (the dataset named in the brief) is used two ways: its captions join the ben-ge-8k BigEarthNet patches (scripts/prepare_bigearthnet_txt.py) for CLIP fine-tuning, and its yes/no + multiple-choice questions score GeoChat (scripts/eval_bigearthnet_txt_qa.py).
