import base64
import builtins
from datetime import date
from io import BytesIO
from types import SimpleNamespace

import pytest
from PIL import Image
from langchain_core.exceptions import ModelRateLimitError

import image_extractor
from schemas import Invoice, LineItem


def test_missing_langchain_gemini_package_has_install_instructions(monkeypatch):
    original_import = builtins.__import__

    def import_without_gemini_integration(name, *args, **kwargs):
        if name == "langchain_google_genai":
            raise ModuleNotFoundError(
                "No module named 'langchain_google_genai'",
                name=name,
            )
        return original_import(name, *args, **kwargs)

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        builtins,
        "__import__",
        import_without_gemini_integration,
    )

    with pytest.raises(
        ModuleNotFoundError,
        match="Install project dependencies with",
    ):
        image_extractor.create_invoice_model()


def test_invoice_model_defaults_to_gemini_35_flash(monkeypatch):
    import langchain_google_genai

    captured = {}

    class FakeChatModel:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        def with_structured_output(self, schema):
            captured["schema"] = schema
            return object()

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.setattr(
        langchain_google_genai,
        "ChatGoogleGenerativeAI",
        FakeChatModel,
    )

    image_extractor.create_invoice_model()

    assert captured["model"] == "gemini-3.5-flash"
    assert captured["schema"] is Invoice


def create_test_image(path, size=(2048, 1024)):
    Image.new("RGB", size, color="white").save(path)
    return path


def make_invoice():
    return Invoice(
        vendor="ABC Store",
        invoice_date=date.today(),
        items=[LineItem(name="Milk", quantity=2, price=250)],
        total=500,
        currency="PKR",
    )


def test_extract_invoice_sends_resized_multimodal_message(
    tmp_path,
    monkeypatch,
):
    path = create_test_image(tmp_path / "receipt.png")
    calls = []

    def invoke(messages):
        calls.append(messages)
        return make_invoice()

    monkeypatch.setattr(
        image_extractor,
        "create_invoice_model",
        lambda _model_name=None: SimpleNamespace(invoke=invoke),
    )

    result = image_extractor.extract_invoice_from_image(str(path))

    assert result.vendor == "ABC Store"
    assert len(calls) == 1
    content = calls[0][0].content
    assert content[0]["type"] == "text"
    assert content[1]["type"] == "image_url"

    data_url = content[1]["image_url"]["url"]
    encoded_image = data_url.split(",", 1)[1]
    image_bytes = base64.b64decode(encoded_image)
    with Image.open(BytesIO(image_bytes)) as sent_image:
        assert max(sent_image.size) == 1024


def test_invoice_image_retries_temporary_api_failure(tmp_path, monkeypatch):
    path = create_test_image(tmp_path / "receipt.png")
    responses = iter([RuntimeError("503 UNAVAILABLE"), make_invoice()])
    calls = []

    def invoke(messages):
        calls.append(messages)
        response = next(responses)
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(
        image_extractor,
        "create_invoice_model",
        lambda _model_name=None: SimpleNamespace(invoke=invoke),
    )
    monkeypatch.setattr(image_extractor.time, "sleep", lambda _: None)

    result = image_extractor.extract_invoice_from_image(
        str(path),
        max_attempts=2,
    )

    assert result.total == 500
    assert len(calls) == 2


def test_invoice_image_does_not_retry_rate_limit_or_quota(
    tmp_path,
    monkeypatch,
):
    path = create_test_image(tmp_path / "receipt.png")
    calls = []

    def invoke(_):
        calls.append(None)
        raise ModelRateLimitError("429 RESOURCE_EXHAUSTED")

    monkeypatch.setattr(
        image_extractor,
        "create_invoice_model",
        lambda _model_name=None: SimpleNamespace(invoke=invoke),
    )
    monkeypatch.setattr(
        image_extractor.time,
        "sleep",
        lambda _: pytest.fail("Rate-limited requests should not be retried."),
    )

    with pytest.raises(
        RuntimeError,
        match="Further retries will not help right now",
    ):
        image_extractor.extract_invoice_from_image(
            str(path),
            max_attempts=3,
        )

    assert len(calls) == 1


def test_invoice_image_failure_names_configured_model(tmp_path, monkeypatch):
    path = create_test_image(tmp_path / "receipt.png")
    monkeypatch.setenv("GEMINI_MODEL", "test-model")
    monkeypatch.setattr(
        image_extractor,
        "create_invoice_model",
        lambda _model_name=None: SimpleNamespace(
            invoke=lambda _: (_ for _ in ()).throw(
                RuntimeError("503 UNAVAILABLE")
            )
        ),
    )
    monkeypatch.setattr(image_extractor.time, "sleep", lambda _: None)

    with pytest.raises(RuntimeError, match="test-model.*failed after 1 attempts"):
        image_extractor.extract_invoice_from_image(
            str(path),
            max_attempts=1,
        )


def test_invoice_image_missing_file_does_not_create_model(tmp_path, monkeypatch):
    def fail_if_called():
        pytest.fail("Gemini model should not be created for a missing image")

    monkeypatch.setattr(image_extractor, "create_invoice_model", fail_if_called)

    with pytest.raises(FileNotFoundError, match="Image not found"):
        image_extractor.extract_invoice_from_image(
            str(tmp_path / "missing.png")
        )
