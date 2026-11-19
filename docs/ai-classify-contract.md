# Grup 3 sınıflandırma API sözleşmesi

Güncelleme: 17 Kasım 2026. Bu belge AI servisinin mevcut davranışını açıklar.
Grup 3'ün kabulü ve ortak ortama taşıma henüz belgelenmemiştir.
Bekleyen kararlar [entegrasyon takip belgesinde](group3-integration.md) tutulur.

POST /ai/classify
Content-Type: application/json

İstek:
```json
{"text":"Yazılım stajı başvuruları başladı"}
```

HTTP 200 yanıtı:
```json
{"predictions":[{"category":"TECHNOLOGY","confidence":0.91},{"category":"CAREER","confidence":0.84}]}
```

Tek konu da aynı biçimdedir:
```json
{"predictions":[{"category":"OTHER","confidence":0.76}]}
```

- Yalnızca TECHNOLOGY, SPORT, ART, CAREER, SOCIAL, OTHER kullanılır.
- predictions boş olamaz. En fazla beş konu kategorisi veya tek OTHER döner.
- Her kategori en fazla bir kez bulunur. OTHER başka kategorilerle birlikte dönmez.
- Her confidence sonlu ve 0–1 aralığındadır. Skorlar kategoriye aittir;
  toplamlarının 1 olması gerekmez ve kalibre doğruluk olasılığı garantisi yoktur.
- Liste sırasından anlam çıkarılmamalıdır. İstemci her öğenin category alanını okur.
- text zorunlu bir metindir. Kenar boşlukları temizlenir; boş kalan metin reddedilir.
- Kaynak verideki expected_categories, değerlendirme etiketleridir; API alanı değildir.

Hatalar:
```json
{"error":"VALIDATION_ERROR","message":"Request body must contain a non-empty string field: text"}
```

| Kod | error | Durum |
|---|---|---|
| 400 | VALIDATION_ERROR | Geçersiz istek/JSON |
| 503 | MODEL_UNAVAILABLE | Sınıflandırıcı ModelUnavailableError ürettiğinde |
| 500 | INTERNAL_SERVER_ERROR | Beklenmeyen hata veya geçersiz sınıflandırıcı çıktısı |

Grup 3 önceki yanıtın category alanını okumak yerine predictions öğelerini
okumalıdır. Bu alan adları henüz Grup 3 tarafından onaylanmış sayılmaz.

Geliştirme portu 8005. Ortak servis URL'si, başlık/açıklama birleştirme şekli,
timeout ve servis çalışmadığında etkinlik oluşturmanın devam edip etmeyeceği
Grup 3 ile kesinleştirilecek kararlardır. localhost yalnızca yerel erişimdir.

## K1 iç sözleşmesi

Classifier.classify(text: str) -> list[ClassificationResult]

ClassificationResult her kategori için category ve confidence taşır. Tek sonuç
bile liste olarak dönmelidir. FakeClassifier bu yapıyı gösterir; gerçek tahmin
veya eşik seçimi yapmaz.

Gerçek MDeBERTaClassifier, CPU üzerinde sabit model revision ile çalışır.
`multi_label=True` kullanılır; beş konu kategorisinde skoru `>= 0.70` olanlar
seçilir. Hiçbiri eşiğe ulaşmazsa yalnızca OTHER döner. OTHER yanıtındaki
confidence, modelin OTHER için ürettiği skordur; eşik kararında kullanılmaz.
Gerçek model sonuçları skora göre azalan sıralanır; tüketici kategori alanlarını
okumalı ve liste sırasına iş anlamı bağlamamalıdır.

Classifier arayüzündeki `load()` ve `is_ready()` metotları hem gerçek modelde
hem FakeClassifier'da uygulanmıştır. PR #10 ile health/yaşam döngüsü entegrasyonu
ana dala alınmıştır. Model uygulama başlangıcında yüklenir; yükleme tamamlanmadan
sunucu istek kabul etmez. Yükleme başarısızsa uygulama başlangıcı başarısız olur.

## Sağlık kontrolü

`GET /health`: model hazırsa HTTP 200 ile
`{"service":"ai-service","status":"UP","version":"1.0.0"}` döner.
Servis çalışırken model hazır değilse HTTP 503 ile
`{"service":"ai-service","status":"DOWN","error":"MODEL_STARTING","version":"1.0.0"}` döner.
Bu health yanıtı, `/ai/classify` endpoint'inin error/message hata biçiminden ayrıdır.
Başlangıç yüklemesi sırasında bağlantı kurulamaması, bu bloklayıcı tasarımın parçasıdır.

Tam servis OpenAPI çıktısı [ai-classify.openapi.yaml](ai-classify.openapi.yaml)
dosyasında hem `/ai/classify` hem `/health` yollarını içerir.
Önceki tek etiketli accuracy sonuçları çoklu etiket doğruluğu olarak sunulmamalıdır.
