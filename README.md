# CampusHub AI Service

FastAPI ile hazırlanmış deneme sınıflandırma servisi.

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

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8005
```

## Çalıştırma — macOS/Linux

Sanal ortam aktifken:

```bash
python -m uvicorn app.main:app --reload --port 8005
```

Swagger: http://127.0.0.1:8005/docs

## API

POST /ai/classify

İstek:
```json
{"text": "Python atölyesi"}
```

Yanıt:
```json
{"category": "TECHNOLOGY", "confidence": 0.91}
```

FakeClassifier her geçerli isteğe sabit deneme sonucu döndürür.
Bu sonuç gerçek model tahmini değildir.

Geçersiz isteklerde HTTP 400 ve error/message alanları döner.

## Testler — Windows (PowerShell)

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Testler — macOS/Linux

Sanal ortam aktifken:

```bash
python -m pytest -q
```

## Durum

/health router'ı uygulamaya bağlanmıştır. Gerçek model bağlantısı
henüz tamamlanmamıştır; şimdilik FakeClassifier kullanılmaktadır.

## Health & Model Lifecycle

GET /health, servisin trafik almaya hazır olup olmadığını modelin
durumuna göre bildirir (T06, T26).

| Durum | HTTP kodu | Yanıt |
|---|---|---|
| Model yüklendi | 200 | `{"service": "ai-service", "status": "UP", "version": "1.0.0"}` |
| Model hazır değil (`is_ready()` false) | 503 | `{"service": "ai-service", "status": "DOWN", "error": "MODEL_STARTING", "version": "1.0.0"}` |

### T26 tasarım kararı

- Model, ilk istekte (lazy) değil, uygulama başlarken FastAPI `lifespan`
  içinde bir kez ve **bloklayarak** yüklenir. Yükleme bitene kadar
  uvicorn port üzerinden istek kabul etmez; yani model yüklenirken
  /health 503 dönmez, bağlantı hiç kurulamaz. Bu bilinçli bir tercihtir:
  üretim ortamında model hazır olmadan servise trafik gelmemelidir.
- Container başlangıcındaki bu yükleme süresi Docker tarafında
  `HEALTHCHECK --start-period=30s` ile tolere edilir (bkz. `Dockerfile`).
  Bu süre içindeki başarısız kontroller container'ı `unhealthy` yapmaz;
  model belleğe yüklenip /health HTTP 200 döndüğünde container `healthy`
  durumuna geçer. Gerçek model (mDeBERTa) daha uzun sürede yükleniyorsa
  `--start-period` değeri artırılmalıdır.
- Model yüklemesi startup sırasında hata fırlatırsa uygulama ayağa
  kalkmaz ve container sonlanır; hata startup logunda görünür.
- Model hazır değilse veya runtime sırasında arızalanırsa
  (`is_ready()` false) /health HTTP 503 döner; sınıflandırıcının
  `ModelUnavailableError` fırlattığı istekler de HTTP 503
  `MODEL_UNAVAILABLE` alır. Docker healthcheck, Kubernetes readiness
  probe veya load balancer bu durumda servise trafik yönlendirmez.
- Hazır olma durumu sınıflandırıcının `is_ready()` metodu ile okunur
  (`app/contracts.py` içindeki `Classifier` arayüzü: `load()`,
  `is_ready()`, `classify()`). Gerçek model sınıfı da bu arayüzü
  uygulayarak aynı davranışı otomatik olarak alır.

### Ortam değişkenleri

| Değişken | Durum | Açıklama |
|---|---|---|
| `HOST`, `PORT` | Aktif | uvicorn'un dinlediği adres ve port (varsayılan `0.0.0.0:8005`) |
| `APP_ENV` | Tanımlı | Ortam adı (`development`, `production` vb.) |
| `MODEL_ID` | **Henüz kullanılmıyor** | Gerçek modelin Hugging Face kimliği (`MoritzLaurer/mDeBERTa-v3-base-mnli-xnli`) |
| `MODEL_REVISION` | **Henüz kullanılmıyor** | Model sürümü / branch / commit |
| `MODEL_PATH` | **Henüz kullanılmıyor** | Modelin yerel dizini |

> **Not:** `MODEL_ID`, `MODEL_REVISION` ve `MODEL_PATH` şu an
> `.env.example` içinde tanımlıdır ancak kod bu değerleri **henüz
> okumaz**, çünkü servis hâlâ `FakeClassifier` ile çalışır. Kişi 1
> (model geliştirici) gerçek mDeBERTa modelini `Classifier` arayüzüne
> bağladığında bu üç değişken kod tarafından okunacaktır. `torch` ve
> `transformers` bağımlılıkları bu entegrasyon için `requirements.txt`
> içine şimdiden eklenmiştir.
>
> `docker run --env-file` tırnak işaretlerini silmediği için
> `.env.example` değerleri tırnaksız yazılmalıdır.

## Docker

```bash
docker build -t campushub-ai-service .
docker run -d --name campushub-ai -p 8005:8005 --env-file .env.example campushub-ai-service
docker inspect --format '{{.State.Health.Status}}' campushub-ai   # starting -> healthy
curl -i http://127.0.0.1:8005/health
```

Healthcheck: `curl -f http://localhost:${PORT:-8005}/health`, ayarlar
`--interval=10s --timeout=3s --start-period=30s --retries=3`.

## Hata Yönetimi

Tüm hata yanıtları `error` ve `message` alanlarını içerir.

| HTTP kodu | error | Açıklama |
|---|---|---|
| 400 | VALIDATION_ERROR | Boş metin, eksik alan, yanlış tür veya bozuk JSON |
| 503 | MODEL_UNAVAILABLE | Sınıflandırıcı ModelUnavailableError ürettiğinde |
| 500 | INTERNAL_SERVER_ERROR | Beklenmeyen sunucu hatası |

Beklenmeyen hataların teknik ayrıntıları istemciye gönderilmez,
sunucu loguna yazılır.

Gerçek model entegrasyonunda modelin kullanılamadığı durumlar
app.exceptions.ModelUnavailableError ile bildirilmelidir.
