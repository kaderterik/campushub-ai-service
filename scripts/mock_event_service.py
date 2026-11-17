"""Grup 3 Event Service'ini taklit eden basit istemci (T18 / T19 hazırlığı).

Etkinlik metinlerini AI servisine gönderir, kategorileri ve gecikmeyi yazdırır.
AI servisi kapalıysa veya zaman aşımına uğrarsa hata fırlatmaz; Event Service'in
etkinliği kategorisiz kaydedip devam edebileceği bir sonuç döndürür.

Kullanım:
    python scripts/mock_event_service.py
    python scripts/mock_event_service.py --url http://127.0.0.1:8005 --timeout 5
    python scripts/mock_event_service.py --text "Bahar şenliği konseri"
"""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass, field

import httpx

DEFAULT_URL = "http://127.0.0.1:8005"
DEFAULT_TIMEOUT = 5.0

SAMPLE_EVENTS = [
    "Yazılım stajı başvuruları başladı, kariyer günlerine davetlisiniz.",
    "Kampüs futbol turnuvası için takım kayıtları açıldı.",
    "Bahar şenliğinde öğrenci korosu konser verecek.",
    "Gönüllü kan bağışı kampanyası kütüphane önünde yapılacak.",
    "Ders kayıt yenileme işlemleri için son gün cuma.",
]


@dataclass
class ClassifyOutcome:
    """AI servisine yapılan bir çağrının Event Service açısından sonucu."""

    status: str  # "ok", "unavailable", "timeout", "error"
    categories: list[str] = field(default_factory=list)
    predictions: list[dict] = field(default_factory=list)
    http_status: int | None = None
    latency_ms: float = 0.0
    detail: str = ""


def classify_event(base_url: str, text: str, timeout: float = DEFAULT_TIMEOUT) -> ClassifyOutcome:
    started = time.perf_counter()
    try:
        response = httpx.post(f"{base_url}/ai/classify", json={"text": text}, timeout=timeout)
    except httpx.TimeoutException as exc:
        return ClassifyOutcome(status="timeout", latency_ms=_elapsed(started), detail=type(exc).__name__)
    except httpx.TransportError as exc:
        return ClassifyOutcome(status="unavailable", latency_ms=_elapsed(started), detail=type(exc).__name__)

    latency = _elapsed(started)
    if response.status_code == 200:
        predictions = response.json()["predictions"]
        return ClassifyOutcome(
            status="ok",
            categories=[item["category"] for item in predictions],
            predictions=predictions,
            http_status=200,
            latency_ms=latency,
        )
    if response.status_code == 503:
        return ClassifyOutcome(status="unavailable", http_status=503, latency_ms=latency, detail=response.text)
    return ClassifyOutcome(status="error", http_status=response.status_code, latency_ms=latency, detail=response.text)


def _elapsed(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Grup 3 Event Service taklidi")
    parser.add_argument("--url", default=DEFAULT_URL, help=f"AI servis adresi (varsayılan {DEFAULT_URL})")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="İstek zaman aşımı (sn)")
    parser.add_argument("--text", action="append", help="Gönderilecek etkinlik metni (birden fazla verilebilir)")
    args = parser.parse_args()

    for text in args.text or SAMPLE_EVENTS:
        outcome = classify_event(args.url, text, args.timeout)
        if outcome.status == "ok":
            scores = ", ".join(f"{p['category']} {p['confidence']:.2f}" for p in outcome.predictions)
            print(f"[OK  {outcome.latency_ms:>7.1f} ms] {text}\n    -> {scores}")
        else:
            print(f"[{outcome.status.upper()} {outcome.latency_ms:>7.1f} ms] {text}\n    -> etkinlik kategorisiz kaydedilir ({outcome.detail})")


if __name__ == "__main__":
    main()
