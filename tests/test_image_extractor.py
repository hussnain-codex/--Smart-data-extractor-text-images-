import json
from types import SimpleNamespace

import pytest
from PIL import Image

import image_extractor


def create_test_image(path):
    Image.new("RGB", (20, 20), color="white").save(path)
    return path


def image_response(**overrides):
    data = {
        "image_type": "receipt",
        "description": "A small receipt",
        "detected_text": ["ABC Store"],
        "objects": ["receipt"],
        "key_details": {"vendor": "ABC Store"},
    }
    data.update(overrides)
    return SimpleNamespace(text=json.dumps(data))


def fake_client(responses):
    calls = []
    response_iter = iter(responses)

    def generate_content(**kwargs):
        calls.append(kwargs)
        response = next(response_iter)
        if isinstance(response, Exception):
            raise response
        return response

    client = SimpleNamespace(
        models=SimpleNamespace(generate_content=generate_content)
    )
    return client, calls


def test_analyze_image_returns_structured_result(tmp_path, monkeypatch):
    path = create_test_image(tmp_path / "receipt.png")
    client, calls = fake_client([image_response()])
    monkeypatch.setenv("GEMINI_MODEL", "test-model")
    monkeypatch.setattr(image_extractor, "create_image_client", lambda: client)

    result = image_extractor.analyze_image(str(path))

    assert result.image_type == "receipt"
    assert result.detected_text == ["ABC Store"]
    assert result.key_details == {"vendor": "ABC Store"}
    assert len(calls) == 1
    assert calls[0]["model"] == "test-model"


def test_missing_image_raises_before_client_creation(tmp_path, monkeypatch):
    def fail_if_called():
        pytest.fail("Client should not be created for a missing image")

    monkeypatch.setattr(image_extractor, "create_image_client", fail_if_called)

    with pytest.raises(FileNotFoundError, match="Image not found"):
        image_extractor.analyze_image(str(tmp_path / "missing.png"))


def test_invalid_image_raises_clear_error(tmp_path, monkeypatch):
    path = tmp_path / "not-an-image.png"
    path.write_text("not an image", encoding="utf-8")

    def fail_if_called():
        pytest.fail("Client should not be created for an invalid image")

    monkeypatch.setattr(image_extractor, "create_image_client", fail_if_called)

    with pytest.raises(ValueError, match="not a valid or supported image"):
        image_extractor.analyze_image(str(path))


def test_max_attempts_must_be_positive(tmp_path, monkeypatch):
    path = create_test_image(tmp_path / "receipt.png")

    def fail_if_called():
        pytest.fail("Client should not be created for invalid max_attempts")

    monkeypatch.setattr(image_extractor, "create_image_client", fail_if_called)

    with pytest.raises(ValueError, match="max_attempts must be at least 1"):
        image_extractor.analyze_image(str(path), max_attempts=0)


def test_temporary_api_failure_is_retried(tmp_path, monkeypatch):
    path = create_test_image(tmp_path / "receipt.png")
    client, calls = fake_client(
        [RuntimeError("temporary error"), image_response()]
    )
    monkeypatch.setattr(image_extractor, "create_image_client", lambda: client)
    monkeypatch.setattr(image_extractor.time, "sleep", lambda _: None)

    result = image_extractor.analyze_image(str(path), max_attempts=2)

    assert result.image_type == "receipt"
    assert len(calls) == 2


def test_repeated_api_failure_raises_runtime_error(tmp_path, monkeypatch):
    path = create_test_image(tmp_path / "receipt.png")
    client, calls = fake_client(
        [RuntimeError("temporary error"), RuntimeError("still failing")]
    )
    monkeypatch.setattr(image_extractor, "create_image_client", lambda: client)
    monkeypatch.setattr(image_extractor.time, "sleep", lambda _: None)

    with pytest.raises(RuntimeError, match="failed after 2 attempts"):
        image_extractor.analyze_image(str(path), max_attempts=2)

    assert len(calls) == 2


def test_invalid_model_json_raises_value_error(tmp_path, monkeypatch):
    path = create_test_image(tmp_path / "receipt.png")
    client, _ = fake_client([image_response(image_type=None)])
    monkeypatch.setattr(image_extractor, "create_image_client", lambda: client)

    with pytest.raises(ValueError, match="did not match the expected schema"):
        image_extractor.analyze_image(str(path))
