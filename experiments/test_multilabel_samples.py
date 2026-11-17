
from transformers import pipeline

MODEL_ID = "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"
REVISION = "8adb042d524ecd5c26d3e3ba0e3fbcf7e2d0864c"

CATEGORIES = {
    "TECHNOLOGY": "teknoloji ve yazılım",
    "SPORT": "spor",
    "ART": "sanat, müzik ve kültür",
    "CAREER": "kariyer ve iş hayatı",
    "SOCIAL": "sosyal buluşma ve gönüllülük",
    "OTHER": "üniversite idari işlemleri, genel bilgilendirme ve öğrenci duyuruları",
}

# Bunlar geliştirme amaçlı örneklerdir.
# Ayrı tuttuğumuz final 18 örneği kullanmıyoruz.
TESTS = [
    (
        "Dijital müzik üretimi atölyesinde yapay zekâ "
        "ve ses işleme araçlarıyla besteler hazırlanacak.",
        ["ART", "TECHNOLOGY"]
    ),
    (
        "Öğrencilere Python programlama atölyesi düzenlenecek.",
        ["TECHNOLOGY"]
    ),
    (
        "Yazılım geliştirici staj programı başvuruları başladı.",
        ["CAREER", "TECHNOLOGY"]
    ),
    (
        "Üniversiteler arası basketbol turnuvası yapılacak.",
        ["SPORT"]
    ),
    (
        "Öğrenciler için gönüllü yardım kampanyası düzenlenecek.",
        ["SOCIAL"]
    ),
    (
        "Üniversitede resim ve heykel sergisi açılacak.",
        ["ART"]
    ),
    (
        "Üniversitemizin yemek bursu başvuru sonuçları açıklandı.",
        ["OTHER"]
    ),
    (
        "Final sınav takviminde değişiklik yapıldı.",
        ["OTHER"]
    ),
    (
        "Öğrenciler için staj ve iş görüşmesi teknikleri semineri.",
        ["CAREER"]
    ),
]

print("Model yükleniyor...")

classifier = pipeline(
    "zero-shot-classification",
    model=MODEL_ID,
    revision=REVISION,
    device=-1,
)

reverse = {
    description: category
    for category, description in CATEGORIES.items()
}

for index, (text, expected) in enumerate(TESTS, start=1):
    result = classifier(
        text,
        candidate_labels=list(CATEGORIES.values()),
        hypothesis_template="Bu metin {} ile ilgilidir.",
        multi_label=True,
    )

    scores = {
        reverse[label]: score
        for label, score in zip(
            result["labels"], result["scores"]
        )
    }

    print(f"\n--- ÖRNEK {index} ---")
    print("Metin:", text)
    print("Beklenen:", ", ".join(expected))

    for category, score in sorted(
        scores.items(),
        key=lambda item: item[1],
        reverse=True,
    ):
        print(f"  {category}: {score:.4f}")

    # Henüz eşik seçmiyoruz; farklı değerleri karşılaştırıyoruz.
    for threshold in [0.50, 0.70, 0.90, 0.95]:
        predicted = [
            category
            for category, score in scores.items()
            if score >= threshold
        ]

        if not predicted:
            predicted = ["OTHER"]

        print(
            f"Eşik {threshold:.2f}: "
            f"{', '.join(predicted)}"
        )
