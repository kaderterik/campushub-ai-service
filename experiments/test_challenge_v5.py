
import json
from pathlib import Path
from collections import Counter
from transformers import pipeline

# 1. Proje klasörü ve V5 açıklamaları
project_dir = Path(__file__).resolve().parents[1]
data_dir = project_dir / "data" / "evaluation"

with open(
    data_dir / "CampusHub_Kategori_Aciklamalari_v5.json",
    encoding="utf-8"
) as f:
    config = json.load(f)

labels = config["labels"]
description_to_category = {
    description: category
    for category, description in labels.items()
}

# 2. Yeni 24 etkinlik: Her kategoriden 4 örnek
events = [
    # TECHNOLOGY
    (
        "Arduino ile sıcaklık sensöründen veri okuyarak "
        "çalışan bir elektronik devre kuracağız.",
        "TECHNOLOGY"
    ),
    (
        "Veri tabanı atölyesinde SQL sorguları yazıp "
        "kütüphane kayıtlarını analiz edeceğiz.",
        "TECHNOLOGY"
    ),
    (
        "Kariyer kulübünün düzenlediği HTML ve CSS "
        "ile web sitesi geliştirme atölyesi.",
        "TECHNOLOGY"
    ),
    (
        "Python ile konuşmayı metne dönüştüren hazır "
        "yapay zekâ modellerini çalıştıracağız.",
        "TECHNOLOGY"
    ),

    # SPORT
    (
        "Üniversite spor salonunda badminton turnuvası.",
        "SPORT"
    ),
    (
        "Doğa yürüyüşü kulübüyle 8 kilometrelik "
        "tempolu trekking etkinliği yapılacak.",
        "SPORT"
    ),
    (
        "Dans kulübünün düzenlediği zumba dersinde "
        "ritmik egzersizler uygulanacak.",
        "SPORT"
    ),
    (
        "Kampüs bahçesinde pilates ve esneme "
        "egzersizleri yapılacak.",
        "SPORT"
    ),

    # ART
    (
        "Fotoğrafçılık topluluğu ışık ve kadraj "
        "teknikleriyle portre çekimi yapacak.",
        "ART"
    ),
    (
        "Üniversite orkestrası keman ve piyano "
        "eserlerinden oluşan resital verecek.",
        "ART"
    ),
    (
        "Tablet kullanarak çizgi roman karakterleri "
        "tasarlayıp dijital boyama yapacağız.",
        "ART"
    ),
    (
        "Edebiyat kulübünde şiir yazma ve "
        "sesli okuma atölyesi düzenlenecek.",
        "ART"
    ),

    # CAREER
    (
        "Teknoloji şirketinin insan kaynakları uzmanı "
        "iş görüşmelerine hazırlık eğitimi verecek.",
        "CAREER"
    ),
    (
        "Öğrencilere staj başvuruları için özgeçmiş "
        "ve niyet mektubu hazırlama anlatılacak.",
        "CAREER"
    ),
    (
        "Mezun mühendisler sektördeki kariyer "
        "yollarını ve iş olanaklarını anlatacak.",
        "CAREER"
    ),
    (
        "Kariyer fuarında öğrenciler işverenlerle "
        "görüşerek açık iş pozisyonlarını öğrenecek.",
        "CAREER"
    ),

    # SOCIAL
    (
        "Mühendislik kulübü yeni üyeler için "
        "tanışma kahvaltısı düzenleyecek.",
        "SOCIAL"
    ),
    (
        "Gönüllü öğrenciler huzurevini ziyaret ederek "
        "yaşlılarla sohbet edip oyun oynayacak.",
        "SOCIAL"
    ),
    (
        "Yapay zekâ topluluğu dönem sonu "
        "kaynaşma pikniği düzenleyecek.",
        "SOCIAL"
    ),
    (
        "Öğrenciler ihtiyaç sahibi çocuklar için "
        "gönüllü kırtasiye bağışı kampanyası düzenleyecek.",
        "SOCIAL"
    ),

    # OTHER
    (
        "Öğrenci işleri Erasmus başvuru evrakları "
        "ve son tarihler hakkında bilgi verecek.",
        "OTHER"
    ),
    (
        "Diyetisyen öğrenci yurdunda sağlıklı "
        "beslenme ve besin alerjilerini anlatacak.",
        "OTHER"
    ),
    (
        "Uzmanlar deprem sonrası acil toplanma "
        "prosedürlerini anlatacak.",
        "OTHER"
    ),
    (
        "Kampüs çevre birimi geri dönüşüm kuralları "
        "ve atık ayrıştırma yönergesini açıklayacak.",
        "OTHER"
    ),
]

# 3. Mevcut başarılı modeli yükle
print("mDeBERTa V5 yükleniyor...")

classifier = pipeline(
    "zero-shot-classification",
    model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli",
    device="cpu"
)

# 4. Değerlendirme
correct = 0
category_total = Counter()
category_correct = Counter()

for i, (text, expected) in enumerate(events, start=1):
    result = classifier(
        text,
        candidate_labels=list(labels.values()),
        hypothesis_template=config["hypothesis_template"],
        multi_label=False
    )

    predicted = description_to_category[result["labels"][0]]
    category_total[expected] += 1

    if predicted == expected:
        correct += 1
        category_correct[expected] += 1
        print(f"{i}/24 - DOGRU: {expected}")
    else:
        print(f"\n{i}/24 - YANLIS")
        print(f"Etkinlik: {text}")
        print(f"Beklenen: {expected}")
        print(f"Tahmin: {predicted}")

        for label, score in zip(
            result["labels"][:3],
            result["scores"][:3]
        ):
            category = description_to_category[label]
            print(f"  {category}: {score:.4f}")

# 5. Sonuç
print("\n--- YENI 24 ETKINLIK SONUCLARI ---")

for category in labels:
    print(
        f"{category}: "
        f"{category_correct[category]}/"
        f"{category_total[category]}"
    )

print(f"\nToplam: {correct}/{len(events)}")
print(f"Accuracy: {correct / len(events):.2%}")
