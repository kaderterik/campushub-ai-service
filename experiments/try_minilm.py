
from transformers import pipeline

MODEL_ID = "MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli"

print("MiniLM modeli yükleniyor...")

classifier = pipeline(
    "zero-shot-classification",
    model=MODEL_ID,
    device="cpu"
)

text = "Üniversitemizden mezun olan mühendisler, meslek hayatlarındaki deneyimlerini ve profesyonel gelişim yolculuklarını öğrencilerle paylaşacak."

categories = [
    "teknoloji",
    "spor",
    "sanat",
    "iş başvurusu, CV hazırlama ve mülakat süreçleri",
    "sosyal etkinlik",
    "diğer konular"
]

result = classifier(
    text,
    candidate_labels=categories,
    hypothesis_template="Bu etkinlik {} ile ilgilidir.",
    multi_label=False
)

print("\nEtkinlik:", text)
print("Tahmin edilen kategori:", result["labels"][0])
print("Confidence:", round(result["scores"][0], 4))

print("\nTüm kategori skorları:")

for label, score in zip(result["labels"], result["scores"]):
    print(f"{label}: {score:.4f}")
