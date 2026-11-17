"""T18 / T26: Servisin başlangıç yaşam döngüsü, gerçek süreç üzerinde.

- Model yüklenirken servis trafik kabul etmez (bağlantı kurulamaz, 503 de dönmez).
- Yükleme bittiğinde ilk başarılı /health yanıtı 200 UP olur.
- Yükleme başarısız olursa süreç kapanır (fail-fast).
"""

import time

import httpx

from tests.system.conftest import free_port, start_server, stop_server, wait_until_healthy


def test_no_traffic_until_model_loaded():
    port = free_port()
    base_url = f"http://127.0.0.1:{port}"
    process = start_server("slow_start_app:app", port, {"SLOW_LOAD_SECONDS": "3"})
    try:
        time.sleep(1.0)  # süreç başladı ama model hâlâ yükleniyor
        try:
            early = httpx.get(f"{base_url}/health", timeout=1.0)
        except httpx.TransportError:
            early = None
        assert early is None, "Model yüklenirken servis istek kabul etmemeli"

        wait_until_healthy(base_url, process)
        response = httpx.get(f"{base_url}/health")
        assert response.status_code == 200
        assert response.json()["status"] == "UP"
    finally:
        stop_server(process)


def test_process_exits_when_model_load_fails():
    port = free_port()
    process = start_server("failing_load_app:app", port)
    try:
        exit_code = process.wait(timeout=30)
        output = process.stdout.read().decode(errors="replace")
    finally:
        stop_server(process)

    assert exit_code != 0
    assert "Application startup failed" in output
