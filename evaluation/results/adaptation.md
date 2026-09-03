# Remote-sensing adaptation proof

Base model: openai/clip-vit-base-patch32, LoRA r=16, 3 epochs, batch 64, lr 0.0001
Data: BigEarthNet subset (data/bigearthnet_subset)

| metric | before | after |
|---|---|---|
| zero-shot label top-1 (val) | 0.693 | 0.848 |

## Run: data=data/bigearthnet_txt init=models/clip_bigearthnet_lora -> models/clip_bigearthnet_txt_lora

Base model: openai/clip-vit-base-patch32, LoRA r=16, 2 epochs, batch 32, lr 0.0001

| metric | before | after |
|---|---|---|
| zero-shot label top-1 (val, data/bigearthnet_subset) | 0.849 | 0.766 |

## Run: data=data/bigearthnet_subset,data/bigearthnet_txt init=base -> models/clip_bigearthnet_txt_lora

Base model: openai/clip-vit-base-patch32, LoRA r=16, 3 epochs, batch 32, lr 0.0001, 7890 training rows

| metric | before | after |
|---|---|---|
| zero-shot label top-1 (val, data/bigearthnet_subset) | 0.693 | 0.906 |
| image->caption recall@1 (val, data/bigearthnet_txt) | 0.017 | 0.066 |
| image->caption recall@5 (val, data/bigearthnet_txt) | 0.071 | 0.237 |
