# iridis AI: presenter's guide

Everything you need to explain, demo and defend the project. Numbers are from `evaluation/results/`.

## 1. The one-minute pitch

Satellite images answer real questions: which villages are flooded, how far a city has grown, where forest was cleared. Today only trained analysts with GIS software can extract those answers. iridis AI is a web assistant where a non-expert uploads one or two satellite images, asks a question in plain English, and gets a grounded answer: text, the evidence drawn on the image, a confidence score, and an auditable log of exactly which model ran with which parameters.

The novelty asked for by the brief is agentic orchestration: instead of one generic vision-language model, a controller inspects the query and the uploaded imagery, picks the right specialist from a fixed registry, runs it, combines outputs and reports the trace. Single-image tasks are the baseline; the focus is paired imagery: two dates (change) and optical + SAR (fusion).

## 2. Architecture

```
upload -> Validator -> Controller -> Specialist tool(s) -> Reporting -> API -> React app
```

Components and where they live:

| Layer | File(s) | What it does |
|---|---|---|
| Validator | `backend/preprocessing/validator.py` | Reads GeoTIFF/TIFF/PNG/JPEG with rasterio and PIL; detects optical vs SAR; checks pair compatibility; classifies input into `single_optical`, `single_sar`, `bitemporal_pair`, `crossmodal_pair`; converts anything to RGB for the models |
| Controller | `backend/agent/controller.py` | Task classification and routing, execution trace, response assembly |
| Registry | `backend/agent/registry.py` | The fixed menu of 5 tools the controller may pick from (the brief requires a predefined registry) |
| Tool contract | `backend/tools/base.py` | Every tool implements `run(images, query, **params) -> ToolResult(text, spatial, confidence, metadata)` |
| 5 specialist tools | `backend/tools/{vqa,captioning,grounding,change,fusion}/` | See section 4 |
| Model backend | `backend/tools/geochat_backend.py` | One place that talks to the VLM: over HTTP to Colab, or locally. Reads model name and box coordinate scale from the server's `/health` |
| Confidence | `backend/agent/confidence.py` | Top-level confidence = minimum over tools used (weakest link) |
| Reporting | `backend/reporting/overlay.py` | Draws boxes and masks onto the evidence image |
| API | `backend/api/main.py` | FastAPI: `POST /upload`, `POST /query`, `POST /report`, static `/files` for previews and evidence |
| Web app | `frontend/` | React 19 + Vite + TypeScript: upload panel, validation strip, query panel, results, evidence canvas, execution trace, JSON report download |

### The controller in detail

1. Normalises the validator's input type (alias table, so a renamed validator output cannot silently break routing).
2. Routes. Input configuration wins over wording: two dates always go to `change`, optical + SAR always to `fusion`. For a single image, keywords decide: highlight / locate / where is / mark -> `grounding`; describe / caption / scene / overview -> `caption`; otherwise `vqa`.
3. There is a hook for an LLM router (function calling) with the rules as fallback. It is switched off: no paid APIs were used anywhere, and with five well separated tasks the rules are exact and predictable. Be honest about this: the routing is deterministic, not a planning LLM.
4. Checks the chosen tool accepts this input type, runs it, records the trace.

Trace recorded for every query: query, task selected, input configuration, routing method, tools used with parameters, per-tool outputs, latency, validator notes (for example "sar (filename hint)"). The frontend renders it under every answer. The brief says only the observable trace is evaluated; this is it.

## 3. Models

| Role | Model | Details |
|---|---|---|
| Single-image VLM used for the benchmarks | GeoChat-7B (MBZUAI) | LLaVA-1.5 architecture: CLIP ViT-L/14-336 vision encoder, MLP projector, Vicuna-7B LLM. Instruction-tuned on 318k remote-sensing image-text pairs. Supports VQA, captioning and referring/grounding with a `[refer]` tag that outputs boxes. Loaded in 4-bit (bitsandbytes) to fit a 16 GB GPU |
| Single-image VLM in the live demo | Qwen2-VL-2B-Instruct | Fallback when GeoChat's 2023 code would not import on Colab's current Python/transformers. Not remote-sensing adapted. Grounding is prompted to emit `<|box_start|>(x1,y1),(x2,y2)<|box_end|>` in 0-1000 coordinates |
| Remote-sensing adapted encoder (mandatory) | CLIP ViT-B/32 + LoRA | Our fine-tune, see section 5 |
| Change: where | Classical edge-difference map | No model, see section 4 |
| Fusion | Physical rules on SAR backscatter and optical indices | No model at run time; the fine-tuned CLIP is the planned upgrade for tile classification |

Serving: the VLM runs on a free Colab T4 behind a Flask server (`/health`, `/answer`) exposed through a Cloudflare quick tunnel. `notebooks/geochat_colab.ipynb` does this. `scripts/run_demo.sh` starts API + web app on the laptop and points at the tunnel URL. Nothing is paid and nothing runs permanently on any machine.

## 4. The five specialist tools

**VQA (`GeoChatVQA`).** Sends the question and image to the VLM. Confidence is a fixed 0.7 because the model returns no probability; the trace says `confidence_source: fixed` rather than pretending.

**Captioning (`GeoChatCaption`).** Same backend, prompt "Describe the land cover and the major objects visible in this satellite image."

**Grounding (`GeoChatGrounding`).** Two-step: first a yes/no presence question ("Is there a water body in this image?") because the model boxes something for any request, even when the object is absent; then the referring prompt. Phrasing study on GeoChat: "give me the location of X" returned boxes 7/7, "[grounding] highlight X" only 3/7 (`evaluation/results/grounding_phrasings.md`). Box parser handles GeoChat's `{<x1><y1><x2><y2>|<angle>}` in 0-100 and Qwen's `(x1,y1),(x2,y2)` in 0-1000; scale is read from the server. Answer text states where the region is ("1 region in the west of the image").

**Change analysis (`ChangeTool`).** Two layers.
- Where: classical change map (`change_map.py`). Both images to grayscale, Gaussian blur, brightness/contrast normalisation of the second image to the first (so a sunnier day is not change), gradient magnitude (edges react to new structures, not to seasonal colour), absolute difference, Otsu threshold with a floor, median filter to remove speckle. Outputs a mask, percent changed and the 3x3 grid cell where change concentrates.
- Whether and what: the map decides whether there is change (cut-off 15.5 percent of pixels, the balanced value found on 160 LEVIR-CC test pairs; the map alone separates changed from unchanged pairs at about 68 to 70 percent). Only if the map says yes, the VLM is shown both dates side by side in one image and asked what changed. Why this split: in testing, the 2B model reported a change for every pair, even when instructed to say "No real change", so a model cannot be the judge; a pixel map cannot hallucinate.
- Confidence 0.7 when the map is clearly above or below the cut-off, 0.6 when borderline. Verdict for "increased / decreased / unchanged" parsed from the answer.
- A CDChat wrapper (a dedicated bi-temporal VLM) exists in `backend/tools/change/tool.py` as the upgrade path; it needs a 14 GB download and fine-tuning that did not fit in the day.

**Optical + SAR fusion (`FusionTool`).** Physics-based, transparent:
- Water: SAR backscatter in the darkest 15 percent (smooth water reflects radar away) AND optical NDWI > 0 (NDWI = (Green - NIR)/(Green + NIR); needs a NIR band, Sentinel-2 B08).
- Built-up: SAR in the brightest 15 percent (corner reflections) AND not vegetation (NDVI <= 0.4) AND not water.
- Despeckle both masks with median filters (3 for water so thin rivers survive, 5 for built-up).
- Confidence = 0.4 + 0.6 x agreement, where agreement is the IoU of the SAR-water and optical-water masks. Two sensors agreeing raises confidence; disagreement lowers it. This is a measured number.
- Handles SAR stored either in linear power or already in dB (detected from sign). Verified on real Sentinel-1/Sentinel-2 pairs from BigEarthNet: a river is traced correctly. Known weakness: mountainous scenes, where radar shadow reads as water and bright slopes as built-up.

## 5. Remote-sensing adaptation (the mandatory fine-tune)

Model: OpenAI CLIP ViT-B/32, LoRA (rank 16, alpha 32, dropout 0.1) on the q, k, v and output projections of both towers. About 2.0M trainable parameters out of 153M (1.3 percent). Contrastive image-text loss. 3 epochs, batch 32, learning rate 1e-4. Trained on an RTX 5070 Ti (16 GB), minutes per run.

Data (7,890 training rows):
- BigEarthNet patches via ben-ge-8k (Zenodo): Sentinel-2 (RGB from B04/B03/B02, 2-98 percentile stretch) and Sentinel-1 VV (dB) GeoTIFFs of the same 8,000 locations. Text = land-cover classes covering more than 10 percent of the patch, prompts "a satellite image of ..." and "a SAR satellite image of ...". So the model learns both modalities.
- BigEarthNet.txt (the dataset named in the brief, HuggingFace BIFOLD-BigEarthNetv2-0/BigEarthNet.txt): its captions joined onto the same patches. v2 patch ids are v1 ids with a tile segment inserted (`S2A_..._20170613T101031_N9999_R022_T33UUP_26_57`), so a regex join maps them. Its yes/no and multiple-choice questions became an extra evaluation set.

Results on held-out validation data (`evaluation/results/adaptation.md`):

| metric | before | after |
|---|---|---|
| zero-shot land-cover label top-1 | 0.693 | 0.906 |
| image -> BigEarthNet.txt caption recall@1 | 0.017 | 0.066 |
| image -> BigEarthNet.txt caption recall@5 | 0.071 | 0.237 |

A first stage on labels alone reached 0.848; adding the BigEarthNet.txt captions lifted it to 0.906 and tripled caption retrieval. Honest note: this encoder is not wired into a live tool yet; it is the designed upgrade for the fusion tool (classify tiles as water / urban / other and merge with the physical masks).

## 6. Benchmarks

| Benchmark | Model | n | Result |
|---|---|---|---|
| RSVQA-LR test | GeoChat-7B 4-bit, zero-shot | 700 | 89.6 percent (presence 91.0, comparison 86.7, rural/urban 94.0). Paper fp16: 91.1 / 90.3 / 94.0 |
| VRSBench val VQA | GeoChat-7B | 360, 12 types equally sampled | 52.8 percent (existence 93.3, category 76.7, rural/urban 73.3, quantity 26.7, shape 30.0) |
| VRSBench captioning | GeoChat-7B | 60 | BLEU-1 0.221, BLEU-4 0.014 (single reference) |
| BigEarthNet.txt QA | GeoChat-7B | 300 (150 yes/no, 150 MCQ) | 40.0 percent (binary 54.7, MCQ 25.3). Questions ask exact areas in m2 and CORINE class adjacency; a zero-shot VLM is near chance, which motivates fine-tuning the VLM on this data next |
| LEVIR-CC change map | classical map | 160 pairs | 68 to 70 percent changed-vs-unchanged separation, cut-off 15.5 percent |
| CDVQA | not run | | Only the question JSON was available; the SECOND images (Google Drive) were not downloaded |

## 7. Datasets used

- BigEarthNet (Sentinel-1 + Sentinel-2 patches) via ben-ge-8k, 1.8 GB.
- BigEarthNet.txt annotations (captions, binary, MCQ, bounding-box questions).
- LEVIR-CC: 10,077 bi-temporal 256x256 pairs with 5 change captions each (2,135 test) for change-tool development and demo pairs.
- VRSBench val (12.5 GB total; sampled 360 VQA + 60 captions).
- RSVQA-LR test.
- Demo inputs in `data/samples/`: LEVIR pairs, a VRSBench lake image, a real Sentinel-2 4-band + Sentinel-1 VV GeoTIFF pair.

## 8. Team and process

Five people, one day, roles: agent controller and integration; single-image VLM tools; change analysis; validator, fine-tuning and fusion; frontend. Contracts fixed in hour one: the `Tool`/`ToolResult` interface and the API response shape. Everyone built against mocks first (five mock tools, a mock API), so nobody was blocked; real tools replaced mocks one import line at a time. Zero paid services.

## 9. Demo script

Files in `data/samples/`.
1. `levir_test_000191_B.png`: "Describe the land-cover and major objects visible in this image." (caption)
2. same image: "How many roads are visible?" (vqa)
3. `lake_town.png`: "Highlight the water body" (grounding, box on the lake)
4. `levir_test_000191_A.png` + `_B.png`: "Has the built-up area increased, decreased, or remained unchanged?" (change, red mask, "increased")
5. `levir_test_000003_A.png` + `_B.png`: "What changed between these two dates?" (change, correctly "no significant structural change")
6. `river_sentinel2_optical.tif` + `river_sentinel1_sar_vv.tif`: "Use the optical and SAR images together to identify built-up and water-covered regions." (fusion, river in blue; works without the model server)

After each: open the execution summary; on the last one click Download report.

## 10. Likely questions and honest answers

- Is the router an LLM? No, deterministic rules keyed on input configuration and keywords, with an LLM hook left disabled to stay free. Predictable and auditable; with five tasks it is also correct.
- Why Qwen in the demo when the benchmarks say GeoChat? GeoChat's 2023 codebase pins transformers 4.31, which no longer installs on Colab's Python 3.13; on our own GPU it ran and produced the benchmark numbers. The system detects which model the server runs and adapts prompts and box scales automatically.
- Where is the remote-sensing adaptation? The CLIP LoRA on BigEarthNet + BigEarthNet.txt (69 -> 91 percent). GeoChat itself is also RS-instruction-tuned by its authors.
- Why not a change-detection model? CDChat needs 14 GB of weights and a fine-tune; the map + VLM design works today, is transparent and cannot hallucinate change. The CDChat wrapper is in the repo as the next step.
- What does the confidence mean? Fusion: measured sensor agreement. Change: map margin around the cut-off. VLM tools: fixed 0.7 because the model gives no probability, labelled as such in the trace. Top level is the minimum over tools.
- How would it handle the ISRO evaluation set (Cartosat-2S optical + RISAT SAR GeoTIFFs)? The validator reads any GeoTIFF, detects SAR from band count/dtype/filename, checks CRS and bounds overlap, resizes mismatched pairs and logs each decision. Fusion works on any optical with a NIR band, or SAR-only water if not.
- Cost and hardware? Zero. Training on one RTX 5070 Ti; serving on a free Colab T4; the app runs on a laptop.
- Limitations? Small VLM hallucinates on paired images (mitigated by the map gate); fusion misreads mountain radar shadows; change map is seasonal-sensitive (68 to 70 percent alone); CDVQA not evaluated; fine-tuned CLIP not yet inside a tool.
