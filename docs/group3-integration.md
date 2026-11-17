# Grup 3 ve ortak entegrasyon takibi

Güncelleme: 17 Kasım 2026. Durum: dış ekip onayı ve erişim bekleniyor.
Bu belge karar taslağıdır; aşağıdaki öneriler karşılıklı kabul edilmiş değildir.

## Hazır olanlar

- AI servisi: `POST /ai/classify`, çoklu kategori `predictions` yanıtı.
- Sağlık kontrolü: `GET /health`.
- [İstek/yanıt kuralları](ai-classify-contract.md) ve
  [tam servis OpenAPI dosyası](ai-classify.openapi.yaml).
- AI servisi için Docker Compose ve örnek Event Service istemcisi.
- HTTP sistem testleri ve istemci taklidi gerçek Grup 3 bağlantısına hazırlıktır;
  gerçek Event Service entegrasyonunun tamamlandığını göstermez.

## Kesinleştirilecek kararlar

| Konu | Mevcut bilgi / öneri | Onay ve uygulama |
|---|---|---|
| Ortak depo | Planlanan ad `campushub-integration`; URL, sorumlu ve K2/K3 erişimi doğrulanmalı. | Entegrasyon sorumlusu; K2/K3 takip |
| Sözleşmenin yeri | Planlanan klasör `api-contracts`; erişim sonrası dosya PR ile taşınacak. | K2 + ortak depo sorumlusu |
| İstek | Tek `text` alanı hazır; başlık/açıklama birleştirme kuralı henüz onaylanmadı. | K2 + Grup 3, K1 destek |
| Yanıt | `predictions` içindeki tüm category/confidence öğeleri okunmalı. | K2 + Grup 3 |
| Adres/ağ | Yerelde `http://127.0.0.1:8005`; ortak Docker ağında servis adı `ai-service` korunursa `http://ai-service:8005` önerilir. | K3 + Grup 3 |
| Timeout | Örnek istemcide 5 saniye; gerçek model ve ortak ortam ölçümüyle kesinleştirilmeli. | K1/K2/K3 + Grup 3 |
| Kesinti/hata | Örnek istemci kategorisiz devam etmeyi gösterir; gerçek kayıt davranışı henüz onaylanmadı. 400, 503, 500 ve timeout ayrı ele alınmalı. | K2/K3 + Grup 3 |

Ortak deponun URL'si veya onay kaydı henüz burada yoktur. Depo açılmadı sonucu
yalnızca bu belgeden çıkarılamaz; ilgili ekipten bağlantı ve erişim istenmelidir.

## T20: Ortak depoya PR sırası

1. Ortak depo URL'sini, hedef branch/klasörü ve erişimi doğrula.
2. Bu repoda `python -m scripts.export_openapi` ile güncel şemayı üret.
3. Ortak deponun ayrı branch'inde `api-contracts/ai-classify.openapi.yaml`
   dosyasını ekle; kaynak AI commit'ini PR açıklamasına yaz.
4. Grup 3'ten sözleşme incelemesi iste; kabul edilen kararları bu tabloya ekle.
5. Ortak PR bağlantısını ve merge commit'ini aşağıya kaydet.

Ortak depo PR'si: **bekliyor**. Grup 3 onayı: **bekliyor**.

## T19: Gerçek bağlantıda kaydedilecek kanıtlar

- Event Service'in geçerli metni gönderip kategori listesini kaydetmesi.
- Tek ve çok kategorili sonuçlar; OTHER'ın yalnız dönmesi.
- Geçersiz istekte 400/error/message davranışı.
- AI servisi kapalıyken ve yanıt gecikirken Event Service'in kararlaştırılan davranışı.
- Model kullanılamadığında 503 ve beklenmeyen hatada 500 davranışı.
- Ortak Compose/ağ üzerinden erişim, sağlık kontrolü ve gerçek model gecikmesi.

Her kontrol için tarih, iki servisin commit'leri, ortam, beklenen/gerçek sonuç
ve log veya test kaydı tutulmalı. T19, bu gerçek bağlantı kontrollerinden sonra
tamamlandı olarak işaretlenmeli.
