# Training / Fine-tuning

This folder covers the **mandatory remote-sensing adaptation** requirement.

Goal: adapt at least one vision or vision-language component using BigEarthNet
(co-registered Sentinel-1 SAR + Sentinel-2 multispectral + text annotations).

Suggested contents:
- `prepare_bigearthnet.py` — download/convert BigEarthNet into training format
- `finetune_clip.py` — adapt an image–text model (e.g. CLIP-style) on optical+SAR
- `finetune_vlm_lora.py` — LoRA fine-tune the VQA/captioning VLM on RS data
- `configs/` — training configs (yaml), so runs are reproducible
- Save checkpoints to `../models/` (gitignored) and log what data/config produced them.
