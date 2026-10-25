
import json
from pathlib import Path
from transformers import pipeline

# Mevcut başarılı V2 açıklamalarını kullan
data_dir = Path(__file__).resolve().parents[1] / "data" / "evaluation"

with open(
    data_dir / "CampusHub_Kategori_Aciklamalari_v2.json",
    encoding="utf-8"
) as f:
    config = json.load(f)

labels = config["labels"]
description_to_category = {
    description: category
    for category, description in labels.items()
}

# Yeni ve daha önce değerlendirmede kullanılmamış örnekler
# Beklenen etiketler etkinliğin ana amacına göre belirlendi.
new_events = [
    ("Python ile görüntü işleme uygulaması geliştirme atölyesi.", "TECHNOLOGY"),
    ("Siber güvenlikte zararlı yazılım analizi eğitimi.", "TECHNOLOGY"),
    ("Robotik kulübü üyeleri sensörlerle çalışan bir robot geliştirecek.", "TECHNOLOGY"),

    ("Üniversiteler arası voleybol turnuvası.", "SPORT"),
    ("Kampüste başlangıç seviyesi yoga uygulaması.", "SPORT"),
    ("Öğrenciler için yüzme teknikleri eğitimi.", "SPORT"),

    ("Yapay zekâ araçlarıyla dijital illüstrasyon ve karakter çizimi atölyesi.", "ART"),
    ("Kısa film çekimi ve senaryo yazımı atölyesi.", "ART"),
    ("Kampüs tiyatro topluluğu sahne gösterisi düzenleyecek.", "ART"),

    ("Yazılım firmasında staj mülakatlarına hazırlık semineri.", "CAREER"),
    ("Mühendisler için CV ve LinkedIn profili hazırlama eğitimi.", "CAREER"),
    ("Teknoloji şirketlerinin işe alım süreçleri hakkında bilgilendirme.", "CAREER"),

    ("Robotik kulübü yeni üyeler için tanışma pikniği düzenleyecek.", "SOCIAL"),
    ("Gönüllü öğrenciler sokak hayvanlarına mama toplama kampanyasında buluşacak.", "SOCIAL"),
    ("Yeni öğrenciler için kampüste tanışma ve kaynaşma etkinliği.", "SOCIAL"),

    ("Sporcular için sakatlıklardan korunma bilgilendirme semineri.", "OTHER"),
    ("Öğrenci işleri burs başvuruları ve akademik kayıt kurallarını anlatacak.", "OTHER"),
    ("Kampüste deprem ve afet güvenliği bilgilendirme oturumu.", "OTHER"),
]

print("mDeBERTa V2 yükleniyor...")

classifier = pipeline(
    "zero-shot-classification",
    model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli",
    device="cpu"
)

correct = 0

for number, (text, expected) in enumerate(new_events, start=1):
    result = classifier(
        text,
        candidate_labels=list(labels.values()),
        hypothesis_template=config["hypothesis_template"],
        multi_label=False
    )

    predicted = description_to_category[result["labels"][0]]

    if predicted == expected:
        correct += 1
        status = "DOGRU"
    else:
        status = "YANLIS"

    print(f"\n{number}/{len(new_events)} - {status}")
    print(f"Etkinlik: {text}")
    print(f"Beklenen: {expected}")
    print(f"Tahmin: {predicted}")

    print("En yüksek 3 kategori:")
    for label, score in zip(result["labels"][:3], result["scores"][:3]):
        category = description_to_category[label]
        print(f"  {category}: {score:.4f}")

print("\n--- YENI ETKINLIK TESTI ---")
print(f"Dogru: {correct}/{len(new_events)}")
print(f"Accuracy: {correct / len(new_events):.2%}")
