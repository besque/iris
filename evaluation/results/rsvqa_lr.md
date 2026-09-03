# RSVQA-LR test accuracy, geochat-7B 4-bit (2026-09-03)

700 questions sampled from the official test split (seed 0, 300 per type), prompt suffix `Answer the question using a single word or phrase.`, zero-shot, no fine-tuning.
Count questions skipped as in the GeoChat paper. Answers normalised (lowercase, first word for yes/no).

| type | n | accuracy |
|---|---|---|
| presence | 300 | 91.0% |
| comp | 300 | 86.7% |
| rural_urban | 100 | 94.0% |
| **all** | 700 | **89.6%** |

For reference the GeoChat paper reports 91.1 / 90.3 / 94.0 (presence / comparison / rural-urban) on the full LR test set in fp16.

## Sample of wrong answers

| type | question | gold | model said |
|---|---|---|---|
| presence | Is there a square building in the image? | no | Yes |
| presence | Is there a large commercial building? | yes | No |
| presence | Is a circular commercial building present? | yes | No |
| presence | Is a circular water area present? | no | Yes |
| presence | Is a square forest present? | yes | No |
| presence | Is a square water area present? | no | Yes |
| presence | Is a commercial building present? | no | Yes |
| presence | Is a square residential building present? | yes | No |
| presence | Is a circular water area present? | no | Yes |
| presence | Is a large parking present? | yes | No |
| presence | Is there a commercial building? | no | Yes |
| presence | Is there a square water area? | no | Yes |
| presence | Is there a circular water area? | no | Yes |
| presence | Is a rectangular commercial building present in the image? | yes | No |
| presence | Is there a circular forest in the image? | yes | No |
| presence | Is there a road at the bottom of a  rectangular scrub? | no | Yes |
| presence | Is there a square residential building? | no | Yes |
| presence | Is there a circular water area? | no | Yes |
| presence | Is a square building present? | no | Yes |
| presence | Is there a road on the right of a  commercial building? | no | Yes |
| presence | Is there a circular water area? | no | Yes |
| presence | Is a large commercial building present? | no | Yes |
| presence | Is a square residential building present? | no | Yes |
| presence | Is a circular grass area present? | yes | No |
| presence | Is a large building present? | no | Yes |
| presence | Is there a circular residential building? | no | Yes |
| presence | Is a medium water area present? | no | Yes |
| comp | Are there less residential buildings than roads? | no | Yes |
| comp | Are there less grass areas than roads? | no | Yes |
| comp | Are there less commercial buildings than water areas? | no | Yes |
