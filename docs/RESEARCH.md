# Background research (Sep 2026)

## What people actually ask satellite imagery

| Query | Who asks |
|---|---|
| Which fields show crop stress? Expected yield? | Agriculture depts, insurers |
| Which villages/roads are underwater right now? | Disaster agencies |
| Which buildings were damaged by this cyclone/quake? | Responders, government |
| Where did forest cover disappear since last quarter? | Forest depts, regulators |
| How much has built-up area grown? Any lakebed encroachment? | City planners |
| How full are reservoirs? How are wetlands changing? | Water boards |
| Which blocks are in drought this season? | State governments (a standing Bhuvan product) |
| What fraction of this area is farmland vs forest vs built-up? | Planners, policy |
| What changed between these two dates? | Everyone — underlies most of the above |

## Pain points (why SatQuery matters)

1. **Clouds block optical images exactly when needed** (monsoon floods). SAR sees through clouds but looks alien — needs expert interpretation. → our optical–SAR fusion.
2. **Skill barrier**: analysis needs GIS + coding; most planners/officials can't. This is exactly why NASA built Earth Copilot.
3. **Slow answers**: change detection and damage assessment are still mostly manual.
4. **Huge data, hard access**: big downloads, fragmented portals.
5. ISRO context: Bhuvan/Bhoonidhi users complain of split portals, slow servers, painful downloads. EOS-04 (RISAT-class) SAR is already used for rapid flood mapping — proven demand for automating this.

## What already exists (closest systems)

- **NASA Earth Copilot** (Microsoft+NASA): GPT translates questions into dataset queries over NASA archives. Data-finding agent, not a vision-model router. [repo](https://github.com/microsoft/Earth-Copilot)
- **RS-ChatGPT**: closest to our idea. ChatGPT is the controller: reads the query, picks vision tools (classification, captioning, detection, segmentation), runs them, composes the answer. [repo](https://github.com/HaonanGuo/Remote-Sensing-ChatGPT)
- **RS-Agent**: LLM "central controller" + tool library + RS knowledge retrieval. [repo](https://github.com/intellisensing/rs-agent)
- **RS VLMs** (can be our specialist tools): **GeoChat** (VQA/grounding on satellite images, open weights), **LHRS-Bot**, **EarthGPT** (handles optical+SAR+IR), **EarthDial** (multi-sensor, multi-temporal).
- **Change chat models**: **CDChat** ([repo](https://github.com/techmn/cdchat)), **ChangeChat**, plus the original CDVQA baseline.
- **RS CLIP encoders**: **RemoteCLIP**, **GeoRSCLIP** — image–text backbones we can fine-tune on BigEarthNet (Sentinel-1 SAR + Sentinel-2 optical).

## The proven recipe (what we build)

LLM planner + tool registry + specialist models + evidence aggregation:
1. LLM controller reads the query and input config.
2. Picks tools from a registry (GeoChat-style model for VQA/caption/grounding, CDChat-style for change, BigEarthNet-adapted encoder for optical–SAR).
3. Runs them, merges outputs with boxes/masks + confidence.
4. Returns answer + evidence + execution trace.

Best starting code: RS-ChatGPT (simplest controller loop), GeoChat weights, CDChat, RemoteCLIP/GeoRSCLIP.
