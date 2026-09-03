# RSVQA-LR test accuracy, geochat-7B 4-bit (2026-09-03)

200 questions sampled from the official test split (seed 0, 100 per type), prompt suffix `Answer the question using a single word or phrase.`, zero-shot, no fine-tuning.
Count questions skipped as in the GeoChat paper. Answers normalised (lowercase, first word for yes/no).

| type | n | accuracy |
|---|---|---|
| presence | 100 | 88.0% |
| rural_urban | 100 | 94.0% |
| **all** | 200 | **91.0%** |

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
| rural_urban | Is it a rural or an urban area | rural | urban |
| rural_urban | Is it a rural or an urban area | rural | urban |
| rural_urban | Is it a rural or an urban area | urban | rural |
| rural_urban | Is it a rural or an urban area | rural | urban |
| rural_urban | Is it a rural or an urban area | rural | urban |
| rural_urban | Is it a rural or an urban area | rural | urban |
