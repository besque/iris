# Evaluation

Benchmark scripts against the prescribed public test splits.

| Benchmark | What it tests | Task |
|---|---|---|
| RSVQA | single-image VQA | mandatory baseline |
| VRSBench | captioning, grounding, VQA | second single-image task |
| CDVQA | change-based VQA on bi-temporal pairs | change analysis |

Suggested contents:
- `eval_rsvqa.py`, `eval_vrsbench.py`, `eval_cdvqa.py`
- `metrics.py` — shared metrics (accuracy, BLEU/CIDEr for captions, IoU for grounding)
- `results/` — saved scores per model version, so we can track progress

Note: final judging also uses a hidden ISRO/SAC set (Cartosat-2S optical +
RISAT SAR pairs), so make eval scripts work on generic folder inputs, not
hardcoded to one dataset layout.
