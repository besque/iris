"""LoRA fine-tune of CLIP on BigEarthNet data. The mandatory adaptation.

Stage 1 (land-cover labels):   python training/finetune_clip.py
Stage 2 (BigEarthNet.txt captions, continuing from stage 1):
    DATA=data/bigearthnet_txt INIT_LORA=models/clip_bigearthnet_lora \
    OUT=models/clip_bigearthnet_txt_lora python training/finetune_clip.py

Rows may carry "labels" (list) or "text" (a caption). Evaluation always uses the
labelled set (EVAL_DATA) so numbers stay comparable across stages.
"""

import json
import os
import random

import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from transformers import CLIPModel, CLIPProcessor

BASE = "openai/clip-vit-base-patch32"
DATA = os.environ.get("DATA", "data/bigearthnet_subset")
EVAL_DATA = os.environ.get("EVAL_DATA", "data/bigearthnet_subset")
OUT = os.environ.get("OUT", "models/clip_bigearthnet_lora")
INIT_LORA = os.environ.get("INIT_LORA")
EPOCHS = int(os.environ.get("EPOCHS", 3))
BATCH = int(os.environ.get("BATCH", 64))
LR = 1e-4
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
PROMPT = "a satellite image of {}"


class BenDataset(Dataset):
    def __init__(self, split, root=DATA):
        self.rows = [json.loads(l) for l in open(f"{root}/{split}.jsonl")]

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        r = self.rows[i]
        if r.get("text"):
            text = r["text"]
        else:
            prompt = "a SAR satellite image of {}" if r.get("modality") == "sar" else PROMPT
            text = prompt.format(", ".join(r["labels"]).lower())
        return Image.open(r["image"]).convert("RGB"), text, r.get("labels", [])


def collate(batch, processor):
    images, texts, labels = zip(*batch)
    enc = processor(text=list(texts), images=list(images), return_tensors="pt",
                    padding=True, truncation=True, max_length=77)
    return enc, labels


def _as_features(model, out, kind):
    """Newer transformers return an output object, sometimes already projected."""
    if torch.is_tensor(out):
        return out
    emb = getattr(out, f"{kind}_embeds", None)
    if emb is not None:
        return emb
    pooled = out.pooler_output
    if pooled.shape[-1] == model.config.projection_dim:
        return pooled
    proj = model.text_projection if kind == "text" else model.visual_projection
    return proj(pooled)


@torch.no_grad()
def zero_shot_top1(model, processor, split="val"):
    """Fraction of samples whose top-ranked label is one of their true labels."""
    ds = BenDataset(split, root=EVAL_DATA)
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
    from peft import LoraConfig, PeftModel, get_peft_model

    processor = CLIPProcessor.from_pretrained(BASE)
    model = CLIPModel.from_pretrained(BASE).to(DEVICE)

    if INIT_LORA:
        model = PeftModel.from_pretrained(model, INIT_LORA, is_trainable=True)
        print(f"continuing from {INIT_LORA}")
    before = zero_shot_top1(model, processor)
    print(f"zero-shot top-1 BEFORE: {before:.3f}")

    if not INIT_LORA:
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
    with open("evaluation/results/adaptation.md", "a") as f:
        f.write(
            f"\n## Run: data={DATA} init={INIT_LORA or 'base'} -> {OUT}\n\n"
            f"Base model: {BASE}, LoRA r=16, {EPOCHS} epochs, batch {BATCH}, lr {LR}\n\n"
            f"| metric | before | after |\n|---|---|---|\n"
            f"| zero-shot label top-1 (val, {EVAL_DATA}) | {before:.3f} | {after:.3f} |\n"
        )
    print(f"saved checkpoint to {OUT} and numbers to evaluation/results/adaptation.md")


if __name__ == "__main__":
    random.seed(0)
    torch.manual_seed(0)
    main()
