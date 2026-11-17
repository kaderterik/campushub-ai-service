
from transformers import pipeline

# Daha önce seçtiğimiz model ve sabit sürümü
MODEL_ID = "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"
REVISION = "8adb042d524ecd5c26d3e3ba0e3fbcf7e2d0864c"

# V5 kategori açıklamalarımız
CATEGORIES = {
    "TECHNOLOGY": "teknoloji ve yazılım",
    "SPORT": "spor",
    "ART": "sanat, müzik ve kültür",
    "CAREER": "kariyer ve iş hayatı",
    "SOCIAL": "sosyal buluşma ve gönüllülük",
    "OTHER": "üniversite idari işlemleri, genel bilgilendirme ve öğrenci duyuruları",
}

print("Model yükleniyor...")

classifier = pipeline(
    "zero-shot-classification",
    model=MODEL_ID,
    revision=REVISION,
    device=-1,  # CPU kullan
)

# İlk deneme etkinliğimiz

text = "Üniversitemizin yemek bursu başvuru sonuçları açıklandı."


result = classifier(
    text,
    candidate_labels=list(CATEGORIES.values()),
    hypothesis_template="Bu metin {} ile ilgilidir.",
    multi_label=True,
)

# Türkçe açıklamaları kategori kodlarına dönüştür
reverse_categories = {
    description: category
    for category, description in CATEGORIES.items()
}

print("\nEtkinlik:", text)
print("\nKategori skorları:")

for label, score in zip(result["labels"], result["scores"]):
    category = reverse_categories[label]
    print(f"{category}: {score:.4f}")
