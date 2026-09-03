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

## Open decisions (fill in as we decide)

- [ ] Which base VLM to fine-tune (GeoChat? LLaVA + LoRA? …)
- [ ] Which change-VQA model
- [ ] Optical–SAR fusion approach
- [x] Frontend: React + Vite (not Streamlit). Mock API until Person 1 `handle_query()` is ready. Response contract: `answer`, `spatial`, `confidence`, `trace`.
- [ ] LLM used for the controller (API vs local)
