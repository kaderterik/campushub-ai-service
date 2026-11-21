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

# docs/ai-classify-contract.md ile aynı kategori seti. Bu betik dış istemciyi
# (Grup 3) taklit ettiği için app/ paketine bağımlı değildir.
VALID_CATEGORIES = frozenset({"TECHNOLOGY", "SPORT", "ART", "CAREER", "SOCIAL", "OTHER"})
MAX_PREDICTIONS = 5

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
    except httpx.ConnectTimeout as exc:
        # Bağlantı hiç kurulamadı (Windows'ta kapalı port da bu şekilde görünebilir):
        # servis kapalı kabul edilir.
        return ClassifyOutcome(status="unavailable", latency_ms=_elapsed(started), detail=type(exc).__name__)
    except httpx.TimeoutException as exc:
        # Bağlantı kuruldu ama yanıt süresinde gelmedi.
        return ClassifyOutcome(status="timeout", latency_ms=_elapsed(started), detail=type(exc).__name__)
    except httpx.TransportError as exc:
        return ClassifyOutcome(status="unavailable", latency_ms=_elapsed(started), detail=type(exc).__name__)

    latency = _elapsed(started)
    if response.status_code == 200:
        try:
            predictions = _parse_predictions(response.json())
        except ValueError as exc:
            # 200 geldi ama yanıt sözleşmeye uymuyor: çökmeden "error" dön.
            return ClassifyOutcome(status="error", http_status=200, latency_ms=latency, detail=f"invalid response: {exc}")
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


def _parse_predictions(body: object) -> list[dict]:
    """Yanıtı docs/ai-classify-contract.md'ye göre doğrular; uymazsa ValueError."""
    if not isinstance(body, dict) or "predictions" not in body:
        raise ValueError("'predictions' field missing")
    predictions = body["predictions"]
    if not isinstance(predictions, list) or not predictions:
        raise ValueError("'predictions' must be a non-empty list")
    if len(predictions) > MAX_PREDICTIONS:
        raise ValueError(f"at most {MAX_PREDICTIONS} predictions are allowed")
    seen: set[str] = set()
    for item in predictions:
        if not isinstance(item, dict):
            raise ValueError("prediction must be an object")
        category = item.get("category")
        confidence = item.get("confidence")
        if not isinstance(category, str) or not category:
            raise ValueError("prediction 'category' must be a non-empty string")
        if category not in VALID_CATEGORIES:
            raise ValueError(f"unknown category: {category!r}")
        if category in seen:
            raise ValueError(f"duplicate category: {category!r}")
        seen.add(category)
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            raise ValueError("prediction 'confidence' must be a number between 0 and 1")
    if "OTHER" in seen and len(seen) > 1:
        raise ValueError("OTHER must not be combined with other categories")
    return predictions


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
