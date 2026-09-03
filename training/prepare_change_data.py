"""Prepare bi-temporal change data for CDChat.

The source metadata is intentionally kept outside this repository. Records may
use ``image`` or ``img_id`` for a shared basename, or provide explicit ``t1``,
``t2``, and ``label`` paths. Questions and answers can be supplied as
``question``/``answer`` fields or as CDChat-style ``conversations``.
"""

import argparse
import json
import shutil
from pathlib import Path
from typing import Any


def _records(metadata: Any) -> list[dict[str, Any]]:
    if isinstance(metadata, list):
        records = metadata
    elif isinstance(metadata, dict):
        records = metadata.get("data", metadata.get("samples"))
    else:
        records = None

    if not isinstance(records, list) or not all(isinstance(item, dict) for item in records):
        raise ValueError("Metadata must be a list of sample objects or an object with a 'data'/'samples' list.")
    return records


def _path(record: dict[str, Any], key: str, source_root: Path, shared_name: str | None) -> Path:
    value = record.get(key)
    if value is None and shared_name is not None:
        value = shared_name
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Record is missing a non-empty '{key}' path.")
    return (source_root / value).resolve() if not Path(value).is_absolute() else Path(value).resolve()


def _conversation(record: dict[str, Any]) -> list[dict[str, str]]:
    conversations = record.get("conversations")
    if isinstance(conversations, list) and conversations:
        return conversations

    question = record.get("question")
    answer = record.get("answer")
    if not isinstance(question, str) or not question.strip():
        raise ValueError("Record must provide 'question' or a non-empty 'conversations' list.")
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("Records using 'question' must provide a non-empty 'answer'.")
    return [
        {"from": "human", "value": "<image>\n" + question.strip()},
        {"from": "gpt", "value": answer.strip()},
    ]


def prepare_change_data(
    metadata_path: str | Path,
    source_root: str | Path,
    output_root: str | Path,
    output_json: str | Path | None = None,
    copy_files: bool = False,
) -> Path:
    metadata_path = Path(metadata_path).resolve()
    source_root = Path(source_root).resolve()
    output_root = Path(output_root).resolve()
    if not metadata_path.is_file():
        raise FileNotFoundError(f"Metadata file does not exist: {metadata_path}")

    with metadata_path.open("r", encoding="utf-8") as metadata_file:
        records = _records(json.load(metadata_file))

    for folder in ("A", "B", "label"):
        (output_root / folder).mkdir(parents=True, exist_ok=True)

    prepared = []
    for index, record in enumerate(records):
        shared_name = record.get("image", record.get("img_id"))
        try:
            source_t1 = _path(record, "t1", source_root, shared_name)
            source_t2 = _path(record, "t2", source_root, shared_name)
            source_label = _path(record, "label", source_root, shared_name)
            for source in (source_t1, source_t2, source_label):
                if not source.is_file():
                    raise FileNotFoundError(f"Referenced file does not exist: {source}")
            name = Path(shared_name).name if isinstance(shared_name, str) else source_t1.name
            if not name:
                raise ValueError("Record needs an image name via 'image', 'img_id', or 't1'.")
            if copy_files:
                shutil.copy2(source_t1, output_root / "A" / name)
                shutil.copy2(source_t2, output_root / "B" / name)
                shutil.copy2(source_label, output_root / "label" / name)
            prepared.append({"id": record.get("id", index), "image": name, "conversations": _conversation(record)})
        except (FileNotFoundError, ValueError) as error:
            raise ValueError(f"Invalid record {index}: {error}") from error

    destination = Path(output_json) if output_json else output_root / "cdchat_change.json"
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as output_file:
        json.dump(prepared, output_file, indent=2)
        output_file.write("\n")
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", required=True, help="Source CDVQA/change metadata JSON file.")
    parser.add_argument("--source-root", required=True, help="Root used to resolve relative source image paths.")
    parser.add_argument("--output-root", default="data/change", help="CDChat image root (default: data/change).")
    parser.add_argument("--output-json", help="Output CDChat JSON path (default: <output-root>/cdchat_change.json).")
    parser.add_argument("--copy", action="store_true", help="Copy validated files into output A/B/label folders.")
    args = parser.parse_args()
    try:
        destination = prepare_change_data(
            args.metadata, args.source_root, args.output_root, args.output_json, args.copy
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    print(f"Prepared {destination}")


if __name__ == "__main__":
    main()