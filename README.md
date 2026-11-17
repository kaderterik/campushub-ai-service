
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

### Sistem testleri (T18)

`tests/system/` altındaki testler servisi gerçek bir uvicorn süreci olarak
(FakeClassifier ile) başlatır ve ona gerçek HTTP istekleri gönderir:

- `/health` ve `/ai/classify` yanıtlarının sözleşmeye uyumu (liste, kategori seti, 0–1 skor, OTHER tek başına)
- Geçersiz istekler ve bozuk JSON için 400, yanlış method için 405, bilinmeyen yol için 404
- 30 eşzamanlı istek, uzun ve Türkçe karakterli metin
- Başlangıç yaşam döngüsü: model yüklenirken bağlantı kurulamaz, yükleme bitince ilk yanıt 200 UP olur; yükleme başarısız olursa süreç kapanır
- Grup 3 istemci taklidi: AI servisine bağlanılamazsa `unavailable`, bağlanıp yanıt alınamazsa `timeout` sonucu

Normal `pytest` çalıştırmasına dahildir; ek bir ayar gerekmez.

### Grup 3 Event Service taklidi

`scripts/mock_event_service.py`, Event Service'in AI servisini nasıl çağıracağını gösterir.
Servis çalışırken:

```bash
python scripts/mock_event_service.py --url http://127.0.0.1:8005 --timeout 5
python scripts/mock_event_service.py --text "Bahar şenliği konseri"
```

AI servisi kapalıysa veya zaman aşımına uğrarsa betik çökmez; etkinliğin
kategorisiz kaydedileceğini bildirir. Gerçek timeout değeri ve bu davranış
Grup 3 ile kesinleştirilecektir (T19).

## Durum

- Gerçek AI modeli (mDeBERTa) FastAPI servisine entegre edilmiştir.
- FakeClassifier varsayılan olarak korunmuştur; `CLASSIFIER_BACKEND=real` ile gerçek model kullanılır.
- Gerçek model için CPU inference doğrulanmıştır.
- `/health` router'ı uygulamaya bağlanmıştır; hem FakeClassifier hem MDeBERTaClassifier `load()` / `is_ready()` arayüzünü uygular.

## Health & Model Lifecycle

GET /health, servisin trafik almaya hazır olup olmadığını modelin
durumuna göre bildirir (T06, T26).

| Durum | HTTP kodu | Yanıt |
|---|---|---|
| Model yüklendi | 200 | `{"service": "ai-service", "status": "UP", "version": "1.0.0"}` |
| Model hazır değil (`is_ready()` false) | 503 | `{"service": "ai-service", "status": "DOWN", "error": "MODEL_STARTING", "version": "1.0.0"}` |

### T26 tasarım kararı

- Model, ilk istekte (lazy) değil, uygulama başlarken FastAPI `lifespan`
  içinde bir kez ve **bloklayarak** yüklenir (`classifier.load()`).
  Yükleme bitene kadar uvicorn port üzerinden istek kabul etmez; yani
  model yüklenirken /health 503 dönmez, bağlantı hiç kurulamaz. Bu
  bilinçli bir tercihtir: üretim ortamında model hazır olmadan servise
  trafik gelmemelidir.
- Container başlangıcındaki bu yükleme süresi Docker tarafında
  `HEALTHCHECK --start-period=300s` ile tolere edilir (bkz. `Dockerfile`).
  Gerçek model önbellekte yoksa ilk açılışta Hugging Face'ten indirildiği
  için bu süre FakeClassifier'a göre çok daha uzundur. Bu süre içindeki
  başarısız kontroller container'ı `unhealthy` yapmaz; model yüklenip
  /health HTTP 200 döndüğünde container `healthy` durumuna geçer.
- Model yüklemesi startup sırasında hata fırlatırsa
  (`ModelUnavailableError`) uygulama ayağa kalkmaz ve container sonlanır;
  hata startup logunda görünür.
- Model hazır değilse (`is_ready()` false) /health HTTP 503 döner;
  sınıflandırıcının `ModelUnavailableError` fırlattığı istekler (ör.
  runtime inference hatası) HTTP 503 `MODEL_UNAVAILABLE` alır. Docker
  healthcheck, Kubernetes readiness probe veya load balancer bu durumda
  servise trafik yönlendirmez.
- Hazır olma durumu sınıflandırıcının `is_ready()` metodu ile okunur
  (`app/contracts.py` içindeki `Classifier` arayüzü: `load()`,
  `is_ready()`, `classify() -> list[ClassificationResult]`).

### Ortam değişkenleri

| Değişken | Varsayılan | Açıklama |
|---|---|---|
| `CLASSIFIER_BACKEND` | `fake` | `real` verilirse gerçek mDeBERTa modeli, aksi halde FakeClassifier kullanılır |
| `HOST`, `PORT` | `0.0.0.0`, `8005` | uvicorn'un dinlediği adres ve port (Docker imajında) |
| `APP_ENV` | `development` | Ortam adı (`development`, `production` vb.) |

> **Not:** Model kimliği (`MoritzLaurer/mDeBERTa-v3-base-mnli-xnli`) ve
> sabitlenmiş revision, değerlendirme sonuçlarıyla birebir uyum için
> `app/models/classifier.py` içinde sabit (`MODEL_ID`, `MODEL_REVISION`)
> olarak tanımlıdır; ortam değişkeninden okunmaz.
>
> `docker run --env-file` tırnak işaretlerini silmediği için
> `.env.example` değerleri tırnaksız yazılmalıdır.

## Docker

```bash
docker build -t campushub-ai-service .

# Varsayılan: FakeClassifier
docker run -d --name campushub-ai -p 8005:8005 --env-file .env.example campushub-ai-service

# Gerçek AI modeli (demo için bu kullanılmalı)
docker run -d --name campushub-ai -p 8005:8005 --env-file .env.example -e CLASSIFIER_BACKEND=real campushub-ai-service

docker inspect --format '{{.State.Health.Status}}' campushub-ai   # starting -> healthy
curl -i http://127.0.0.1:8005/health
```

Healthcheck: `curl -f http://localhost:${PORT:-8005}/health`, ayarlar
`--interval=10s --timeout=3s --start-period=300s --retries=3`.

Gerçek model ilk açılışta indirildiği için yavaş bağlantıda 300 sn'lik
start-period aşılabilir; bu durumda container bir süre `unhealthy` görünür ve
model yüklenip /health 200 döndüğünde kendiliğinden `healthy` olur. Bunu
önlemek için aşağıdaki kalıcı model önbelleğini kullanın.

### Docker Compose ve kalıcı model önbelleği

```bash
docker compose up -d --build
docker inspect --format '{{.State.Health.Status}}' campushub-ai
curl -i http://127.0.0.1:8005/health
docker compose down        # volume ve model silinmez
```

Volume daha önce `docker run` ile oluşturulduysa compose `volume "campushub-hf"
already exists but was not created by Docker Compose` uyarısı verir; bu uyarı
zararsızdır, mevcut volume ve içindeki model kullanılır.

Compose varsayılan olarak gerçek modeli (`CLASSIFIER_BACKEND=real`) açar ve
Hugging Face önbelleğini `campushub-hf` volume'unda tutar. Model yalnızca ilk
açılışta indirilir; sonraki açılışlar saniyeler sürer.

### Çevrimdışı çalıştırma (T17)

Model `campushub-hf` volume'una bir kez indirildikten sonra servis internet
olmadan açılabilir:

```bash
docker run -d --name campushub-ai-offline --network none \
  -e CLASSIFIER_BACKEND=real -e HF_HUB_OFFLINE=1 \
  -v campushub-hf:/home/appuser campushub-ai-service
docker exec campushub-ai-offline curl -s http://localhost:8005/health
```

Model daha önce yerelde (venv ile) indirildiyse, tekrar indirmek yerine
Windows/macOS önbelleğinden volume'a kopyalanabilir:

```bash
docker run --rm --user root \
  -v ~/.cache/huggingface/hub:/src:ro -v campushub-hf:/home/appuser \
  campushub-ai-service sh -c "rm -rf /home/appuser/.cache/huggingface && mkdir -p /home/appuser/.cache/huggingface && cp -r /src /home/appuser/.cache/huggingface/hub && chown -R appuser:appuser /home/appuser/.cache"
```

Windows cmd'de `~/.cache/...` yerine `%USERPROFILE%\.cache\huggingface\hub`
yazılır. `docker cp` ile Windows klasörüne kopyalama önerilmez: Hugging Face
önbelleğindeki symlink'ler Windows'ta oluşturulamaz ve model bulunamaz.

T17 doğrulaması (17 Kasım 2026): imajda yalnızca `torch 2.14.1+cpu` var
(`nvidia`/CUDA paketi yok); `--network none` ile container saniyeler içinde
`healthy` oldu ve `/ai/classify` gerçek model skorlarını döndürdü.

## Karar Günlüğü

| Tarih | Karar |
|---|---|
| 2026-10 | T26: Model `lifespan` içinde bloklayarak yüklenir; yükleme süresi Docker `start-period` ile tolere edilir. |
| 2026-11 | `transformers==4.57.6` sabit tutulur; 5.x model uyumluluğu doğrulanmadan alınmaz. |
| 2026-11 | Model kimliği ve revision (`8adb042d524ecd5c26d3e3ba0e3fbcf7e2d0864c`) `app/models/classifier.py` içinde sabittir; ortam değişkeninden okunmaz. |
| 2026-11 | Docker'da torch CPU sürümü kullanılır; model önbelleği `campushub-hf` volume'unda kalıcıdır. |

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
Dosya tam servis şemasıdır; `/ai/classify` ve `/health` yollarını içerir.

Swagger arayüzü: http://127.0.0.1:8005/docs

Çalışan servisin OpenAPI JSON adresi:
http://127.0.0.1:8005/openapi.json

API şemaları değiştiğinde depo kökünden yeniden üretin:

```bash
python -m scripts.export_openapi
```

Windows'ta sanal ortam aktif değilse:

```powershell
.\.venv\Scripts\python.exe -m scripts.export_openapi
```

Bu komut uygulama başlangıcını çalıştırmaz ve model ağırlıklarını indirmez.
PyYAML bağımlılığı requirements.txt içinde sabitlenmiştir.

Grup 3 için istek, predictions listesi ve hata kuralları
[API sözleşmesinde](docs/ai-classify-contract.md) açıklanır.
Ortak `campushub-integration` deposuna taşıma, Grup 3 kabulü ve gerçek Event Service
testleri henüz tamamlandı sayılmaz. Erişim, ortak adres, gönderilecek metin,
timeout ve kesinti davranışı [entegrasyon takibinde](docs/group3-integration.md)
ayrı ayrı izlenir.
