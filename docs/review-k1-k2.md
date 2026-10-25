# K1/K2 inceleme notları

İncelenen taban: origin/main b413e31. K3 branch'i bu değişikliğe alınmadı.

## Düzeltilen API sorunları

- İç sınıflandırıcı, servis, yanıt şeması, FakeClassifier ve API testleri tek
  kategoriden kategori/skor listesine taşındı.
- Boş, tekrarlı, yedinci kategorili ve OTHER ile başka konu karıştıran yanıtlar
  sunucu hatası olarak reddedilir. Bu, istemcinin hatası olmadığı için 400 değildir.
- Grup 3 örnekleri ve Swagger yanıt yapısı güncellendi.

## K1 branch'inde kalan işler (feature/k1-model)

- experiments/model_decision.md tek etiket ve multi_label=False kararı içeriyor.
  Değerlendirme scriptleri de labels[0] ve expected_category kullanıyor. Bu karar
  yeni çoklu etiket hedefiyle güncellenmeli; değerlendirme metrikleri de uyarlanmalı.
- app/models/classifier.py henüz yok; gerçek model bu API'ye entegre değil.
- experiments/benchmark_models.py Unix resource modülünü koşulsuz import ediyor.
  Windows'ta çalışmaz; RAM ölçümü platforma uygun uygulanmalı.
- Deneyler transformers kullanıyor, mevcut requirements.txt bu bağımlılığı
  tanımlamıyor. Model ortamının torch/transformers vb. paket sürümleri ayrıca
  sabitlenip CPU kurulumu doğrulanmalı.
- Model kararında revision SHA yazılı olsa da deney pipeline çağrıları revision
  geçmiyor. Tekrarlanabilir sonuçlar için seçilen sürüm çağrılarda da sabitlenmeli.
- Model indirme/gerçek inference çalıştırılmadı. Mevcut benchmark sayıları
  yeniden ölçülmedi; yalnızca scriptler ve kaydedilmiş sonuçlar incelendi.

## Yazım kontrolü

origin/main ve origin/feature/k1-model takip edilen içeriklerinde serive
bulunmadı. Python paket yolu app/services ve sınıf InferenceService doğru.
Yazım hatası GitHub depo adında campushub-ai-serive olarak bulunuyor.
GitHub depo yeniden adlandırması yapılmadı. Depo sahibi Settings > General >
Repository name alanından campushub-ai-service yapabilir. Ardından yerel
origin URL'si yeni ada göre güncellenmeli; mevcut olmayan yeni URL'ye şimdi
geçilmedi. Yerel klasör adının import yollarına etkisi yoktur.
