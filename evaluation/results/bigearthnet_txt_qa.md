# GeoChat-7B 4-bit zero-shot on BigEarthNet.txt QA (300 sampled questions)

| type | n | accuracy |
|---|---|---|
| binary | 150 | 54.7% |
| mcq | 150 | 25.3% |
| **all** | 300 | **40.0%** |

| category | n | accuracy |
|---|---|---|
| adjacency | 58 | 43.1% |
| area | 63 | 39.7% |
| climate zone | 22 | 22.7% |
| count | 62 | 51.6% |
| country | 25 | 32.0% |
| presence | 49 | 42.9% |
| relative pos | 6 | 16.7% |
| season | 15 | 20.0% |

## Sample of wrong answers

| type | question | gold | model |
|---|---|---|---|
| binary | Does any instance of complex cultivation patterns and a mixed forest share a common bounda | no | yes |
| binary | Is the area of arable lands greater than 1152000 m2? | no | yes |
| binary | Are there touching boundaries between any arable land and pastures? | no | yes |
| binary | Does the image show other classes besides transitional woodlands or shrubs? | yes | no |
| binary | Do coniferous forests occupy at least 60% of the image? | no | yes |
| binary | Would you say that any arable land lies next to a coniferous forest in the image? | yes | no |
| binary | Does the boundary of any instance of complex cultivation patterns touch that of urban fabr | yes | no |
| binary | Would you classify arable lands as taking up between 144000 m^2 and 288000 m^2 of the imag | no | yes |
| binary | Is there evidence of industrial or commercial units in the image? | yes | no |
| binary | Are there at least two connected regions of complex cultivation patterns visible in the im | yes | no |
| binary | Is the total area of marine waters between 90% and 100%? | yes | no |
| binary | Would you classify broad-leaved forests as covering between 576000 m^2 and 720000 m^2 of t | no | yes |
| binary | Is the area covered by moors, heathland, or sclerophyllous vegetation at least 0%? | yes | no |
| binary | Are transitional woodlands or shrubs represented in more than one continuous area within t | yes | no |
| binary | Does this scene feature mixed forest? | no | yes |
