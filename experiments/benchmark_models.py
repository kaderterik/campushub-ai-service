
import csv
import json
import math
import platform
import resource
import statistics
import sys
import time
from pathlib import Path

from transformers import pipeline


# 1. Karşılaştıracağımız hazır modeller
MODELS = {
    "minilm": "MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli",
    "mdeberta": "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli",
    "mdeberta_2mil7": (
        "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"
    ),
}

if len(sys.argv) != 2 or sys.argv[1] not in MODELS:
    print("Kullanim:")
    print("python experiments/benchmark_models.py minilm")
    print("python experiments/benchmark_models.py mdeberta")
    print("python experiments/benchmark_models.py mdeberta_2mil7")
    sys.exit(1)

model_name = sys.argv[1]
model_id = MODELS[model_name]


# 2. RAM ölçüm fonksiyonu
def peak_ram_mb():
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    if platform.system() == "Darwin":
        return value / (1024 * 1024)

    return value / 1024


# 3. Veri setini ve V5 açıklamalarını yükle
project_dir = Path(__file__).resolve().parents[1]
data_dir = project_dir / "data" / "evaluation"

with open(
    data_dir / "CampusHub_60_Dengeli_Degerlendirme_v2.json",
    encoding="utf-8"
) as f:
    examples = json.load(f)

with open(
    data_dir / "CampusHub_Kategori_Aciklamalari_v5.json",
    encoding="utf-8"
) as f:
    config = json.load(f)

development = [
    item for item in examples
    if item["split"] == "development"
]

if not development:
    raise ValueError("Gelistirme veri seti bos!")

labels = config["labels"]
description_to_category = {
    description: category
    for category, description in labels.items()
}


# 4. Model yükleme süresini ölç
print(f"\nModel: {model_name}")
print("Model CPU üzerinde yükleniyor...")

ram_before = peak_ram_mb()

start_load = time.perf_counter()

classifier = pipeline(
    "zero-shot-classification",
    model=model_id,
    device="cpu"
)

loading_time = time.perf_counter() - start_load

ram_after_load = peak_ram_mb()


# 5. Isınma tahmini (ölçüme dahil değil)
print("Isinma tahmini yapiliyor...")

classifier(
    development[0]["text"],
    candidate_labels=list(labels.values()),
    hypothesis_template=config["hypothesis_template"],
    multi_label=False
)


# 6. Her etkinliğin inference süresini ölç
print("42 etkinlik siniflandiriliyor...")

inference_times = []
correct = 0

for item in development:
    start = time.perf_counter()

    result = classifier(
        item["text"],
        candidate_labels=list(labels.values()),
        hypothesis_template=config["hypothesis_template"],
        multi_label=False
    )

    elapsed = time.perf_counter() - start
    inference_times.append(elapsed)

    predicted = description_to_category[result["labels"][0]]
    expected = item["expected_category"]

    if predicted == expected:
        correct += 1


# 7. Performans istatistiklerini hesapla
total = len(development)

average_ms = statistics.mean(inference_times) * 1000

sorted_times = sorted(inference_times)
p95_index = math.ceil(0.95 * total) - 1
p95_ms = sorted_times[p95_index] * 1000

peak_ram = peak_ram_mb()
accuracy = correct / total


# 8. Sonuçları terminalde göster
print("\n" + "=" * 45)
print("BENCHMARK SONUCLARI")
print("=" * 45)

print(f"Model: {model_name}")
print(f"Dogruluk: {correct}/{total} ({accuracy:.2%})")

print(f"Yukleme suresi: {loading_time:.3f} saniye")
print(f"Ortalama inference: {average_ms:.2f} ms")
print(f"P95 inference: {p95_ms:.2f} ms")

print(f"Yukleme sonrasi peak RAM: {ram_after_load:.2f} MB")
print(f"Islem boyunca peak RAM: {peak_ram:.2f} MB")

print("=" * 45)


# 9. Sonuçları CSV tablosuna kaydet
csv_path = project_dir / "experiments" / "benchmark_results.csv"

fieldnames = [
    "model",
    "correct",
    "total",
    "accuracy_percent",
    "loading_seconds",
    "average_inference_ms",
    "p95_inference_ms",
    "peak_ram_mb",
]

new_row = {
    "model": model_name,
    "correct": correct,
    "total": total,
    "accuracy_percent": round(accuracy * 100, 2),
    "loading_seconds": round(loading_time, 3),
    "average_inference_ms": round(average_ms, 2),
    "p95_inference_ms": round(p95_ms, 2),
    "peak_ram_mb": round(peak_ram, 2),
}

rows = []

if csv_path.exists():
    with open(csv_path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

# Aynı model tekrar ölçülürse eski satırını güncelle
rows = [row for row in rows if row["model"] != model_name]
rows.append(new_row)

with open(csv_path, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"\nSonuclar kaydedildi: {csv_path}")
