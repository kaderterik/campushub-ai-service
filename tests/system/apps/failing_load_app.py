"""Model yüklemesi başarısız olan servis (fail-fast davranışı testi için)."""

from app.exceptions import ModelUnavailableError
from app.services.fake_classifier import FakeClassifier


def _failing_load(self) -> None:
    raise ModelUnavailableError("simulated model load failure")


FakeClassifier.load = _failing_load

from app.main import app  # noqa: E402,F401
