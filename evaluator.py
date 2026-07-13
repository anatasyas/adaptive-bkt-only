"""
evaluator.py — BKT+Ontologi vs Sequential Baseline
Dengan tambahan Learning Gain dan Mastery Speed
"""

import csv, json, math, random, os
from collections import defaultdict
from pathlib import Path
import pandas as pd

from ontology import build_ontology

FLAT_PRIOR = 0.35

# ====================== METRIK HELPER ======================
def compute_auc_roc(preds):
    actual = [p["actual"] for p in preds]
    predicted = [p["predicted"] for p in preds]
    n_pos = sum(actual)
    n_neg = len(actual) - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.5
    thresholds = sorted(set(predicted), reverse=True)
    tpr_list, fpr_list = [0.0], [0.0]
    for t in thresholds:
        tp = sum(1 for a, p in zip(actual, predicted) if p >= t and a == 1)
        fp = sum(1 for a, p in zip(actual, predicted) if p >= t and a == 0)
        tpr_list.append(tp / n_pos)
        fpr_list.append(fp / n_neg)
    tpr_list.append(1.0)
    fpr_list.append(1.0)
    auc = sum((fpr_list[i]-fpr_list[i-1])*(tpr_list[i]+tpr_list[i-1])/2 
              for i in range(1, len(tpr_list)))
    return round(auc, 4)


def compute_rmse(preds):
    return round(math.sqrt(sum((p["predicted"] - p["actual"])**2 for p in preds) / len(preds)), 4)


def compute_accuracy(preds, threshold=0.5):
    correct = sum(1 for p in preds if (p["predicted"] >= threshold) == bool(p["actual"]))
    return round(correct / len(preds), 4)


def compute_learning_gain(preds):
    """Rata-rata peningkatan pengetahuan per soal"""
    gains = [p["p_after"] - p["p_before"] for p in preds 
             if "p_after" in p and "p_before" in p]
    return round(sum(gains) / len(gains), 4) if gains else 0.0


def compute_mastery_speed(by_student, threshold=0.85):
    """Rata-rata jumlah soal sampai mastery per kelompok pace"""
    speeds = defaultdict(list)
    
    for sid, rows in by_student.items():
        pace = rows[0].get("profile", "Average").capitalize()
        for i, row in enumerate(rows, 1):
            if row.get("p_after", 0) >= threshold:
                speeds[pace].append(i)
                break
        else:
            speeds[pace].append(len(rows))
    
    return {pace: round(sum(vals)/len(vals), 1) if vals else 0 
            for pace, vals in speeds.items()}


# ====================== MAIN EVALUATE ======================
def evaluate(train_csv: str, test_csv: str):
    # Load data
    rows_test = []
    with open(test_csv, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows_test.append({
                "student_id": row["student_id"],
                "profile": row["profile"],
                "kc_id": row["kc_id"],
                "opportunity": int(row["opportunity"]),
                "correct": int(row["correct"]),
                "p_before": float(row.get("p_before", FLAT_PRIOR)),
                "p_after": float(row.get("p_after", FLAT_PRIOR)),
            })

    by_student = defaultdict(list)
    for r in rows_test:
        by_student[r["student_id"]].append(r)

    print(f"Jumlah siswa: {len(by_student)} | Total interaksi: {len(rows_test)}\n")

    # Kumpulkan semua prediksi
    all_preds = []
    for rows in by_student.values():
        for row in rows:
            all_preds.append({
                "actual": row["correct"],
                "predicted": row["p_before"],
                "p_before": row["p_before"],
                "p_after": row["p_after"],
                "pace": row["profile"].capitalize()
            })

    df = pd.DataFrame(all_preds)

    # === Hasil per Group ===
    print("=== HASIL EVALUASI PER PACE GROUP ===")
    for pace in ["Slow", "Average", "Fast"]:
        group = df[df["pace"] == pace]
        if len(group) == 0:
            continue
        print(f"\n{pace} Learner ({len(group)} interaksi):")
        print(f"  AUC-ROC       : {compute_auc_roc(group.to_dict('records'))}")
        print(f"  RMSE          : {compute_rmse(group.to_dict('records'))}")
        print(f"  Accuracy      : {compute_accuracy(group.to_dict('records'))}")
        print(f"  Learning Gain : {compute_learning_gain(group.to_dict('records'))}")

    # Mastery Speed
    mastery = compute_mastery_speed(by_student)
    print("\n=== MASTERY SPEED (rata-rata soal sampai p_know >= 0.85) ===")
    for pace, speed in mastery.items():
        print(f"  {pace:8}: {speed:6.1f} soal")

    return df


# ====================== RUN ======================
if __name__ == "__main__":
    os.chdir(Path(__file__).parent)
    
    train_csv = "data/matematika_grade1_train.csv"
    test_csv  = "data/matematika_grade1_test.csv"

    print("Menjalankan Evaluasi BKT...\n")
    evaluate(train_csv, test_csv)
