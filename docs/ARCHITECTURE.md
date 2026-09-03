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

- [x] Frontend: React + Vite (not Streamlit). Mock API until live `/upload` `/query` `/report`. Response contract matches below. (Person 5)

## API response shape (Person 5: confirm this works for you)

```json
{"answer": str, "spatial": dict|null, "confidence": float, "trace": {...}}
```

## Open decisions (fill in as we decide)

- [ ] Which base VLM to fine-tune (GeoChat? LLaVA + LoRA? …)
- [ ] Which change-VQA model
- [ ] Person 2: captioning or grounding as the second single-image task? (mocks exist for both)
