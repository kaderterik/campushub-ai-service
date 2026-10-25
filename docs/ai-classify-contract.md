# Grup 3 sınıflandırma API sözleşmesi (çoklu kategori taslağı)

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
veya eşik seçimi yapmaz. Gerçek modelin çoklu etiket çıkarımı, seçim eşikleri ve
OTHER davranışı geliştirme kümesinde K1 ile belirlenmelidir. multi_label=True
tek başına hangi etiketlerin seçileceği kararını çözmez. Önceki tek etiketli
accuracy sonuçları çoklu etiket doğruluğu olarak sunulmamalıdır.

K3'ün PR #4'ündeki load()/is_ready() yaşam döngüsü eklemeleri ayrı tutuldu.
Entegrasyonda bu metotlar korunarak classify dönüş tipi listeye uyarlanmalıdır.
