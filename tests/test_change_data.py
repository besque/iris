import json

from evaluation.eval_cdvqa import evaluate_cdvqa
from training.prepare_change_data import prepare_change_data


class FakeChangeModel:
    def predict(self, image_t1, image_t2, question):
        assert image_t1.name == "scene.png"
        assert image_t2.name == "scene.png"
        return "New buildings appeared."


def _write_source_files(source_root):
    for folder in ("source_a", "source_b", "source_label"):
        (source_root / folder).mkdir()
        (source_root / folder / "scene.png").write_bytes(b"test")


def test_prepare_change_data_emits_cdchat_records_without_copying(tmp_path):
    source_root = tmp_path / "source"
    source_root.mkdir()
    _write_source_files(source_root)
    metadata = source_root / "metadata.json"
    metadata.write_text(json.dumps([{
        "image": "scene.png",
        "t1": "source_a/scene.png",
        "t2": "source_b/scene.png",
        "label": "source_label/scene.png",
        "question": "What changed?",
        "answer": "New buildings appeared.",
    }]), encoding="utf-8")

    output_root = tmp_path / "change"
    output_json = prepare_change_data(metadata, source_root, output_root)

    prepared = json.loads(output_json.read_text(encoding="utf-8"))
    assert prepared[0]["image"] == "scene.png"
    assert prepared[0]["conversations"][0]["from"] == "human"
    assert not (output_root / "A" / "scene.png").exists()


def test_evaluate_cdvqa_uses_fake_model_and_scores_answer(tmp_path):
    image_root = tmp_path / "change"
    for folder in ("A", "B"):
        (image_root / folder).mkdir(parents=True)
        (image_root / folder / "scene.png").write_bytes(b"test")
    metadata = tmp_path / "questions.json"
    metadata.write_text(json.dumps([{
        "img_id": "scene.png",
        "question": "What changed?",
        "answer": "New buildings appeared.",
    }]), encoding="utf-8")

    result = evaluate_cdvqa(metadata, image_root, tmp_path / "predictions.json", FakeChangeModel())

    assert result["exact_match_accuracy"] == 1.0
    assert result["predictions"][0]["answer"] == "New buildings appeared."