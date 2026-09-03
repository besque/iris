from pathlib import Path
from typing import Any, Optional


def _cuda_available() -> bool:
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False


class ChangeModel:
    """
    Wrapper around the CDChat bi-temporal change-analysis model.

    CDChat inference requires a CUDA-capable GPU.
    This wrapper therefore checks the device before loading
    the actual model.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        model_base: Optional[str] = None,
        mm_projector_path: Optional[str] = None,
        device: Optional[str] = None,
    ):
        self.model_path = model_path
        self.model_base = model_base
        self.mm_projector_path = mm_projector_path

        self.device = device or ("cuda" if _cuda_available() else "cpu")

        self.tokenizer = None
        self.model = None
        self.image_processor = None
        self.context_len = None

    def load(self) -> None:
        """
        Load CDChat.

        CDChat's official model loader uses CUDA/FP16,
        so inference requires an NVIDIA CUDA GPU.
        """

        if self.device != "cuda":
            raise RuntimeError(
                "CDChat inference requires a CUDA-capable NVIDIA GPU. "
                f"Current device: {self.device}. "
                "The current machine has no CUDA device."
            )

        if not self.model_path:
            raise ValueError(
                "model_path must be provided before loading CDChat."
            )

        model_path = Path(self.model_path)

        if not model_path.exists():
            raise FileNotFoundError(
                f"CDChat model path does not exist: {model_path}"
            )

        from cdchat.mm_utils import get_model_name_from_path
        from cdchat.model.builder import load_pretrained_model

        model_name = get_model_name_from_path(str(model_path))

        (
            self.tokenizer,
            self.model,
            self.image_processor,
            self.context_len,
        ) = load_pretrained_model(
            model_path=str(model_path),
            model_base=self.model_base,
            model_name=model_name,
            device_map="auto",
            device="cuda",
            mm_projector_path=self.mm_projector_path,
        )

        self.model.eval()

    def predict(
        self,
        image_t1: Any,
        image_t2: Any,
        question: str,
    ) -> str:
        """
        Run CDChat inference on a bi-temporal image pair.

        Actual inference will be implemented after the model
        checkpoint and GPU environment are available.
        """

        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        if self.model is None:
            raise RuntimeError(
                "Change model is not loaded. Call load() first."
            )

        if self.device != "cuda":
            raise RuntimeError(
                "CDChat inference requires a CUDA-capable NVIDIA GPU."
            )

        # Image preprocessing and model.generate() will be
        # connected after the checkpoint is configured.
        raise NotImplementedError(
            "CDChat inference pipeline has not been connected yet."
        )