# Results summary (2026-09-03)

All numbers are from scripts in `scripts/` and `training/`, run on the prescribed public test/val splits (sampled where noted) with no paid APIs.

## Remote-sensing adaptation (mandatory) — `adaptation.md`

CLIP ViT-B/32 + LoRA, trained on BigEarthNet patches (Sentinel-1 + Sentinel-2, ben-ge-8k) with land-cover labels and the BigEarthNet.txt captions joined to the same patches (7,890 rows).

| metric (held-out val) | before | after |
|---|---|---|
| zero-shot land-cover label top-1 | 0.693 | **0.906** |
| image → BigEarthNet.txt caption recall@1 | 0.017 | **0.066** |
| image → BigEarthNet.txt caption recall@5 | 0.071 | **0.237** |

## Single-image VQA — GeoChat-7B (4-bit), zero-shot

| benchmark | n | accuracy | file |
|---|---|---|---|
| RSVQA-LR test (presence / comparison / rural-urban) | 700 | **89.6%** (91.0 / 86.7 / 94.0) | `rsvqa_lr.md` |
| VRSBench val VQA, 12 question types equally sampled | 360 | **52.8%** (existence 93%, category 77%, quantity 27%) | `vrsbench.md` |
| BigEarthNet.txt QA (yes/no + multiple choice on CORINE area/adjacency/climate) | 300 | 40.0% (binary 54.7%, mcq 25.3%) | `bigearthnet_txt_qa.md` |

The BigEarthNet.txt questions ask about exact areas in m² and class adjacency of CORINE land-cover classes; a zero-shot VLM is near chance there, which is the obvious next fine-tuning target.

## Captioning — GeoChat-7B, zero-shot

VRSBench val, 60 images: BLEU-1 0.221, BLEU-4 0.014 (single reference). See `vrsbench.md`.

## Grounding — GeoChat-7B `[refer]`

Phrasing study in `grounding_phrasings.md`: "give me the location of X" returns boxes 7/7, "[grounding] highlight X" 3/7. A yes/no presence check runs first to avoid boxing absent objects.

## Change analysis — LEVIR-CC

Classical change map alone separates changed vs unchanged pairs at 68-70% (`scripts/eval_change_map.py`, 160 pairs), so the tool's verdict combines the map with GeoChat descriptions of both dates. Verified on sample pairs: no-change pair called correctly; "houses replaced trees" pair → "less vegetation, built-up increased".

## Optical + SAR fusion

Rule-based water/built-up mapping with sensor-agreement confidence, checked on real Sentinel-1/Sentinel-2 pairs (`scripts/check_fusion_real.py`): river traced correctly, terrain speckle reduced by despeckling; known weakness on mountainous scenes (radar shadow reads as water).

## Not run

CDVQA needs the SECOND dataset images (Google Drive); only its question JSON is on the GPU box. `scripts/` has no CDVQA runner yet.
