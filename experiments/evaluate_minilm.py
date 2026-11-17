
import json
from pathlib import Path
from transformers import pipeline

# 1. JSON dosyalarımızın bulunduğu klasör
data_dir = Path(__file__).resolve().parents[1] / "data" / "evaluation"

# 2. Etkinlik örneklerini oku
with open(data_dir / "CampusHub_60_Dengeli_Degerlendirme_v2.json", encoding="utf-8") as f:
    examples = json.load(f)

# 3. Kategori açıklamalarını oku
with open(data_dir / "CampusHub_Kategori_Aciklamalari_v2.json", encoding="utf-8") as f:
    config = json.load(f)

# 4. Yalnızca geliştirme örneklerini seç
development = [item for item in examples if item["split"] == "development"]

labels = config["labels"]
description_to_category = {
    description: category
    for category, description in labels.items()
}

# 5. Hazır MiniLM modelini yükle
print("MiniLM yükleniyor...")

classifier = pipeline(
    "zero-shot-classification",
    model="MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli",
    device="cpu"
)

# 6. Her etkinliği otomatik sınıflandır
correct = 0

for number, item in enumerate(development, start=1):
    result = classifier(
        item["text"],
        candidate_labels=list(labels.values()),
        hypothesis_template=config["hypothesis_template"],
        multi_label=False
    )

    predicted = description_to_category[result["labels"][0]]
    expected = item["expected_category"]

    if predicted == expected:
        correct += 1

    print(f"{number}/42 | Beklenen: {expected} | Tahmin: {predicted}")

# 7. Doğruluk oranını hesapla
accuracy = correct / len(development)

print("\n--- MINILM SONUÇLARI ---")
print(f"Doğru tahmin: {correct}/{len(development)}")
print(f"Accuracy: {accuracy:.2%}")
