
"""T14 - Güncel CampusHub modelinin CPU performans ölçümü."""

import json
import math
import platform
try:
    import resource
except ImportError:
    resource = None
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.models.classifier import (
    MODEL_ID,
    MODEL_REVISION,
    MDeBERTaClassifier,
)



def peak_ram_mb():
    """Python sürecinin en yüksek RAM kullanımını MB cinsinden döndürür."""

    if platform.system() == "Windows":
        try:
            import psutil
        except ImportError as exc:
            raise RuntimeError(
                "Windows RAM olcumu icin psutil gereklidir."
            ) from exc

        info = psutil.Process().memory_info()

        peak = getattr(info, "peak_wset", None)
        if peak is None:
            peak = getattr(info, "peak_rss", None)

        if peak is None:
            raise RuntimeError(
                "Windows peak RAM bilgisi alinamadi."
            )

        return peak / (1024 * 1024)

    if resource is None:
        raise RuntimeError("RAM olcumu bu sistemde desteklenmiyor.")

    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    if platform.system() == "Darwin":
        return value / (1024 * 1024)

    return value / 1024



def main():
    data_path = ROOT / "data/evaluation/CampusHub_421_GELISTIRME_DUZELTILMIS.json"

    with open(data_path, encoding="utf-8") as file:
        records = json.load(file)

    development = [
        item for item in records
        if item.get("split") == "development"
    ]

    if len(development) < 30:
        raise ValueError("En az 30 geliştirme kaydı gerekli.")

    # Final test verilerini kullanmıyoruz.
    texts = [item["text"] for item in development[:30]]

    print("Güncel mDeBERTa CPU benchmark başlıyor...", flush=True)

    classifier = MDeBERTaClassifier()

    initial_peak = peak_ram_mb()

    start = time.perf_counter()
    classifier.load()
    loading_seconds = time.perf_counter() - start

    loading_peak = peak_ram_mb()

    # İlk tahmin ısınma içindir, süre ölçümüne katılmaz.
    classifier.classify(texts[0])

    inference_times = []

    for index, text in enumerate(texts, 1):
        start = time.perf_counter()
        classifier.classify(text)
        elapsed_ms = (time.perf_counter() - start) * 1000
        inference_times.append(elapsed_ms)
        print(f"Ölçülen: {index}/30", flush=True)

    ordered = sorted(inference_times)
    p95_index = math.ceil(len(ordered) * 0.95) - 1

    results = {
        "model": MODEL_ID,
        "revision": MODEL_REVISION,
        "device": "cpu",
        "multi_label": True,
        "threshold": 0.70,
        "dataset": "development",
        "sample_count": len(texts),
        "loading_seconds": round(loading_seconds, 3),
        "average_inference_ms": round(
            statistics.mean(inference_times), 2
        ),
        "p95_inference_ms": round(ordered[p95_index], 2),
        "initial_process_peak_ram_mb": round(initial_peak, 2),
        "after_load_process_peak_ram_mb": round(loading_peak, 2),
        "overall_process_peak_ram_mb": round(peak_ram_mb(), 2),
        "system": platform.platform(),
    }

    output = ROOT / "experiments/results/benchmark_real_cpu.json"
    output.parent.mkdir(parents=True, exist_ok=True)

    with open(output, "w", encoding="utf-8") as file:
        json.dump(results, file, ensure_ascii=False, indent=2)

    print("\nT14 SONUÇLARI")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"\nKaydedildi: {output}")
    print("RAM değerleri modelin tek başına değil, Python sürecinin peak RAM değerleridir.")


if __name__ == "__main__":
    main()
