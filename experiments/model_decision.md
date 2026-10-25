# CampusHub AI — Nihai Model Kararı (T11)

## 1. Amaç

CampusHub uygulamasındaki Türkçe etkinlik ve duyuru açıklamalarını, bir metnin birden fazla konuyla ilişkili olabilmesini destekleyerek **altı sabit kategoride çok etiketli (multi-label)** sınıflandırmak.

Önceden eğitilmiş zero-shot classification modeli kullanılacaktır; proje kapsamında model yeniden eğitilmeyecektir.

## 2. Seçilen Model

- **Model ID:** `MoritzLaurer/mDeBERTa-v3-base-mnli-xnli`
- **Hugging Face revision (commit SHA):** `8adb042d524ecd5c26d3e3ba0e3fbcf7e2d0864c`
- **Yöntem:** Zero-shot, çok etiketli metin sınıflandırma (`multi_label=True`)
- **Çalışma ortamı:** CPU (`device=-1`)
- **Metin dili:** Türkçe
- **Çıktı:** Bir veya daha fazla kategori ve her kategoriye ait skor

Model sürümünü sabitlemek için entegrasyonda model ID ve revision birlikte kullanılacaktır. Model skorları **kalibre edilmiş olasılık olarak yorumlanmaz**.

## 3. Sabit Kategoriler ve Güncel Model Açıklamaları

337 kayıtlık çoklu kategori geliştirme değerlendirmesinde kullanılan açıklamalar:

| Kategori | Modelde kullanılan açıklama |
|---|---|
| TECHNOLOGY | teknoloji ve yazılım |
| SPORT | spor |
| ART | sanat, müzik ve kültür |
| CAREER | kariyer ve iş hayatı |
| SOCIAL | sosyal buluşma ve gönüllülük |
| OTHER | üniversite idari işlemleri, genel bilgilendirme ve öğrenci duyuruları |

**Hypothesis template:** `Bu metin {} ile ilgilidir.`

**Not:** Önceki tek kategorili V5 deneylerinde kullanılan kategori açıklamaları ve template farklıydı; eski deneyler tarihsel karşılaştırma olarak 5–6. bölümlerde korunmuştur. Güncel çoklu etiketli değerlendirmede kullanılan kesin ayarlar `experiments/evaluate_multilabel.py` ve `experiments/results/multilabel_dev_scores.json` dosyasının `signature` alanında kayıtlıdır. V5 açıklama dosyası, bu güncel yapılandırmanın birebir kaynağı olarak gösterilmemelidir.

## 4. Güncel Çoklu Kategori Karar Kuralı

1. Transformers `zero-shot-classification` pipeline'ı `multi_label=True` ile çalıştırılır.
2. Modelden altı açıklamanın skoru alınır. Ancak doğrudan etiket seçerken yalnızca beş ana konu (`TECHNOLOGY`, `SPORT`, `ART`, `CAREER`, `SOCIAL`) değerlendirilir.
3. **Eşik (`threshold`) = `0.70`**. Skoru `>= 0.70` olan tüm ana konu kategorileri seçilir.
4. Hiçbir ana konu eşik değerini geçmezse sonuç yalnızca **`OTHER`** olur (fallback).
5. `OTHER`, başka bir ana konu kategorisiyle birlikte döndürülmez; doğrudan `OTHER` model skoru eşik kararında kullanılmaz.
6. Tahmin edilen kategori sayısı birden fazla olabilir. Model skorları, doğruluk olasılığı veya garanti edilen güven seviyesi değildir.

API için beklenen çoklu kategori yanıt biçimi:

```json
{
  "predictions": [
    {"category": "TECHNOLOGY", "confidence": 0.91},
    {"category": "CAREER", "confidence": 0.84}
  ]
}
```

Yukarıdaki skorlar yalnızca yanıt biçimi örneğidir. `OTHER` fallback için API'ye yazılacak `confidence` değerinin nasıl üretileceği **T12 entegrasyonunda ayrıca açık ve tutarlı biçimde tanımlanmalıdır**; bu değer kalibre edilmiş olasılık gibi sunulmamalıdır.

## 5. Önceki Tek Kategorili Model Karşılaştırması (Tarihsel)

İlk 42 geliştirme örneğiyle yapılan **tek kategorili** deneylerin sonuçları:

| Model | Doğru / Toplam | Accuracy |
|---|---:|---:|
| MiniLM | 22/42 | %52,38 |
| mDeBERTa V5 | 33/42 | %78,57 |
| mDeBERTa 2mil7 V5 | 31/42 | %73,81 |

CPU benchmark sonuçları (yerel deney koşulları):

| Metrik | MiniLM | mDeBERTa V5 | mDeBERTa 2mil7 V5 |
|---|---:|---:|---:|
| Model yükleme (sn) | 1,597 | 1,554 | 2,093 |
| Ortalama inference (ms) | 26,36 | 621,51 | 607,38 |
| P95 inference (ms) | 27,91 | 723,40 | 710,52 |
| Ölçülen peak RAM (MB) | 817,12 | 750,42 | 871,88 |

Bu hız/RAM değerleri farklı cihazlarda aynı sonucu garanti etmez. Tek kategorili **accuracy** ile güncel çok etiketli **Micro-F1**, farklı metrikler ve farklı veri setleri kullandıkları için doğrudan karşılaştırılamaz.

## 6. Önceki Ek Geliştirme Deneyleri (Tarihsel)

Eski tek kategorili mDeBERTa V5 denemeleri:

- İlk 42 geliştirme örneği: **33/42 — %78,57**
- Ek 18 etkinlik: **13/18 — %72,22**
- Ek 24 etkinlik: **18/24 — %75,00**
- Bu eski deneylerin toplamı: **64/84 — %76,19**

Buradaki 84 örnek, yeni ayrılan **84 kayıtlık T29 final test verisi değildir**. Ayrıca eski deneyler `multi_label=False` kullandığından güncel 337 kayıtlık sonuçlarla doğrudan eşdeğer değildir. Eski ek denemelerde özellikle `OTHER` için hatalar görülmüştür.

## 7. Güncel Çoklu Etiketli Geliştirme Değerlendirmesi (T11)

**Veri:** `data/evaluation/CampusHub_421_GELISTIRME_DUZELTILMIS.json`

- Geliştirme kayıt sayısı: **337**
- Ayrı tutulan final test kayıt sayısı: **84** (bu aşamada kullanılmadı)
- Geliştirme JSON SHA-256: `462e05cda851c3be6b9c6fc1937d582978e901d62772964da8840ed56ea4fe1b`
- Değerlendirme kodu: `experiments/evaluate_multilabel.py`
- Skor önbelleği: `experiments/results/multilabel_dev_scores.json`
- Metrik dosyası: `experiments/results/multilabel_dev_metrics.json`

Sabit model ve kategori açıklamalarıyla dört eşik denenmiştir:

| Eşik | Precision | Recall | Micro-F1 | Macro-F1 | Exact Match |
|---|---:|---:|---:|---:|---:|
| 0.50 | %51,14 | %72,58 | %60,00 | %58,64 | %36,20 |
| **0.70** | **%61,24** | **%68,82** | **%64,81** | **%64,45** | **%52,23** |
| 0.90 | %54,97 | %53,49 | %54,22 | %53,86 | %48,37 |
| 0.95 | %51,26 | %49,19 | %50,21 | %49,15 | %45,40 |

**Karar:** İncelenen eşikler içinde `0.70`, **Micro-F1, Macro-F1 ve Exact Match** bakımından en yüksek sonucu sağlamıştır. Bu nedenle final testten **önce** eşik `0.70` olarak sabitlenmiştir.

0.70 eşiğinde:

- **Exact Match:** 176/337 = **%52,23** (tüm tahmin edilen kategoriler beklenenlerle birebir aynı)
- **En az bir doğru kategori:** 248/337 = **%73,59** (yanlış ek kategoriler olsa bile en az biri doğru)
- **Kısmen doğru, ama tam eşleşmeyen:** 72/337
- **Beklenen kategorilerle hiç örtüşmeyen:** 89/337

`En az bir doğru kategori` ölçütü, yanlış ek kategorileri cezalandırmadığından **ana başarı metriği değildir**. Ana metrik **Micro-F1**, yardımcı metrikler **Macro-F1** ve **Exact Match** olacaktır.

0.70 eşiğinde kategori bazında F1:

| Kategori | F1 |
|---|---:|
| TECHNOLOGY | %60,29 |
| SPORT | %93,02 |
| ART | %68,47 |
| CAREER | %68,44 |
| SOCIAL | %47,62 |
| OTHER | %48,85 |

**Bilinen sınırlamalar:** Özellikle `SOCIAL` / `OTHER` karışıklığı, eşik altında kalan ilgili kategoriler ve gereksiz ek kategoriler görülmüştür. Geliştirme verisinde kategori dağılımı eşit değildir. Bu sınırlamalar raporda açıkça belirtilecektir; final test sonuçlarına göre eşik değiştirilmeyecektir.

## 8. T29 — 84 Kayıtlık Bağımsız Final Test

**Final test dosyası:** `data/evaluation/CampusHub_421_FINAL_TEST_DUZELTILMIS_DOKUNMA.json`

**Kayıt sayısı:** 84. Bu dosya, 337 geliştirme kaydıyla toplam **421 örneklik** veri setinin ayrı tutulan bölümüdür.

**Final testten önce sabitlenen kararlar:**

- Model ID ve revision (2. bölüm)
- Altı kategori ve açıklamaları (3. bölüm)
- Hypothesis template: `Bu metin {} ile ilgilidir.`
- `multi_label=True`
- Beş ana kategoride `0.70` eşik
- Hiçbiri geçmezse `OTHER` fallback
- Değerlendirme metrikleri: Micro-F1 (ana); Macro-F1, Exact Match, en az bir doğru kategori (yardımcı)

**Önerilen asgari kabul hedefleri (proje içi, final veriye bakılmadan belirlenmiştir):** Micro-F1 **≥ %60** ve Exact Match **≥ %45**. Bunlar ödev yönergesinden alınmış zorunlu eşikler değil, mevcut geliştirme deneyine dayanarak konulmuş **öneri hedeflerdir**; ekip / ders sorumlusu gerekirse onaylamalıdır. Eşik sağlanmasa bile gerçek sonuç değiştirilmeden raporlanacaktır.

**Önemli kapsam değişikliği:** Eski T29 planı 18 örnekli holdout testiydi. Grup kararına göre bunun yerine 84 kayıtlık yeni final test uygulanacaktır. Ödev yönergesi özellikle 18 örnek istiyorsa kapsam değişikliği ders sorumlusuna bildirilmelidir.

**Final test durumu:** **Henüz çalıştırılmadı.** Geliştirme sonuçlarıyla yapılan eşik seçimi tamamlandıktan sonra final set **bir kez** değerlendirilecek. Sonuçlar görülünce model/threshold/etiket açıklamaları final veriye göre ayarlanmayacak.

## 9. Sonraki Adımlar

1. **T11:** Güncel model kararını, geliştirme sonuçlarını ve sabit ayarları belgeleyip commit/push yapmak.
2. **T29:** 84 kayıtlık final testi, ayarları değiştirmeden bir kez çalıştırmak ve sonuçları raporlamak.
3. **T12:** Gerçek `app/models/classifier.py` entegrasyonunu; `load()`, `is_ready()`, `classify()` ve K2'nin `predictions` sözleşmesiyle uyumlu biçimde tamamlamak.
4. **Entegrasyon:** K2 API ve K3 health/Docker akışını birlikte test etmek.
5. **Teslim:** Nihai rapor, testler, son commit/push ve PR.

**Nihai T11 model kararı:** Sabit revision'lı **mDeBERTa**, `multi_label=True`, beş ana etiket için **0.70 eşik** ve eşik geçilmezse **OTHER fallback**. Eski tek kategorili sonuçlar yalnızca tarihsel model seçimi kanıtıdır.
