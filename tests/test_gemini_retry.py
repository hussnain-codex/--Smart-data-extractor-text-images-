from types import SimpleNamespace

import pytest
from google.genai.errors import ClientError, ServerError
from langchain_core.exceptions import ModelRateLimitError

import image_extractor


def server_error(code=503, status="UNAVAILABLE"):
    return ServerError(code, {"error": {"code": code, "status": status}})


def client_error(code, status):
    return ClientError(code, {"error": {"code": code, "status": status}})


def fake_request(outcomes):
    """Return a request function and the model names it was called with."""
    calls = []
    outcome_iter = iter(outcomes)

    def request(model_name):
        calls.append(model_name)
        outcome = next(outcome_iter)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    return request, calls


@pytest.fixture
def no_sleep(monkeypatch):
    monkeypatch.setattr(image_extractor.time, "sleep", lambda _: None)


def test_models_include_fallbacks_without_duplicates(monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "primary")
    monkeypatch.setenv(
        "GEMINI_FALLBACK_MODELS", " backup-a, primary,,backup-b "
    )

    assert image_extractor.gemini_models() == [
        "primary",
        "backup-a",
        "backup-b",
    ]


def test_default_model_is_used_when_nothing_is_configured():
    assert image_extractor.gemini_models() == ["gemini-3.5-flash"]


@pytest.mark.parametrize(
    ("error", "kind"),
    [
        (server_error(), image_extractor.TEMPORARY),
        (TimeoutError("timed out"), image_extractor.TEMPORARY),
        (client_error(429, "RESOURCE_EXHAUSTED"), image_extractor.QUOTA),
        (ModelRateLimitError("429"), image_extractor.QUOTA),
        (client_error(404, "NOT_FOUND"), image_extractor.MODEL_NOT_FOUND),
        (client_error(401, "UNAUTHENTICATED"), image_extractor.FATAL),
        (client_error(400, "INVALID_ARGUMENT"), image_extractor.FATAL),
    ],
)
def test_classify_gemini_error(error, kind):
    assert image_extractor.classify_gemini_error(error) == kind


def test_classify_follows_wrapped_cause():
    try:
        try:
            raise client_error(429, "RESOURCE_EXHAUSTED")
        except ClientError as inner:
            raise RuntimeError("wrapped") from inner
    except RuntimeError as outer:
        assert (
            image_extractor.classify_gemini_error(outer)
            == image_extractor.QUOTA
        )


def test_overloaded_model_falls_back_after_retries(monkeypatch, no_sleep):
    monkeypatch.setenv("GEMINI_MODEL", "busy")
    monkeypatch.setenv("GEMINI_FALLBACK_MODELS", "backup")
    request, calls = fake_request(
        [server_error(), server_error(), "ok"]
    )

    result = image_extractor.call_gemini(request, "Test", max_attempts=2)

    assert result == "ok"
    assert calls == ["busy", "busy", "backup"]


def test_quota_error_skips_to_fallback_without_retry(monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "no-quota")
    monkeypatch.setenv("GEMINI_FALLBACK_MODELS", "backup")
    monkeypatch.setattr(
        image_extractor.time,
        "sleep",
        lambda _: pytest.fail("Quota errors should not be retried."),
    )
    request, calls = fake_request(
        [client_error(429, "RESOURCE_EXHAUSTED"), "ok"]
    )

    assert image_extractor.call_gemini(request, "Test") == "ok"
    assert calls == ["no-quota", "backup"]


def test_missing_model_is_not_retried(monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "retired-model")
    monkeypatch.setattr(
        image_extractor.time,
        "sleep",
        lambda _: pytest.fail("Missing models should not be retried."),
    )
    request, calls = fake_request([client_error(404, "NOT_FOUND")])

    with pytest.raises(RuntimeError, match="not available to this API key"):
        image_extractor.call_gemini(request, "Test", max_attempts=3)

    assert calls == ["retired-model"]


def test_fatal_error_stops_without_trying_fallbacks(monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "primary")
    monkeypatch.setenv("GEMINI_FALLBACK_MODELS", "backup")
    request, calls = fake_request([client_error(401, "UNAUTHENTICATED")])

    with pytest.raises(RuntimeError, match="check GEMINI_API_KEY"):
        image_extractor.call_gemini(request, "Test")

    assert calls == ["primary"]


def test_all_models_failing_reports_each_reason(monkeypatch, no_sleep):
    monkeypatch.setenv("GEMINI_MODEL", "busy")
    monkeypatch.setenv("GEMINI_FALLBACK_MODELS", "no-quota")
    request, _ = fake_request(
        [server_error(), client_error(429, "RESOURCE_EXHAUSTED")]
    )

    with pytest.raises(RuntimeError) as raised:
        image_extractor.call_gemini(request, "Test", max_attempts=1)

    message = str(raised.value)
    assert "'busy' failed after 1 attempts" in message
    assert "'no-quota' rate limit or daily quota reached" in message


def test_value_error_is_not_retried(monkeypatch):
    request, calls = fake_request([ValueError("bad schema")])

    with pytest.raises(ValueError, match="bad schema"):
        image_extractor.call_gemini(request, "Test", max_attempts=3)

    assert len(calls) == 1


def test_retry_delay_grows_and_is_capped():
    assert 5 <= image_extractor.retry_delay(1) < 6
    assert 15 <= image_extractor.retry_delay(2) < 16
    assert 60 <= image_extractor.retry_delay(5) < 61


def test_invoice_extraction_uses_fallback_model(tmp_path, monkeypatch):
    from PIL import Image

    path = tmp_path / "receipt.png"
    Image.new("RGB", (20, 20), color="white").save(path)
    monkeypatch.setenv("GEMINI_MODEL", "no-quota")
    monkeypatch.setenv("GEMINI_FALLBACK_MODELS", "backup")
    created = []

    def create_invoice_model(model_name=None):
        created.append(model_name)

        def invoke(_):
            if model_name == "no-quota":
                raise ModelRateLimitError("429 RESOURCE_EXHAUSTED")
            raise ValueError("reached backup model")

        return SimpleNamespace(invoke=invoke)

    monkeypatch.setattr(
        image_extractor, "create_invoice_model", create_invoice_model
    )

    with pytest.raises(ValueError, match="reached backup model"):
        image_extractor.extract_invoice_from_image(str(path))

    assert created == ["no-quota", "backup"]
