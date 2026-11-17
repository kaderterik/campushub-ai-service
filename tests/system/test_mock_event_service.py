"""Grup 3 istemci taklidinin (scripts/mock_event_service.py) davranışı.

T19 hazırlığı: AI servisi kapalıyken veya yanıt vermezken Event Service tarafı
çökmemeli, sonucu 'unavailable' / 'timeout' olarak alıp devam edebilmelidir.
"""

import socket
import threading

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

    outcome = classify_event(f"http://127.0.0.1:{closed_port}", "Konser duyurusu", timeout=2)

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
