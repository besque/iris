"""LoRA fine-tune of CLIP on a BigEarthNet subset. The mandatory adaptation.

Run on the GPU machine after scripts/prepare_bigearthnet.py:
    pip install torch transformers peft pillow
    python training/finetune_clip.py

Evaluates zero-shot label accuracy BEFORE and AFTER and writes both to
evaluation/results/adaptation.md. Checkpoint goes to models/clip_bigearthnet_lora/.
"""

import json
import os
import random

import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from transformers import CLIPModel, CLIPProcessor

BASE = "openai/clip-vit-base-patch32"
DATA = "data/bigearthnet_subset"
OUT = "models/clip_bigearthnet_lora"
EPOCHS = 3
BATCH = 64
LR = 1e-4
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
PROMPT = "a satellite image of {}"


class BenDataset(Dataset):
    def __init__(self, split):
        self.rows = [json.loads(l) for l in open(f"{DATA}/{split}.jsonl")]

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        r = self.rows[i]
        prompt = "a SAR satellite image of {}" if r.get("modality") == "sar" else PROMPT
        text = prompt.format(", ".join(r["labels"]).lower())
        return Image.open(r["image"]).convert("RGB"), text, r["labels"]


def collate(batch, processor):
    images, texts, labels = zip(*batch)
    enc = processor(text=list(texts), images=list(images), return_tensors="pt",
                    padding=True, truncation=True)
    return enc, labels


def _as_features(model, out, kind):
    """Newer transformers return an output object here instead of a tensor."""
    if torch.is_tensor(out):
        return out
    emb = getattr(out, f"{kind}_embeds", None)
    if emb is not None:
        return emb
    proj = model.text_projection if kind == "text" else model.visual_projection
    return proj(out.pooler_output)


@torch.no_grad()
def zero_shot_top1(model, processor, split="val"):
    """Fraction of samples whose top-ranked label is one of their true labels."""
    ds = BenDataset(split)
    all_labels = sorted({l for r in ds.rows for l in r["labels"]})
    text_enc = processor(text=[PROMPT.format(l.lower()) for l in all_labels],
                         return_tensors="pt", padding=True, truncation=True).to(DEVICE)
    text_emb = _as_features(model, model.get_text_features(**text_enc), "text")
    text_emb = text_emb / text_emb.norm(dim=-1, keepdim=True)

    hits = 0
    for img, _, labels in ds:
        enc = processor(images=img, return_tensors="pt").to(DEVICE)
        emb = _as_features(model, model.get_image_features(**enc), "image")
        emb = emb / emb.norm(dim=-1, keepdim=True)
        top = all_labels[(emb @ text_emb.T).argmax().item()]
        hits += top in labels
    return hits / len(ds)


def main():
    from peft import LoraConfig, get_peft_model

    processor = CLIPProcessor.from_pretrained(BASE)
    model = CLIPModel.from_pretrained(BASE).to(DEVICE)

    before = zero_shot_top1(model, processor)
    print(f"zero-shot top-1 BEFORE: {before:.3f}")

    lora = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.1,
                      target_modules=["q_proj", "k_proj", "v_proj", "out_proj"])
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()

    loader = DataLoader(BenDataset("train"), batch_size=BATCH, shuffle=True,
                        collate_fn=lambda b: collate(b, processor))
    opt = torch.optim.AdamW(model.parameters(), lr=LR)
    model.train()
    for epoch in range(EPOCHS):
        for step, (enc, _) in enumerate(loader):
            enc = {k: v.to(DEVICE) for k, v in enc.items()}
            out = model(**enc, return_loss=True)
            out.loss.backward()
            opt.step()
            opt.zero_grad()
            if step % 10 == 0:
                print(f"epoch {epoch} step {step} loss {out.loss.item():.4f}")

    model.eval()
    after = zero_shot_top1(model, processor)
    print(f"zero-shot top-1 AFTER: {after:.3f}")

    os.makedirs(OUT, exist_ok=True)
    model.save_pretrained(OUT)

    os.makedirs("evaluation/results", exist_ok=True)
    with open("evaluation/results/adaptation.md", "w") as f:
        f.write(
            f"# Remote-sensing adaptation proof\n\n"
            f"Base model: {BASE}, LoRA r=16, {EPOCHS} epochs, batch {BATCH}, lr {LR}\n"
            f"Data: BigEarthNet subset ({DATA})\n\n"
            f"| metric | before | after |\n|---|---|---|\n"
            f"| zero-shot label top-1 (val) | {before:.3f} | {after:.3f} |\n"
        )
    print(f"saved checkpoint to {OUT} and numbers to evaluation/results/adaptation.md")


if __name__ == "__main__":
    random.seed(0)
    torch.manual_seed(0)
    main()
