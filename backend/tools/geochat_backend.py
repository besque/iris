"""One place that talks to the VLM. Everything else (prompting, parsing,
ToolResult) lives in the tool classes and does not care where the model runs.

Pick the backend with GEOCHAT_BACKEND:
  http   POST {"image": <base64 png>, "prompt": str} to GEOCHAT_ENDPOINT
         (the Colab notebook's serve cell speaks this), reply {"text": str}
  local  load geochat-7B in 4-bit on this machine (needs the GeoChat repo
         on PYTHONPATH and a GPU)
  qwen   Qwen2-VL-2B-Instruct through transformers, the fallback model
If unset, http is used when GEOCHAT_ENDPOINT is set, else local."""

import base64
import io
import os

import numpy as np
from PIL import Image

# where the box coordinates of each model live, per side of the image
COORD_SCALES = {"geochat-7B": 100, "Qwen2-VL-2B-Instruct": 1000}

_local = {}   # cached model handles


def backend_name() -> str:
    name = os.environ.get("GEOCHAT_BACKEND", "").lower()
    if name:
        return name
    return "http" if os.environ.get("GEOCHAT_ENDPOINT") else "local"


def _remote_health() -> dict:
    """The serve cell reports which model it loaded, so ask it once instead of guessing."""
    if "health" not in _local:
        _local["health"] = {}
        url = os.environ.get("GEOCHAT_ENDPOINT")
        if url:
            try:
                import requests
                _local["health"] = requests.get(url.rstrip("/") + "/health", timeout=15).json()
            except Exception:
                pass
    return _local["health"]


def model_name() -> str:
    if os.environ.get("GEOCHAT_MODEL_NAME"):
        return os.environ["GEOCHAT_MODEL_NAME"]
    if backend_name() == "http" and _remote_health().get("model"):
        return _remote_health()["model"]
    return "Qwen2-VL-2B-Instruct" if backend_name() == "qwen" else "geochat-7B"


def coord_scale() -> int:
    if os.environ.get("GEOCHAT_COORD_SCALE"):
        return int(os.environ["GEOCHAT_COORD_SCALE"])
    if backend_name() == "http" and _remote_health().get("coord_scale"):
        return int(_remote_health()["coord_scale"])
    return COORD_SCALES.get(model_name(), 100)


def load_image(image) -> Image.Image:
    """Path, validator dict, numpy array or PIL image -> RGB PIL image."""
    if isinstance(image, (list, tuple)):
        if len(image) != 1:
            raise ValueError(f"single-image tool got {len(image)} images")
        image = image[0]
    if isinstance(image, dict):
        image = image.get("rgb", image.get("array", image.get("path")))
    if isinstance(image, Image.Image):
        return image.convert("RGB")
    if isinstance(image, str):
        if image.lower().endswith((".tif", ".tiff")):
            from backend.preprocessing.validator import to_rgb
            return Image.fromarray(to_rgb(image))
        return Image.open(image).convert("RGB")
    if isinstance(image, np.ndarray):
        arr = image
        if arr.ndim == 3 and arr.shape[0] in (1, 3, 4) and arr.shape[-1] not in (1, 3, 4):
            arr = np.moveaxis(arr, 0, -1)     # CxHxW -> HxWxC
        if arr.ndim == 2:
            arr = np.stack([arr] * 3, axis=-1)
        if arr.shape[-1] == 4:
            arr = arr[..., :3]
        if arr.dtype != np.uint8:
            arr = arr.astype(np.float32)
            top = np.nanmax(arr) if np.nanmax(arr) > 0 else 1.0
            arr = (arr / (1.0 if top <= 1.0 else top) * 255).clip(0, 255).astype(np.uint8)
        return Image.fromarray(arr).convert("RGB")
    raise TypeError(f"unsupported image type: {type(image).__name__}")


def _call_geochat(image: Image.Image, prompt: str) -> str:
    """The one function to change per environment. Returns the raw model text."""
    name = backend_name()
    if name == "http":
        return _call_http(image, prompt)
    if name == "local":
        return _call_local_geochat(image, prompt)
    if name == "qwen":
        return _call_local_qwen(image, prompt)
    raise ValueError(f"unknown GEOCHAT_BACKEND: {name}")


# ---------------------------------------------------------------- http

def _call_http(image, prompt):
    import requests

    url = os.environ.get("GEOCHAT_ENDPOINT")
    if not url:
        raise RuntimeError("GEOCHAT_ENDPOINT not set (the tunnel URL printed by the notebook)")
    if "qwen" in model_name().lower():
        prompt = qwen_prompt(prompt)   # the fallback model has no [refer] tags
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    payload = {"image": base64.b64encode(buf.getvalue()).decode(), "prompt": prompt}
    r = requests.post(url.rstrip("/") + "/answer", json=payload, timeout=180)
    r.raise_for_status()
    return r.json()["text"]


# --------------------------------------------------------------- local

def _call_local_geochat(image, prompt):
    if "geochat" not in _local:
        _local["geochat"] = _load_geochat()
    tokenizer, model, image_processor, gen = _local["geochat"]
    return gen(tokenizer, model, image_processor, image, prompt)


def _load_geochat():
    # same recipe as the notebook, kept identical so a bug shows up in both
    import torch
    from geochat.constants import DEFAULT_IMAGE_TOKEN, IMAGE_TOKEN_INDEX
    from geochat.conversation import conv_templates
    from geochat.mm_utils import process_images, tokenizer_image_token
    from geochat.model.builder import load_pretrained_model

    path = os.environ.get("GEOCHAT_WEIGHTS", "MBZUAI/geochat-7B")
    tokenizer, model, image_processor, _ = load_pretrained_model(
        path, None, "geochat-7B", load_4bit=True)

    def gen(tokenizer, model, image_processor, image, prompt, max_new_tokens=256):
        conv = conv_templates["llava_v1"].copy()
        conv.append_message(conv.roles[0], DEFAULT_IMAGE_TOKEN + "\n" + prompt)
        conv.append_message(conv.roles[1], None)
        ids = tokenizer_image_token(conv.get_prompt(), tokenizer, IMAGE_TOKEN_INDEX,
                                    return_tensors="pt").unsqueeze(0).to(model.device)
        pix = process_images([image], image_processor, model.config).to(
            model.device, dtype=torch.float16)
        with torch.inference_mode():
            out = model.generate(ids, images=pix, do_sample=False,
                                 max_new_tokens=max_new_tokens, use_cache=True)
        text = tokenizer.batch_decode(out[:, ids.shape[1]:], skip_special_tokens=True)[0]
        return text.strip().removesuffix("</s>").strip()

    return tokenizer, model, image_processor, gen


def _call_local_qwen(image, prompt):
    if "qwen" not in _local:
        _local["qwen"] = _load_qwen()
    model, processor = _local["qwen"]
    import torch

    prompt = qwen_prompt(prompt)
    messages = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": prompt}]}]
    chat = processor.apply_chat_template(messages, add_generation_prompt=True)
    inputs = processor(text=[chat], images=[image], return_tensors="pt").to(model.device)
    with torch.inference_mode():
        out = model.generate(**inputs, max_new_tokens=256, do_sample=False)
    return processor.batch_decode(out[:, inputs.input_ids.shape[1]:],
                                  skip_special_tokens=True)[0].strip()


def _load_qwen():
    import torch
    from transformers import AutoProcessor, Qwen2VLForConditionalGeneration

    name = "Qwen/Qwen2-VL-2B-Instruct"
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        name, torch_dtype=torch.float16, device_map="auto")
    return model, AutoProcessor.from_pretrained(name)


def qwen_prompt(prompt: str) -> str:
    """Qwen has no task tags. Turn a GeoChat-style prompt into a plain request."""
    for tag in ("[refer]", "[grounding]", "[identify]"):
        if prompt.lower().startswith(tag):
            body = prompt[len(tag):].strip()
            return (f"{body} Answer briefly, then give the bounding box of the region as "
                    f"<|box_start|>(x1,y1),(x2,y2)<|box_end|>.")
    return prompt
