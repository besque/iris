"""Evaluate a change model on CDVQA-style bi-temporal samples."""

import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable


def _load_records(metadata_path: Path) -> list[dict[str, Any]]:
    with metadata_path.open("r", encoding="utf-8") as metadata_file:
        data = json.load(metadata_file)
    records = data if isinstance(data, list) else data.get("data", data.get("samples"))
    if not isinstance(records, list) or not all(isinstance(item, dict) for item in records):
        raise ValueError("Metadata must be a list of sample objects or an object with a 'data'/'samples' list.")
    return records


def _question(record: dict[str, Any]) -> str:
    question = record.get("question")
    if isinstance(question, str) and question.strip():
        return question.strip()
    for message in record.get("conversations", []):
        if message.get("from", "").lower() == "human":
            value = message.get("value", "")
            if isinstance(value, str):
                return value.replace("<image>", "", 1).strip()
    raise ValueError("Sample is missing a non-empty 'question' or human conversation message.")


def _ground_truth(record: dict[str, Any]) -> str | None:
    answer = record.get("answer", record.get("ground_truth"))
    if isinstance(answer, str):
        return answer
    answers = record.get("answers")
    if isinstance(answers, list) and all(isinstance(item, str) for item in answers):
        return answers[0] if answers else None
    for message in reversed(record.get("conversations", [])):
        if message.get("from", "").lower() == "gpt" and isinstance(message.get("value"), str):
            return message["value"]
    return None


def _image_paths(record: dict[str, Any], image_root: Path) -> tuple[Path, Path]:
    shared_name = record.get("image", record.get("img_id"))
    t1 = record.get("t1", shared_name)
    t2 = record.get("t2", shared_name)
    if not isinstance(t1, str) or not isinstance(t2, str) or not t1.strip() or not t2.strip():
        raise ValueError("Sample must provide 'image'/'img_id' or non-empty 't1' and 't2' paths.")
    paths = []
    for value, folder in ((t1, "A"), (t2, "B")):
        path = Path(value)
        paths.append(path.resolve() if path.is_absolute() else (image_root / folder / path).resolve())
    return paths[0], paths[1]


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", text.casefold())).strip()


def exact_match_accuracy(predictions: Iterable[dict[str, Any]]) -> float | None:
    scored = [item for item in predictions if isinstance(item.get("answer"), str) and isinstance(item.get("ground_truth"), str)]
    if not scored:
        return None
    return sum(_normalise(item["answer"]) == _normalise(item["ground_truth"]) for item in scored) / len(scored)


def evaluate_cdvqa(
    metadata_path: str | Path,
    image_root: str | Path,
    output_path: str | Path,
    model: Any = None,
    model_path: str | Path | None = None,
    model_base: str | Path | None = None,
    mm_projector_path: str | Path | None = None,
    device: str = "cuda",
) -> dict[str, Any]:
    metadata_path = Path(metadata_path).resolve()
    image_root = Path(image_root).resolve()
    output_path = Path(output_path).resolve()
    if not metadata_path.is_file():
        raise FileNotFoundError(f"Metadata file does not exist: {metadata_path}")

    records = _load_records(metadata_path)
    samples = []
    for index, record in enumerate(records):
        try:
            image_t1, image_t2 = _image_paths(record, image_root)
            if not image_t1.is_file() or not image_t2.is_file():
                raise FileNotFoundError(f"Missing T1/T2 image for sample {index}: {image_t1}, {image_t2}")
            samples.append((record, image_t1, image_t2, _question(record)))
        except (FileNotFoundError, ValueError) as error:
            raise ValueError(f"Invalid sample {index}: {error}") from error

    if model is None:
        from backend.tools.change.model import ChangeModel

        model = ChangeModel(
            model_path=model_path,
            model_base=model_base,
            mm_projector_path=mm_projector_path,
            device=device,
        )
        model.load()

    predictions = []
    for index, (record, image_t1, image_t2, question) in enumerate(samples):
        answer = model.predict(image_t1=image_t1, image_t2=image_t2, question=question)
        predictions.append({
            "id": record.get("id", index),
            "image": record.get("image", record.get("img_id")),
            "question": question,
            "answer": answer,
            "ground_truth": _ground_truth(record),
        })

    result = {
        "predictions": predictions,
        "exact_match_accuracy": exact_match_accuracy(predictions),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix.lower() == ".jsonl":
        with output_path.open("w", encoding="utf-8") as output_file:
            for prediction in predictions:
                output_file.write(json.dumps(prediction) + "\n")
    else:
        with output_path.open("w", encoding="utf-8") as output_file:
            json.dump(result, output_file, indent=2)
            output_file.write("\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", required=True, help="CDVQA question/answer metadata JSON file.")
    parser.add_argument("--image-root", required=True, help="Root containing CDChat-compatible A/ and B/ folders.")
    parser.add_argument("--output", required=True, help="Prediction output path (.json or .jsonl).")
    parser.add_argument("--model-path", required=True, help="CDChat checkpoint path on the GPU machine.")
    parser.add_argument("--model-base", help="Base language-model path for LoRA checkpoints.")
    parser.add_argument("--mm-projector-path", help="Optional pretrained multimodal projector path.")
    parser.add_argument("--device", default="cuda", help="CUDA device for CDChat inference (default: cuda).")
    args = parser.parse_args()
    try:
        result = evaluate_cdvqa(
            args.metadata,
            args.image_root,
            args.output,
            model_path=args.model_path,
            model_base=args.model_base,
            mm_projector_path=args.mm_projector_path,
            device=args.device,
        )
    except (OSError, ValueError, RuntimeError) as error:
        parser.error(str(error))
    print(json.dumps({"exact_match_accuracy": result["exact_match_accuracy"]}))


if __name__ == "__main__":
    main()