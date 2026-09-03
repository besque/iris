"""Launch CDChat LoRA fine-tuning for bi-temporal change analysis.

This wrapper does not implement training. It delegates to CDChat's existing
``external/cdchat/train/train.py`` entry point and never downloads models or
datasets.
"""

import argparse
import subprocess
import sys
from pathlib import Path

import torch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CDCHAT_TRAIN_SCRIPT = PROJECT_ROOT / "external" / "cdchat" / "train" / "train.py"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-path", required=True, help="Pretrained CDChat/base model path.")
    parser.add_argument("--data-path", default="data/change/cdchat_change.json", help="CDChat instruction JSON path.")
    parser.add_argument("--image-folder", default="data/change", help="Folder containing A/, B/, and label/.")
    parser.add_argument("--output-dir", default="models/cdchat/change-lora", help="LoRA output directory.")
    parser.add_argument("--lora-r", type=int, default=64)
    parser.add_argument("--lora-alpha", type=int, default=16)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument("--num-train-epochs", type=float, default=3.0)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--per-device-train-batch-size", type=int, default=1)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=8)
    parser.add_argument("--save-steps", type=int, default=500)
    parser.add_argument("--logging-steps", type=int, default=10)
    parser.add_argument(
        "--vision-tower",
        default="openai/clip-vit-large-patch14-336",
        help="Vision tower passed to CDChat (default: %(default)s).",
    )
    parser.add_argument("--lora-bias", choices=("none", "all", "lora_only"), default="none")
    parser.add_argument("--dry-run", action="store_true", help="Print the command without checking CUDA or executing it.")
    return parser


def build_command(args: argparse.Namespace) -> list[str]:
    return [
        sys.executable,
        str(CDCHAT_TRAIN_SCRIPT),
        "--model_name_or_path", args.model_path,
        "--data_path", args.data_path,
        "--image_folder", args.image_folder,
        "--output_dir", args.output_dir,
        "--vision_tower", args.vision_tower,
        "--lora_enable", "True",
        "--lora_r", str(args.lora_r),
        "--lora_alpha", str(args.lora_alpha),
        "--lora_dropout", str(args.lora_dropout),
        "--lora_bias", args.lora_bias,
        "--num_train_epochs", str(args.num_train_epochs),
        "--learning_rate", str(args.learning_rate),
        "--per_device_train_batch_size", str(args.per_device_train_batch_size),
        "--gradient_accumulation_steps", str(args.gradient_accumulation_steps),
        "--save_steps", str(args.save_steps),
        "--logging_steps", str(args.logging_steps),
        "--fp16", "True",
    ]


def print_configuration(args: argparse.Namespace, command: list[str]) -> None:
    print("CDChat LoRA training configuration")
    print(f"  model path:        {args.model_path}")
    print(f"  data path:         {args.data_path}")
    print(f"  image folder:      {args.image_folder}")
    print(f"  output directory:   {args.output_dir}")
    print(f"  LoRA:              r={args.lora_r}, alpha={args.lora_alpha}, dropout={args.lora_dropout}, bias={args.lora_bias}")
    print(f"  epochs:            {args.num_train_epochs}")
    print(f"  learning rate:     {args.learning_rate}")
    print(f"  batch size:        {args.per_device_train_batch_size}")
    print(f"  gradient steps:    {args.gradient_accumulation_steps}")
    print(f"  save/log steps:    {args.save_steps}/{args.logging_steps}")
    print(f"  vision tower:      {args.vision_tower}")
    print("  exact command:     " + subprocess.list2cmdline(command))


def main() -> int:
    args = build_parser().parse_args()
    command = build_command(args)
    print_configuration(args, command)

    if args.dry_run:
        print("Dry run: training was not started.")
        return 0

    if not torch.cuda.is_available():
        print("CUDA is unavailable; training was not started. CDChat LoRA training requires an NVIDIA CUDA GPU.")
        return 2

    if not CDCHAT_TRAIN_SCRIPT.is_file():
        print(f"CDChat training script does not exist: {CDCHAT_TRAIN_SCRIPT}")
        return 2

    print("CUDA is available; starting the existing CDChat training script.")
    completed = subprocess.run(command, cwd=PROJECT_ROOT)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())