"""CampusHub Group 5 K1 — T29 frozen 84-row FINAL holdout evaluation.

Run ONCE from repository root: python experiments/evaluate_final_84.py

The code never selects/tunes thresholds on holdout data, and does not read the
old 18-record holdout. An interrupted inference can resume from saved scores.
If a complete final report already exists, it will not rerun inference.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

MODEL_ID = "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"
REVISION = "8adb042d524ecd5c26d3e3ba0e3fbcf7e2d0864c"
CATEGORIES = {
    "TECHNOLOGY": "teknoloji ve yazılım",
    "SPORT": "spor",
    "ART": "sanat, müzik ve kültür",
    "CAREER": "kariyer ve iş hayatı",
    "SOCIAL": "sosyal buluşma ve gönüllülük",
    "OTHER": "üniversite idari işlemleri, genel bilgilendirme ve öğrenci duyuruları",
}
TEMPLATE = "Bu metin {} ile ilgilidir."
THRESHOLD = 0.70  # Fixed BEFORE any final-test model inference.
FINAL_SHA256 = "a423b7359d8b35c5dc1851d5484d487dbf2d1d5a81f693f1163122fcbbb5899e"
DEV_SHA256 = "462e05cda851c3be6b9c6fc1937d582978e901d62772964da8840ed56ea4fe1b"
ROOT = Path(__file__).resolve().parents[1]
FINAL_PATH = ROOT / "data/evaluation/final_test_84.json"
DEV_PATH = ROOT / "data/evaluation/CampusHub_421_GELISTIRME_DUZELTILMIS.json"
OUT_DIR = ROOT / "experiments/results"
SCORES_PATH = OUT_DIR / "multilabel_final_scores.json"
REPORT_PATH = OUT_DIR / "multilabel_final_metrics.json"


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def validate(rows: object, name: str, n: int, split: str) -> None:
    if not isinstance(rows, list) or len(rows) != n:
        raise ValueError(f"{name}: {n} kayıt bekleniyordu.")
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise ValueError(f"{name}: {index}. kayıt bir nesne değil.")
        expected = row.get("expected_categories")
        if (not isinstance(row.get("text"), str)
                or not row["text"].strip()
                or not isinstance(expected, list) or not expected
                or len(expected) != len(set(expected))
                or any(c not in CATEGORIES for c in expected)
                or row.get("split") != split):
            raise ValueError(f"{name}: {index}. kayıt geçersiz.")


def predict(scores: dict, threshold: float = THRESHOLD) -> set[str]:
    """Five topical labels with OTHER ONLY as fallback (identical to T11)."""
    chosen = {c for c in CATEGORIES if c != "OTHER" and scores[c] >= threshold}
    return chosen if chosen else {"OTHER"}


def metrics(rows: list, scores: list) -> dict:
    tp = {c: 0 for c in CATEGORIES}
    fp = {c: 0 for c in CATEGORIES}
    fn = {c: 0 for c in CATEGORIES}
    exact = partial = no_hit = 0
    for row, score in zip(rows, scores):
        expected = set(row["expected_categories"])
        chosen = predict(score)
        if chosen == expected:
            exact += 1
        elif chosen & expected:
            partial += 1
        else:
            no_hit += 1
        for c in CATEGORIES:
            tp[c] += int(c in expected and c in chosen)
            fp[c] += int(c not in expected and c in chosen)
            fn[c] += int(c in expected and c not in chosen)

    def prf(t, f_p, f_n):
        p = t / (t + f_p) if t + f_p else 0.0
        r = t / (t + f_n) if t + f_n else 0.0
        f = 2 * p * r / (p + r) if p + r else 0.0
        return {"precision": round(p, 4), "recall": round(r, 4),
                "f1": round(f, 4), "tp": t, "fp": f_p, "fn": f_n}

    per_category = {c: prf(tp[c], fp[c], fn[c]) for c in CATEGORIES}
    micro = prf(sum(tp.values()), sum(fp.values()), sum(fn.values()))
    macro = round(sum(v["f1"] for v in per_category.values()) / len(per_category), 4)
    total = len(rows)
    passed = micro["f1"] >= 0.60 and exact / total >= 0.45
    return {
        "policy": "five topical labels + OTHER fallback",
        "threshold": THRESHOLD,
        "sample_count": total,
        "micro": micro,
        "macro_f1": macro,
        "exact_match": round(exact / total, 4),
        "exact_count": exact,
        "partial_count": partial,
        "no_correct_category_count": no_hit,
        "at_least_one_correct_count": exact + partial,
        "at_least_one_correct_rate": round((exact + partial) / total, 4),
        "per_category": per_category,
        "provisional_internal_targets": {"micro_f1_min": 0.60, "exact_match_min": 0.45,
                                        "met": passed},
        "note": "Internal proposed targets, not mandatory course requirements. Do not tune on holdout results.",
    }


def write_json(path: Path, data: object) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def main() -> None:
    # Avoid a second, accidental holdout evaluation.
    if REPORT_PATH.exists():
        print(f"T29 zaten tamamlanmış; tekrar çalıştırılmadı: {REPORT_PATH}")
        print(REPORT_PATH.read_text(encoding="utf-8"))
        return

    # Freeze both data files; reject accidental mix-ups or post-hoc edits.
    final_bytes = FINAL_PATH.read_bytes()
    dev_bytes = DEV_PATH.read_bytes()
    if sha256(final_bytes) != FINAL_SHA256:
        raise ValueError("84'lük final JSON beklenen sabit dosya değil; işlem DURDURULDU.")
    if sha256(dev_bytes) != DEV_SHA256:
        raise ValueError("337'lik geliştirme dosyası değişmiş; işlem DURDURULDU.")
    rows = json.loads(final_bytes)
    dev_rows = json.loads(dev_bytes)
    validate(rows, "final test", 84, "final_test")
    validate(dev_rows, "development", 337, "development")
    final_texts = {r["text"].strip() for r in rows}
    dev_texts = {r["text"].strip() for r in dev_rows}
    if final_texts & dev_texts:
        raise ValueError("Final ve geliştirme verisinde birebir tekrar bulundu!")

    signature = {
        "data_sha256": FINAL_SHA256,
        "model": MODEL_ID,
        "revision": REVISION,
        "categories": CATEGORIES,
        "hypothesis_template": TEMPLATE,
        "multi_label": True,
        "threshold": THRESHOLD,
        "policy": "five topical labels + OTHER fallback",
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cache = {"signature": signature, "scores": []}
    if SCORES_PATH.exists():
        old = json.loads(SCORES_PATH.read_text(encoding="utf-8"))
        if old.get("signature") != signature:
            raise ValueError("Önceki final skor dosyasının yapılandırması farklı; üzerine yazılmayacak.")
        cache = old
        print(f"Önceden kaydedilmiş {len(cache['scores'])} skor bulundu.", flush=True)
    if len(cache["scores"]) > len(rows):
        raise ValueError("Skor kaydı 84 örnekten uzun; işlem durduruldu.")

    if len(cache["scores"]) < len(rows):
        from transformers import pipeline
        print("Sabit mDeBERTa modeli CPU'da yükleniyor...", flush=True)
        classifier = pipeline("zero-shot-classification", model=MODEL_ID,
                              revision=REVISION, device=-1)
        descriptions = list(CATEGORIES.values())
        reverse = {v: k for k, v in CATEGORIES.items()}
        for start in range(len(cache["scores"]), len(rows), 4):
            chunk = rows[start:start + 4]
            outputs = classifier([r["text"] for r in chunk],
                                 candidate_labels=descriptions,
                                 hypothesis_template=TEMPLATE,
                                 multi_label=True, batch_size=2)
            if isinstance(outputs, dict):
                outputs = [outputs]
            if len(outputs) != len(chunk):
                raise ValueError("Model beklenen sayıda tahmin döndürmedi.")
            for result in outputs:
                mapped = {reverse[desc]: float(value)
                          for desc, value in zip(result["labels"], result["scores"])}
                if set(mapped) != set(CATEGORIES):
                    raise ValueError("Model altı kategori için de skor döndürmedi.")
                cache["scores"].append(mapped)
            write_json(SCORES_PATH, cache)  # Resume safely if interrupted.
            print(f"İşlendi: {len(cache['scores'])}/84", flush=True)

    report = {"signature": signature, "results": metrics(rows, cache["scores"])}
    write_json(REPORT_PATH, report)
    result = report["results"]
    print("\nT29 FINAL — 84 örnek, SABİT eşik 0.70")
    print(f"Precision:       {result['micro']['precision']:.4f}")
    print(f"Recall:          {result['micro']['recall']:.4f}")
    print(f"Micro-F1:        {result['micro']['f1']:.4f}")
    print(f"Macro-F1:        {result['macro_f1']:.4f}")
    print(f"Exact Match:     {result['exact_count']}/84 (%{100*result['exact_match']:.2f})")
    print(f"Kısmen doğru:    {result['partial_count']}")
    print(f"Hiç doğru yok:   {result['no_correct_category_count']}")
    print(f"En az bir doğru: {result['at_least_one_correct_count']}/84")
    print(f"İç hedefler:     {'Karşılandı' if result['provisional_internal_targets']['met'] else 'Karşılanmadı'}")
    print(f"Sonuç dosyası:   {REPORT_PATH}")
    print("Final test sonuçlarına göre model/eşik/kategori açıklamaları değiştirilmeyecek.")


if __name__ == "__main__":
    main()
