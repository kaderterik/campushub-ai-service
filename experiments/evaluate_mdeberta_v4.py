
import json
from pathlib import Path
from transformers import pipeline


# 1. JSON dosyalarının bulunduğu klasör
data_dir = Path(__file__).resolve().parents[1] / "data" / "evaluation"


# 2. Etkinlik örneklerini oku
with open(
    data_dir / "CampusHub_60_Dengeli_Degerlendirme_v2.json",
    encoding="utf-8"
) as f:
    examples = json.load(f)


# 3. Kategori açıklamalarını oku
with open(
    data_dir / "CampusHub_Kategori_Aciklamalari_v4.json",
    encoding="utf-8"
) as f:
    config = json.load(f)


# 4. Yalnızca geliştirme örneklerini seç
development = [
    item for item in examples
    if item["split"] == "development"
]

labels = config["labels"]

description_to_category = {
    description: category
    for category, description in labels.items()
}


# 5. mDeBERTa modelini yükle
print("mDeBERTa yükleniyor...")

classifier = pipeline(
    "zero-shot-classification",
    model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli",
    device="cpu"
)


# 6. Etkinlikleri sınıflandır ve hataları incele
correct = 0
total = len(development)

for number, item in enumerate(development, start=1):

    result = classifier(
        item["text"],
        candidate_labels=list(labels.values()),
        hypothesis_template=config["hypothesis_template"],
        multi_label=False
    )

    predicted_label = result["labels"][0]
    predicted = description_to_category[predicted_label]

    expected = item["expected_category"]

    # Doğru tahminleri say
    if predicted == expected:
        correct += 1

    # Yalnızca hatalı tahminleri göster
    else:
        print(f"\n{number}/{total} - HATALI TAHMIN")
        print(f"Etkinlik: {item['text']}")
        print(f"Beklenen kategori: {expected}")
        print(f"Modelin tahmini: {predicted}")

        print("En yüksek 3 kategori skoru:")

        for label, score in zip(
            result["labels"][:3],
            result["scores"][:3]
        ):
            category = description_to_category[label]
            print(f"  {category}: {score:.4f}")

        print("-" * 50)


# 7. Doğruluk oranını hesapla
if total == 0:
    print("Geliştirme örneği bulunamadı.")
else:
    accuracy = correct / total
    wrong = total - correct

    print("\n--- mDeBERTa SONUÇLARI ---")
    print(f"Toplam etkinlik: {total}")
    print(f"Doğru tahmin: {correct}/{total}")
    print(f"Hatalı tahmin: {wrong}")
    print(f"Accuracy: {accuracy:.2%}")
