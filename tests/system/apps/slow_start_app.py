"""Model yüklemesi yavaş süren servis (T26 bloklayıcı yükleme testi için).

FakeClassifier.load() SLOW_LOAD_SECONDS kadar bekler; böylece gerçek modelin
uzun yüklenme süresi taklit edilir.
"""

import os
import time

from app.services.fake_classifier import FakeClassifier

_original_load = FakeClassifier.load


def _slow_load(self) -> None:
    time.sleep(float(os.getenv("SLOW_LOAD_SECONDS", "2")))
    _original_load(self)


FakeClassifier.load = _slow_load

from app.main import app  # noqa: E402,F401
