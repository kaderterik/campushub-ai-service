# K1/K2 API Entegrasyonu ve İnceleme Durumu

Bu belge, önceki inceleme notlarının güncellenmiş hâlidir.
Geçmiş deney sonuçlarını değiştirmez. Güncelleme: 17 Kasım 2026.

## Tamamlanan API Çalışmaları

- API, bir metin için birden fazla kategori döndürebilir.
- Yanıtın predictions listesinde her kategori için category ve
  confidence alanları bulunur.
- Altı kategori kullanılır: TECHNOLOGY, SPORT, ART, CAREER,
  SOCIAL ve OTHER.
- OTHER yalnızca tek başına döner.
- Boş liste, tekrarlanan kategori ve geçersiz skorlar reddedilir.
- Geçersiz istekler 400, model kullanılamadığında 503,
  beklenmeyen hatalar 500 döndürür.
- Bu hata yanıtları ortak error/message biçimini kullanır.

## Gerçek Model Bağlantısı

app/models/classifier.py içindeki MDeBERTaClassifier,
InferenceService üzerinden FastAPI endpoint'ine bağlanmıştır.

- CLASSIFIER_BACKEND=real ile gerçek model seçilir.
- Varsayılan FakeClassifier sabit deneme sonucu döndürür.
- Gerçek model uygulama başlangıcında bir kez yüklenir.
- Model CPU üzerinde ve sabit revision ile çalışır.
- Beş konu kategorisinden skoru 0.70 veya üzerinde olanlar seçilir.
- Hiçbir konu eşiği karşılamazsa yalnızca OTHER döner.
- Confidence değerleri kalibre edilmiş doğruluk olasılıkları değildir.

Windows PowerShell'de gerçek modeli çalıştırmak için:

```powershell
$env:CLASSIFIER_BACKEND = "real"
python -m uvicorn app.main:app --port 8005
```

## Doğrulama Kapsamı

17 Kasım 2026 tarihli PR #10 incelemesinde 56 otomatik test geçmiştir.
Bu doğrulama API/model birim testleri, health testleri, gerçek uvicorn sürecine
HTTP istekleri, 30 istekli eşzamanlılık denemesi ve başlangıç yaşam döngüsünü kapsar.

Otomatik model testlerinde pipeline taklit edilir; HTTP sistem testlerinde
ayrı uvicorn süreci FakeClassifier ile başlatılır.
Model ağırlıkları indirilmeden API bağlantısı, kategori seçim
kuralları ve başlangıçtaki yükleme çağrısı doğrulanır.

Windows'ta gerçek modelle ayrıca manuel deneme yapılmıştır:

- Yazılım stajı metninde HTTP 200 ve TECHNOLOGY/CAREER sonuçları alınmıştır.
- Boş metinde HTTP 400 ve VALIDATION_ERROR alınmıştır.

Bu deneme modelin sıfırdan indirilmesini ayrıca doğrulamaz;
model dosyaları önbellekten yüklenmiş olabilir.

## Grup 3 Sözleşmesi

İstek ve yanıt yapısı docs/ai-classify-contract.md içinde açıklanır.
Swagger arayüzü /docs adresindedir.

Grup 3 ile şu kararlar karşılıklı kesinleştirilmelidir:

- predictions yanıt yapısının kabulü
- Başlık, açıklama veya birleştirilmiş metnin gönderilmesi
- Ortak servis adresi ve port
- Timeout süresi
- Servis kapalıyken veya hata döndüğünde uygulanacak davranış

Sözleşmenin hazırlanması, Grup 3 onayı anlamına gelmez.
Ortak integration deposuna taşıma, depo ve erişim hazır olduğunda yapılacaktır.
Bekleyen kararlar ve T20/T19 adımları [entegrasyon takibinde](group3-integration.md)
listelenir; ortak depo ve Grup 3 kabulü tamamlandı olarak işaretlenmemiştir.

## Health ve Docker Entegrasyonu

PR #10 ana dala alınmıştır. `/health` router'ı uygulamaya bağlanmış;
Classifier sözleşmesine `load()` ve `is_ready()` eklenmiştir.
Model başlangıçta bloklayarak yüklenir. Dockerfile, Compose, kalıcı model
önbelleği ve sistem testleri ana dalda mevcuttur.
Docker/çevrimdışı çalışma için K3'ün doğrulama kaydı README'dedir;
bu K2 belge güncellemesinde Docker yeniden çalıştırılarak doğrulanmamıştır.

## Ayrı Takip Edilen Çalışmalar

- K1'in model karar belgesi ve değerlendirme raporları ayrıca takip edilir.
- Eski tek etiketli deneyler, güncel çok etiketli API davranışıyla
  karıştırılmamalıdır.
- K3'ün mevcut health, Docker ve Compose uygulaması bu belge güncellemesinde
  değiştirilmemiştir. Gerçek Event Service ile T19 kontrolü beklemektedir.
- Eski benchmark scriptlerinin Windows uyumluluğu bu belge
  güncellemesiyle düzeltilmiş sayılmaz.

## Depo Adı

GitHub depo adı campushub-ai-service olarak düzeltilmiştir.

Bilgisayardaki eski campushub-ai-serive klasör adı,
Python import yollarını değiştirmez.
