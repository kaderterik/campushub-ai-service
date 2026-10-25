
# CampusHub AI Service

FastAPI ile hazırlanmış, üniversite etkinlik açıklamalarını sınıflandıran AI mikroservisi.

Servis iki sınıflandırıcıyı destekler:
- **FakeClassifier:** API geliştirme ve testleri için sabit sonuç döndürür.
- **MDeBERTaClassifier:** Gerçek çok dilli zero-shot AI modeli ile sınıflandırma yapar.

Varsayılan sınıflandırıcı FakeClassifier'dır.

## Kurulum — Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Kurulum — macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Çalıştırma — Windows (PowerShell)

Varsayılan FakeClassifier ile:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8005
```

Gerçek AI modeli ile:

```powershell
$env:CLASSIFIER_BACKEND = "real"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8005
```

## Çalıştırma — macOS/Linux

Sanal ortam aktifken FakeClassifier ile:

```bash
python -m uvicorn app.main:app --reload --port 8005
```

Gerçek AI modeli ile:

```bash
CLASSIFIER_BACKEND=real python -m uvicorn app.main:app --port 8005
```

Swagger arayüzü: http://127.0.0.1:8005/docs

## Gerçek AI Modeli

Kullanılan model:

`MoritzLaurer/mDeBERTa-v3-base-mnli-xnli`

Model Hugging Face üzerinden yüklenir ve sabit model revision'ı kullanılır.

Özellikler:
- CPU üzerinde çalışır.
- Model, uygulama başlangıcında bir kez yüklenir.
- Tekrar `load()` çağrılması modeli yeniden yüklemez.
- Türkçe etkinlik açıklamalarını sınıflandırabilir.
- Multi-label sınıflandırma desteklenir.
- Karar eşiği 0.70'tir.

Model ilk kez çalıştırıldığında, önbellekte yoksa Hugging Face üzerinden indirilir. İlk indirme için internet bağlantısı gereklidir.

Gerçek modeli etkinleştirmek için `CLASSIFIER_BACKEND=real` ortam değişkeni kullanılmalıdır. Bu ayar yapılmazsa FakeClassifier çalışır.

### Sınıflandırma Kuralları

Desteklenen kategoriler:

- TECHNOLOGY
- SPORT
- ART
- CAREER
- SOCIAL
- OTHER

Beş konu kategorisinin her biri bağımsız olarak değerlendirilir.

0.70 veya üzerinde skor alan konu kategorileri sonuç listesine eklenir.

Hiçbir konu kategorisi 0.70 eşiğini geçmezse yalnızca OTHER döndürülür.

OTHER, diğer kategorilerle birlikte döndürülmez.

Model skorları 0 ile 1 arasındadır; toplamlarının 1 olması gerekmez. Bu skorlar kalibre edilmiş doğruluk olasılıkları olarak yorumlanmamalıdır.

## API

### POST /ai/classify

İstek:

```json
{
  "text": "Python atölyesi"
}
```

Yanıt örneği (HTTP 200):

```json
{
  "predictions": [
    {
      "category": "TECHNOLOGY",
      "confidence": 0.91
    },
    {
      "category": "CAREER",
      "confidence": 0.84
    }
  ]
}
```

Bu örnek, FakeClassifier'ın döndürdüğü sabit deneme sonucudur. Gerçek model tahmini değildir.

Her tahmin kendi `category` ve `confidence` alanlarını taşır.

Liste boş olamaz ve kategoriler tekrarlanamaz.

Tek kategorili yanıt da aynı liste yapısını kullanır (sözleşme örneği):

```json
{
  "predictions": [
    {
      "category": "OTHER",
      "confidence": 0.76
    }
  ]
}
```

Bu tek kategorili örnek, FakeClassifier'ın sabit çıktısı değildir.

Grup 3 sözleşmesi: [docs/ai-classify-contract.md](docs/ai-classify-contract.md).

Bu yanıt biçimi önceki tek `category/confidence` nesnesinden farklıdır. Grup 3 tüketicisinin de bu sözleşmeyi kullanması gerekir.

Geçersiz isteklerde HTTP 400 ve `error/message` alanları döner.

## Testler — Windows (PowerShell)

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Testler — macOS/Linux

Sanal ortam aktifken:

```bash
python -m pytest -q
```

Projedeki `pytest.ini` dosyası sayesinde normal test keşfi yalnızca `tests/` klasöründen yapılır.

Böylece `experiments/test_*.py` dosyaları standart API testleri sırasında otomatik çalıştırılmaz.

Gerçek modelin otomatik birim testlerinde model pipeline'ı taklit edilerek (mock) model indirmeden yükleme ve sınıflandırma kuralları kontrol edilebilir.

## Durum

- Gerçek AI modeli FastAPI servisine entegre edilmiştir.
- FakeClassifier varsayılan olarak korunmuştur.
- `CLASSIFIER_BACKEND=real` ile gerçek model kullanılabilir.
- Gerçek model için CPU inference doğrulanmıştır.
- Mevcut 26 API testi başarıyla geçmiştir.
- K3 tarafından geliştirilen `/health` router'ının uygulamaya entegrasyonu ayrıca tamamlanmalıdır.
- Docker ortamında gerçek modelin kullanılması için `CLASSIFIER_BACKEND=real` ayarı ve gerekli model bağımlılıkları kontrol edilmelidir.

## Hata Yönetimi

Sınıflandırma işlemindeki doğrulama, model ve beklenmeyen sunucu hata yanıtları `error` ve `message` alanlarını içerir.

| HTTP kodu | error | Açıklama |
|---|---|---|
| 400 | VALIDATION_ERROR | Boş metin, eksik alan, yanlış tür veya bozuk JSON |
| 503 | MODEL_UNAVAILABLE | Sınıflandırıcı ModelUnavailableError ürettiğinde |
| 500 | INTERNAL_SERVER_ERROR | Beklenmeyen sunucu hatası |

Beklenmeyen hataların teknik ayrıntıları istemciye gönderilmez, sunucu loguna yazılır.

Modelin kullanılamadığı durumlar `app.exceptions.ModelUnavailableError` ile bildirilebilir.

## OpenAPI Sözleşmesi

API tanımı [docs/ai-classify.openapi.yaml](docs/ai-classify.openapi.yaml)
dosyasında sürümlenir.

Swagger arayüzü: http://127.0.0.1:8005/docs

Çalışan servisin OpenAPI JSON adresi:
http://127.0.0.1:8005/openapi.json

API şemaları değiştiğinde YAML dosyası yeniden üretilmelidir.
Grup 3 bu sözleşmedeki istek, predictions listesi ve hata
yanıtlarını esas almalıdır.