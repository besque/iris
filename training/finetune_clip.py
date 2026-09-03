"""LoRA fine-tune of CLIP on BigEarthNet data. The mandatory adaptation.

Stage 1 (land-cover labels):
    python training/finetune_clip.py
Stage 2 (labels + BigEarthNet.txt captions together, from the base model):
    DATA=data/bigearthnet_subset,data/bigearthnet_txt OUT=models/clip_bigearthnet_txt_lora \
    python training/finetune_clip.py

Rows carry "labels" (list) or "text" (a caption). Two metrics, both on held-out data:
zero-shot label top-1 (EVAL_DATA) and image->caption retrieval recall (RETRIEVAL_DATA).
"""

import json
import os
import random

import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from transformers import CLIPModel, CLIPProcessor

BASE = "openai/clip-vit-base-patch32"
DATA = os.environ.get("DATA", "data/bigearthnet_subset").split(",")
EVAL_DATA = os.environ.get("EVAL_DATA", "data/bigearthnet_subset")
RETRIEVAL_DATA = os.environ.get("RETRIEVAL_DATA", "data/bigearthnet_txt")
OUT = os.environ.get("OUT", "models/clip_bigearthnet_lora")
INIT_LORA = os.environ.get("INIT_LORA")
EPOCHS = int(os.environ.get("EPOCHS", 3))
BATCH = int(os.environ.get("BATCH", 64))
LR = 1e-4
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
PROMPT = "a satellite image of {}"


def load_rows(roots, split):
    rows = []
    for root in roots:
        path = f"{root}/{split}.jsonl"
        if os.path.exists(path):
            rows += [json.loads(l) for l in open(path)]
    return rows


class BenDataset(Dataset):
    def __init__(self, split, roots=DATA):
        self.rows = load_rows(roots, split)

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
def _embed_texts(model, processor, texts):
    out = []
    for i in range(0, len(texts), 64):
        enc = processor(text=texts[i:i + 64], return_tensors="pt", padding=True,
                        truncation=True, max_length=77).to(DEVICE)
        e = _as_features(model, model.get_text_features(**enc), "text")
        out.append(e / e.norm(dim=-1, keepdim=True))
    return torch.cat(out)


@torch.no_grad()
def _embed_image(model, processor, img):
    enc = processor(images=img, return_tensors="pt").to(DEVICE)
    e = _as_features(model, model.get_image_features(**enc), "image")
    return e / e.norm(dim=-1, keepdim=True)


@torch.no_grad()
def zero_shot_top1(model, processor, split="val"):
    """Fraction of samples whose top-ranked label is one of their true labels."""
    ds = BenDataset(split, roots=[EVAL_DATA])
    all_labels = sorted({l for r in ds.rows for l in r["labels"]})
    text_emb = _embed_texts(model, processor, [PROMPT.format(l.lower()) for l in all_labels])
    hits = 0
    for img, _, labels in ds:
        top = all_labels[(_embed_image(model, processor, img) @ text_emb.T).argmax().item()]
        hits += top in labels
    return hits / len(ds)


@torch.no_grad()
def caption_retrieval(model, processor, split="val", k=5):
    """Image -> caption retrieval among all val captions. Returns (recall@1, recall@k)."""
    rows = load_rows([RETRIEVAL_DATA], split)
    rows = [r for r in rows if r.get("text")]
    if not rows:
        return None
    first = {}
    for r in rows:  # one caption per image keeps the pool clean
        first.setdefault(r["image"], r["text"])
    images, caps = list(first), list(first.values())
    text_emb = _embed_texts(model, processor, caps)
    r1 = rk = 0
    for i, path in enumerate(images):
        sims = (_embed_image(model, processor, Image.open(path).convert("RGB")) @ text_emb.T)[0]
        ranked = sims.argsort(descending=True)
        r1 += int(ranked[0].item() == i)
        rk += int(i in ranked[:k].tolist())
    return r1 / len(images), rk / len(images)


def evaluate(model, processor):
    top1 = zero_shot_top1(model, processor)
    ret = caption_retrieval(model, processor)
    print(f"  label top-1 {top1:.3f}" + (f"   caption R@1 {ret[0]:.3f}  R@5 {ret[1]:.3f}" if ret else ""))
    return top1, ret


def main():
    from peft import LoraConfig, PeftModel, get_peft_model

    processor = CLIPProcessor.from_pretrained(BASE)
    model = CLIPModel.from_pretrained(BASE).to(DEVICE)

    if INIT_LORA:
        model = PeftModel.from_pretrained(model, INIT_LORA, is_trainable=True)
        print(f"continuing from {INIT_LORA}")
    print("BEFORE:")
    before = evaluate(model, processor)

    if not INIT_LORA:
        lora = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.1,
                          target_modules=["q_proj", "k_proj", "v_proj", "out_proj"])
        model = get_peft_model(model, lora)
    model.print_trainable_parameters()

    train = BenDataset("train")
    print(f"training on {len(train)} rows from {DATA}")
    loader = DataLoader(train, batch_size=BATCH, shuffle=True, collate_fn=lambda b: collate(b, processor))
    opt = torch.optim.AdamW(model.parameters(), lr=LR)
    model.train()
    for epoch in range(EPOCHS):
        for step, (enc, _) in enumerate(loader):
            enc = {k: v.to(DEVICE) for k, v in enc.items()}
            out = model(**enc, return_loss=True)
            out.loss.backward()
            opt.step()
            opt.zero_grad()
            if step % 20 == 0:
                print(f"epoch {epoch} step {step} loss {out.loss.item():.4f}")

    model.eval()
    print("AFTER:")
    after = evaluate(model, processor)

    os.makedirs(OUT, exist_ok=True)
    model.save_pretrained(OUT)

    os.makedirs("evaluation/results", exist_ok=True)
    with open("evaluation/results/adaptation.md", "a") as f:
        f.write(f"\n## Run: data={','.join(DATA)} init={INIT_LORA or 'base'} -> {OUT}\n\n"
                f"Base model: {BASE}, LoRA r=16, {EPOCHS} epochs, batch {BATCH}, lr {LR}, {len(train)} training rows\n\n"
                f"| metric | before | after |\n|---|---|---|\n"
                f"| zero-shot label top-1 (val, {EVAL_DATA}) | {before[0]:.3f} | {after[0]:.3f} |\n")
        if before[1] and after[1]:
            f.write(f"| image->caption recall@1 (val, {RETRIEVAL_DATA}) | {before[1][0]:.3f} | {after[1][0]:.3f} |\n"
                    f"| image->caption recall@5 (val, {RETRIEVAL_DATA}) | {before[1][1]:.3f} | {after[1][1]:.3f} |\n")
    print(f"saved checkpoint to {OUT} and numbers to evaluation/results/adaptation.md")


if __name__ == "__main__":
    random.seed(0)
    torch.manual_seed(0)
    main()
