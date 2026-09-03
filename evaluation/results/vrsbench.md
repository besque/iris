# GeoChat-7B 4-bit zero-shot on VRSBench val sample (360 VQA, 60 captions)

## VQA

| type | n | accuracy |
|---|---|---|
| image | 30 | 60.0% |
| object category | 30 | 76.7% |
| object color | 30 | 36.7% |
| object direction | 30 | 33.3% |
| object existence | 30 | 93.3% |
| object position | 30 | 66.7% |
| object quantity | 30 | 26.7% |
| object shape | 30 | 30.0% |
| object size | 30 | 43.3% |
| reasoning | 30 | 50.0% |
| rural or urban | 30 | 73.3% |
| scene type | 30 | 43.3% |
| **all** | 360 | **52.8%** |

## Captioning

BLEU-1 0.221, BLEU-4 0.014 (single reference, 60 images)

Example:

- model: The image depicts a scene with a road and a windmill. The road is located at the top right of the image, while the windmill is located at the bottom left. The windmill is gray in color and appears to be a single unit. The road appears to be a continuation of the one at the top right, but it is not p
- reference: This high-resolution image sourced from GoogleEarth shows a landscape with varied vegetation and a single small vehicle located in the top-right area of the image. The terrain is a mix of grassy patches and wooded areas with trees scattered throughout. There is a winding path within the vegetation a

## Sample of wrong VQA answers

| type | question | gold | model |
|---|---|---|---|
| object color | What is the color of the vehicle at the top-right corner? | Black | maroon |
| object color | What color is the terrain? | Grey-brown | gray |
| object color | What is the primary color of the terrain? | Brown | Gray |
| object color | What color are the roofs of the buildings? | red | Brown |
| object color | What color is the running track in the stadium? | Red | Gray |
| object color | What is the primary color of the tennis court? | Blue | Teal |
| object color | What color is the tennis court? | blue | Purple |
| object color | What is the color of the basketball court? | Blue | Not specified |
| object color | What is the predominant color of the water body adjacent to the bridge? | dark | Gray |
| object color | What color are the majority of rooftops in the image? | Blue | gray |
| object color | Is the overpass surface color darker than the road beneath it? | Yes | No |
| object color | What is the main color of the vehicle parked at the bottom-left corner? | Black | olive |
| object color | What is the predominant color of the storage tank? | white | gray |
| object color | What color are the storage tanks? | White | gray |
| object color | What color dominates the image? | Green | Gray |
