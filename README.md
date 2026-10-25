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

Yanıt (HTTP 200):
```json
{
  "predictions": [
    {"category": "TECHNOLOGY", "confidence": 0.91},
    {"category": "CAREER", "confidence": 0.84}
  ]
}
```

FakeClassifier, gönderilen metnin konusundan bağımsız olarak her geçerli
isteğe yukarıdaki iki kategorili sabit deneme sonucunu döndürür.
Bu sonuç gerçek model tahmini değildir.

Kullanılabilen altı kategori: `TECHNOLOGY`, `SPORT`, `ART`, `CAREER`,
`SOCIAL` ve `OTHER`. Bir metin birden fazla konuya ait olabilir.
Her öğe kendi `confidence` değerini taşır; değerler 0–1 aralığındadır
ve toplamlarının 1 olması gerekmez. Liste boş olamaz ve kategoriler tekrarlanamaz.
`OTHER`, başka konu kategorisine uymayan içerikler için yalnızca tek başına döner.

Tek kategorili yanıt da aynı liste yapısını kullanır (sözleşme örneği):
```json
{
  "predictions": [
    {"category": "OTHER", "confidence": 0.76}
  ]
}
```

Bu tek kategorili örnek mevcut FakeClassifier'ın sabit çıktısı değildir.

Grup 3 sözleşmesi: [docs/ai-classify-contract.md](docs/ai-classify-contract.md).
Bu yanıt biçimi önceki category/confidence nesnesinden farklıdır;
Grup 3 tüketicisi ve K1 sınıflandırıcısı birlikte uyarlanmalıdır.

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

Gerçek model bağlantısı ve K3'ün hazırlayacağı /health router'ının
uygulamaya bağlanması henüz tamamlanmamıştır.

## Hata Yönetimi

Sınıflandırma işlemindeki doğrulama, model ve beklenmeyen sunucu hata yanıtları `error` ve `message` alanlarını içerir.

| HTTP kodu | error | Açıklama |
|---|---|---|
| 400 | VALIDATION_ERROR | Boş metin, eksik alan, yanlış tür veya bozuk JSON |
| 503 | MODEL_UNAVAILABLE | Sınıflandırıcı ModelUnavailableError ürettiğinde |
| 500 | INTERNAL_SERVER_ERROR | Beklenmeyen sunucu hatası |

Beklenmeyen hataların teknik ayrıntıları istemciye gönderilmez,
sunucu loguna yazılır.

Gerçek model entegrasyonunda modelin kullanılamadığı durumlar
app.exceptions.ModelUnavailableError ile bildirilmelidir.
