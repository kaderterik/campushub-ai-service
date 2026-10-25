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
| Model henüz hazır değil | 503 | `{"service": "ai-service", "status": "DOWN", "error": "MODEL_STARTING", "version": "1.0.0"}` |

### T26 tasarım kararı

- Model, ilk istekte (lazy) değil, uygulama başlarken FastAPI `lifespan`
  içinde bir kez yüklenir. Böylece ilk kullanıcı isteği model yükleme
  süresini beklemez ve yükleme hataları istek anında değil, startup
  sırasında ortaya çıkar.
- Model yüklenip hazır olana kadar /health HTTP 503 ve
  `MODEL_STARTING` döner. Docker healthcheck, Kubernetes readiness probe
  veya load balancer bu sürede servise trafik yönlendirmez; model
  hazır olduğunda yanıt HTTP 200'e döner.
- Hazır olma durumu sınıflandırıcının `is_ready()` metodu ile okunur
  (`app/contracts.py` içindeki `Classifier` arayüzü: `load()`,
  `is_ready()`, `classify()`). Gerçek model sınıfı da bu arayüzü
  uygulayarak aynı davranışı otomatik olarak alır.
- Model ayarları ortam değişkenlerinden gelir (bkz. `.env.example`):
  `MODEL_ID`, `MODEL_REVISION` ve `MODEL_PATH`.

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
