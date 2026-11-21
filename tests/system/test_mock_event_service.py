"""Grup 3 istemci taklidinin (scripts/mock_event_service.py) davranışı.

T19 hazırlığı: AI servisi kapalıyken veya yanıt vermezken Event Service tarafı
çökmemeli, sonucu 'unavailable' / 'timeout' olarak alıp devam edebilmelidir.
"""

import socket
import threading

import httpx
import pytest

from scripts.mock_event_service import classify_event
from tests.system.conftest import free_port


def test_client_gets_categories_from_running_service(running_service):
    outcome = classify_event(running_service, "Yazılım stajı başvuruları başladı")

    assert outcome.status == "ok"
    assert outcome.http_status == 200
    assert outcome.categories
    assert outcome.latency_ms >= 0


def test_client_handles_service_down():
    closed_port = free_port()  # bu portta dinleyen kimse yok

    outcome = classify_event(f"http://127.0.0.1:{closed_port}", "Konser duyurusu", timeout=5)

    assert outcome.status == "unavailable"
    assert outcome.categories == []


def test_client_handles_timeout():
    # Bağlantıyı kabul edip hiç yanıt vermeyen sunucu
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen()
    port = server.getsockname()[1]
    accepted = []
    stop = threading.Event()

    def accept_and_hang():
        server.settimeout(5)
        try:
            conn, _ = server.accept()
            accepted.append(conn)
            stop.wait(5)
        except OSError:
            pass

    thread = threading.Thread(target=accept_and_hang, daemon=True)
    thread.start()
    try:
        outcome = classify_event(f"http://127.0.0.1:{port}", "Spor turnuvası", timeout=0.5)
    finally:
        stop.set()
        for conn in accepted:
            conn.close()
        server.close()

    assert outcome.status == "timeout"
    assert outcome.categories == []


def test_connect_timeout_counts_as_unavailable(monkeypatch):
    # Windows'ta kapalı porta bağlanmak ConnectTimeout olarak görünebilir.
    def raise_connect_timeout(*args, **kwargs):
        raise httpx.ConnectTimeout("connect timed out")

    monkeypatch.setattr(httpx, "post", raise_connect_timeout)

    outcome = classify_event("http://127.0.0.1:9", "Konser duyurusu", timeout=1)

    assert outcome.status == "unavailable"


@pytest.mark.parametrize(
    "body",
    [
        b'{"categories": ["SPORT"]}',  # predictions alanı yok
        b'{"predictions": []}',  # boş liste
        b'{"predictions": "SPORT"}',  # liste değil
        b'{"predictions": [{"category": "SPORT"}]}',  # confidence yok
        b'{"predictions": [{"category": "SPORT", "confidence": 1.7}]}',  # aralık dışı
        b'[1, 2, 3]',  # nesne değil
        b'<html>proxy error</html>',  # JSON değil
        b'{"predictions": [{"category": "MUSIC", "confidence": 0.9}]}',  # bilinmeyen kategori
        b'{"predictions": [{"category": "technology", "confidence": 0.9}]}',  # küçük harf: bilinmeyen
        b'{"predictions": [{"category": "SPORT", "confidence": 0.9}, {"category": "SPORT", "confidence": 0.8}]}',  # tekrar
        b'{"predictions": [{"category": "OTHER", "confidence": 0.8}, {"category": "SPORT", "confidence": 0.75}]}',  # OTHER + başka
        b'{"predictions": [{"category": "TECHNOLOGY", "confidence": 0.9}, {"category": "OTHER", "confidence": 0.7}]}',  # başka + OTHER
        b'{"predictions": [{"category": "TECHNOLOGY", "confidence": 0.9}, {"category": "SPORT", "confidence": 0.9}, {"category": "ART", "confidence": 0.9}, {"category": "CAREER", "confidence": 0.9}, {"category": "SOCIAL", "confidence": 0.9}, {"category": "SOCIAL", "confidence": 0.9}]}',  # 5'ten fazla
    ],
)
def test_client_handles_malformed_200_response(monkeypatch, body):
    def fake_post(url, **kwargs):
        return httpx.Response(200, content=body, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", fake_post)

    outcome = classify_event("http://ai-service:8005", "Spor turnuvası")

    assert outcome.status == "error"
    assert outcome.http_status == 200
    assert outcome.categories == []
    assert outcome.detail.startswith("invalid response")


@pytest.mark.parametrize(
    "body, expected",
    [
        (b'{"predictions": [{"category": "OTHER", "confidence": 0.76}]}', ["OTHER"]),
        (b'{"predictions": [{"category": "CAREER", "confidence": 0.94}, {"category": "TECHNOLOGY", "confidence": 0.83}]}', ["CAREER", "TECHNOLOGY"]),
        (
            b'{"predictions": [{"category": "TECHNOLOGY", "confidence": 0.9}, {"category": "SPORT", "confidence": 0.8}, {"category": "ART", "confidence": 0.8}, {"category": "CAREER", "confidence": 0.7}, {"category": "SOCIAL", "confidence": 0.7}]}',
            ["TECHNOLOGY", "SPORT", "ART", "CAREER", "SOCIAL"],
        ),
    ],
)
def test_client_accepts_valid_contract_responses(monkeypatch, body, expected):
    def fake_post(url, **kwargs):
        return httpx.Response(200, content=body, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", fake_post)

    outcome = classify_event("http://ai-service:8005", "Etkinlik")

    assert outcome.status == "ok"
    assert outcome.categories == expected


def test_client_category_set_matches_service_contract():
    # İstemcinin kabul ettiği kategoriler servisin sözleşmesiyle aynı kalmalı.
    from typing import get_args

    from app.contracts import Category
    from scripts.mock_event_service import VALID_CATEGORIES

    assert VALID_CATEGORIES == set(get_args(Category))
