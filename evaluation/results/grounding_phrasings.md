# Grounding phrasings, GeoChat-7B 4-bit (2026-09-03)

Model: geochat-7B via http backend. Boxes parsed by
backend/tools/grounding/box_parser.py, coordinate scale 0-100.

## Box hit rate per phrasing

| phrasing | boxes returned | of prompts |
|---|---|---|
| `[refer] give me the location of {obj}` | 7 | 7 |
| `[refer] where is {obj}? give me its bounding box` | 7 | 7 |
| `[refer] {obj}` | 7 | 7 |
| `[refer] locate {obj} in the image` | 7 | 7 |
| `[refer] where is {obj}?` | 5 | 7 |
| `[grounding] highlight {obj}` | 3 | 7 |

## Every prompt and raw answer

| image | object | phrasing | boxes | raw output |
|---|---|---|---|---|
| waterview.jpg | the water body | `[refer] give me the location of {obj}` | 1 | `{<0><53><29><73>\|<90>}` |
| waterview.jpg | the water body | `[refer] where is {obj}?` | 1 | `{<10><50><26><70>\|<90>}` |
| waterview.jpg | the water body | `[refer] where is {obj}? give me its bounding box` | 1 | `{<0><53><29><73>\|<90>}` |
| waterview.jpg | the water body | `[refer] {obj}` | 1 | `{<0><56><45><80>\|<90>}` |
| waterview.jpg | the water body | `[refer] locate {obj} in the image` | 1 | `{<0><56><29><76>\|<90>}` |
| waterview.jpg | the water body | `[grounding] highlight {obj}` | 0 | `<p>1 bridge at the center</p>` |
| waterview.jpg | the lake | `[refer] give me the location of {obj}` | 1 | `{<0><50><39><70>\|<90>}` |
| waterview.jpg | the lake | `[refer] where is {obj}?` | 1 | `{<0><53><39><73>\|<90>}` |
| waterview.jpg | the lake | `[refer] where is {obj}? give me its bounding box` | 1 | `{<0><50><39><70>\|<90>}` |
| waterview.jpg | the lake | `[refer] {obj}` | 1 | `{<0><50><42><74>\|<90>}` |
| waterview.jpg | the lake | `[refer] locate {obj} in the image` | 1 | `{<0><50><39><70>\|<90>}` |
| waterview.jpg | the lake | `[grounding] highlight {obj}` | 1 | `<p>1 large harbor</p> {<36><56><76><80>\|<90>}` |
| waterview.jpg | the bridge | `[refer] give me the location of {obj}` | 1 | `{<36><64><76><76>\|<90>}` |
| waterview.jpg | the bridge | `[refer] where is {obj}?` | 0 | `The bridge is located at the center of the image.` |
| waterview.jpg | the bridge | `[refer] where is {obj}? give me its bounding box` | 1 | `{<36><61><76><73>\|<90>}` |
| waterview.jpg | the bridge | `[refer] {obj}` | 1 | `{<36><64><76><76>\|<90>}` |
| waterview.jpg | the bridge | `[refer] locate {obj} in the image` | 1 | `{<36><64><76><76>\|<90>}` |
| waterview.jpg | the bridge | `[grounding] highlight {obj}` | 0 | `<p>1 bridge at the center</p>` |
| 11760.jpg | the buildings | `[refer] give me the location of {obj}` | 1 | `{<5><12><13><24>\|<90>}` |
| 11760.jpg | the buildings | `[refer] where is {obj}?` | 3 | `{<10><13><18><21>\|<90>}{<16><10><20><14>\|<90>}{<10><10><14><14>\|<90>}` |
| 11760.jpg | the buildings | `[refer] where is {obj}? give me its bounding box` | 1 | `{<5><12><13><24>\|<90>}` |
| 11760.jpg | the buildings | `[refer] {obj}` | 1 | `{<10><13><18><25>\|<90>}` |
| 11760.jpg | the buildings | `[refer] locate {obj} in the image` | 7 | `{<10><13><18><25>\|<90>}{<16><10><20><14>\|<90>}{<20><10><24><14>\|<90>}{<24><10><30><14>\|<90>}{<28><10><34><14>\|<90>}{<32><10><38><14>\|<90>}{<40><10><46><14>\|<90>}` |
| 11760.jpg | the buildings | `[grounding] highlight {obj}` | 1 | `{<5><11><13><23>\|<90>}` |
| 11760.jpg | the road | `[refer] give me the location of {obj}` | 1 | `{<89><88><100><92>\|<90>}` |
| 11760.jpg | the road | `[refer] where is {obj}?` | 1 | `{<89><88><100><92>\|<90>}` |
| 11760.jpg | the road | `[refer] where is {obj}? give me its bounding box` | 1 | `{<89><88><100><92>\|<90>}` |
| 11760.jpg | the road | `[refer] {obj}` | 1 | `{<89><88><100><92>\|<90>}` |
| 11760.jpg | the road | `[refer] locate {obj} in the image` | 1 | `{<89><88><100><92>\|<90>}` |
| 11760.jpg | the road | `[grounding] highlight {obj}` | 0 | `<p>1 road at the right</p>` |
| 11765.jpg | the buildings | `[refer] give me the location of {obj}` | 1 | `{<69><86><77><94>\|<90>}` |
| 11765.jpg | the buildings | `[refer] where is {obj}?` | 1 | `{<69><86><77><94>\|<90>}` |
| 11765.jpg | the buildings | `[refer] where is {obj}? give me its bounding box` | 1 | `{<69><85><77><93>\|<90>}` |
| 11765.jpg | the buildings | `[refer] {obj}` | 1 | `{<69><85><77><93>\|<90>}` |
| 11765.jpg | the buildings | `[refer] locate {obj} in the image` | 2 | `{<69><86><77><94>\|<90>}{<60><50><68><58>\|<90>}` |
| 11765.jpg | the buildings | `[grounding] highlight {obj}` | 1 | `{<68><85><76><97>\|<90>}` |
| 11765.jpg | the road | `[refer] give me the location of {obj}` | 1 | `{<69><0><77><100>\|<45>}` |
| 11765.jpg | the road | `[refer] where is {obj}?` | 0 | `The road is at the top right of the image.` |
| 11765.jpg | the road | `[refer] where is {obj}? give me its bounding box` | 1 | `{<69><0><77><10>\|<45>}` |
| 11765.jpg | the road | `[refer] {obj}` | 1 | `{<69><0><77><100>\|<45>}` |
| 11765.jpg | the road | `[refer] locate {obj} in the image` | 1 | `{<67><0><75><10>\|<45>}` |
| 11765.jpg | the road | `[grounding] highlight {obj}` | 0 | `<p>1 large airplane</p>` |
