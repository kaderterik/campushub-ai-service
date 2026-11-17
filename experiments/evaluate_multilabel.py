"""CampusHub K1 — 337 development samples, multi-label zero-shot evaluation.

Run from repository root: python experiments/evaluate_multilabel.py
The 84-record final test set is intentionally NOT loaded by this script.
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
THRESHOLDS = (0.50, 0.70, 0.90, 0.95)
ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data/evaluation/CampusHub_421_GELISTIRME_DUZELTILMIS.json"
OUT_DIR = ROOT / "experiments/results"
CACHE_PATH = OUT_DIR / "multilabel_dev_scores.json"
REPORT_PATH = OUT_DIR / "multilabel_dev_metrics.json"


def validate_rows(rows):
    if not isinstance(rows, list) or len(rows) != 337:
        raise ValueError("337 kayıtlık geliştirme JSON'u bekleniyordu.")
    for i, row in enumerate(rows):
        expected = row.get("expected_categories")
        if (not isinstance(row.get("text"), str) or not row["text"].strip()
                or not isinstance(expected, list) or not expected
                or any(c not in CATEGORIES for c in expected)
                or len(expected) != len(set(expected))
                or row.get("split") != "development"):
            raise ValueError(f"Geçersiz geliştirme kaydı: {i + 1}")


def predict(scores, threshold):
    """OTHER is a fallback when none of the five topical labels pass threshold."""
    selected = {c for c in CATEGORIES if c != "OTHER" and scores[c] >= threshold}
    return selected if selected else {"OTHER"}


def calc_metrics(rows, scores, threshold):
    tp = {c: 0 for c in CATEGORIES}
    fp = {c: 0 for c in CATEGORIES}
    fn = {c: 0 for c in CATEGORIES}
    exact = 0
    for row, score in zip(rows, scores):
        expected = set(row["expected_categories"])
        predicted = predict(score, threshold)
        exact += int(expected == predicted)
        for c in CATEGORIES:
            tp[c] += int(c in expected and c in predicted)
            fp[c] += int(c not in expected and c in predicted)
            fn[c] += int(c in expected and c not in predicted)

    def prf(t, f_p, f_n):
        p = t / (t + f_p) if t + f_p else 0.0
        r = t / (t + f_n) if t + f_n else 0.0
        f1 = 2 * p * r / (p + r) if p + r else 0.0
        return {"precision": round(p, 4), "recall": round(r, 4), "f1": round(f1, 4),
                "tp": t, "fp": f_p, "fn": f_n}

    by_category = {c: prf(tp[c], fp[c], fn[c]) for c in CATEGORIES}
    micro = prf(sum(tp.values()), sum(fp.values()), sum(fn.values()))
    macro_f1 = sum(by_category[c]["f1"] for c in CATEGORIES) / len(CATEGORIES)
    return {
        "threshold": threshold,
        "micro": micro,
        "macro_f1": round(macro_f1, 4),
        "exact_match": round(exact / len(rows), 4),
        "exact_count": exact,
        "total": len(rows),
        "per_category": by_category,
    }


def main():
    from transformers import pipeline

    raw = DATA_PATH.read_bytes()
    rows = json.loads(raw)
    validate_rows(rows)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    signature = {
        "data_sha256": hashlib.sha256(raw).hexdigest(),
        "model": MODEL_ID, "revision": REVISION,
        "categories": CATEGORIES, "hypothesis_template": TEMPLATE,
        "multi_label": True,
    }

    cache = {"signature": signature, "scores": []}
    if CACHE_PATH.exists():
        loaded = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        if loaded.get("signature") == signature:
            cache = loaded
            print(f"Önceden hesaplanan {len(cache['scores'])} skor yüklendi.", flush=True)
        else:
            print("Veri/model değişmiş: eski skor önbelleği kullanılmıyor.", flush=True)
    if len(cache["scores"]) > len(rows):
        raise ValueError("Önbellekte beklenenden fazla kayıt var.")

    if len(cache["scores"]) < len(rows):
        print("Model yükleniyor (CPU)...", flush=True)
        classifier = pipeline(
            "zero-shot-classification", model=MODEL_ID,
            revision=REVISION, device=-1,
        )
        descriptions = list(CATEGORIES.values())
        descriptions_to_code = {v: k for k, v in CATEGORIES.items()}
        start = len(cache["scores"])
        for offset in range(start, len(rows), 4):
            chunk = rows[offset: offset + 4]
            results = classifier(
                [r["text"] for r in chunk],
                candidate_labels=descriptions,
                hypothesis_template=TEMPLATE,
                multi_label=True,
                batch_size=2,
            )
            if isinstance(results, dict):
                results = [results]
            for result in results:
                mapped = {descriptions_to_code[label]: float(score)
                          for label, score in zip(result["labels"], result["scores"])}
                if set(mapped) != set(CATEGORIES):
                    raise ValueError("Model bütün kategori skorlarını döndürmedi.")
                cache["scores"].append(mapped)
            # Save after every batch: an interrupted run can resume here.
            CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"İşlendi: {len(cache['scores'])}/{len(rows)}", flush=True)

    scores = cache["scores"]
    reports = [calc_metrics(rows, scores, t) for t in THRESHOLDS]
    REPORT_PATH.write_text(json.dumps({"policy": "five topical labels + OTHER fallback",
                                       "results": reports}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nEŞİK     PRECISION  RECALL     MICRO-F1   MACRO-F1   EXACT MATCH")
    for report in reports:
        micro = report["micro"]
        print(f"{report['threshold']:<8.2f} {micro['precision']:<10.4f} "
              f"{micro['recall']:<10.4f} {micro['f1']:<10.4f} "
              f"{report['macro_f1']:<10.4f} {report['exact_match']:.4f}")
    print(f"\nDetaylı sonuç: {REPORT_PATH}")
    print("NOT: Bu değerlendirmede yalnızca 337 geliştirme örneği kullanıldı; final test okunmadı.")


if __name__ == "__main__":
    main()
