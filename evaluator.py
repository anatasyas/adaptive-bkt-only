"""
evaluator.py — BKT+Ontologi vs Sequential Baseline

Sequential Baseline merepresentasikan pembelajaran konvensional:
  - Urutan KC tetap (B01 → B02 → ... → A02), sama untuk semua siswa
  - Prediksi P(benar) = rata-rata akurasi KC dari data latih (empirical mean)
  - Tidak ada pembaruan knowledge state per siswa
  - Tidak ada pengecekan prasyarat

Metrik yang digunakan:
  Prediksi   : AUC-ROC, RMSE, Akurasi (one-step-ahead)
  Kurikulum  : Param Recovery RMSE P(L₀), Path Validity
"""

import csv, json, math, random, os
from collections import defaultdict
from pathlib import Path
import networkx as nx

from ontology import (
    build_ontology, get_available_kcs,
    get_ontology_informed_prior, get_prerequisites,
)
from bkt_engine import (
    StudentModel, KCState,
    init_student, process_response,
    select_next_kc, DEFAULT_BKT_PARAMS,
)

FLAT_PRIOR = 0.35


# ── Sequential Baseline ───────────────────────────────────────────────────────
def build_seq_predictor(train_csv: str) -> dict[str, float]:
    """Hitung rata-rata akurasi per KC dari data latih sebagai predictor."""
    acc_sum   = defaultdict(float)
    acc_count = defaultdict(int)
    with open(train_csv, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            acc_sum[row["kc_id"]]   += int(row["correct"])
            acc_count[row["kc_id"]] += 1
    return {
        kc: acc_sum[kc] / acc_count[kc]
        for kc in acc_sum if acc_count[kc] > 0
    }


def fixed_kc_order(G: nx.DiGraph) -> list[str]:
    """
    Urutan KC tetap: topological sort (ikuti prasyarat),
    merepresentasikan urutan buku/kurikulum konvensional.
    """
    try:
        return list(nx.topological_sort(G))
    except nx.NetworkXUnfeasible:
        return list(G.nodes)


# ── Load Dataset ──────────────────────────────────────────────────────────────
def load_dataset(csv_path: str) -> list[dict]:
    rows = []
    with open(csv_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append({
                "student_id": row["student_id"],
                "kc_id":      row["kc_id"],
                "opportunity":int(row["opportunity"]),
                "correct":    int(row["correct"]),
                "true_p0":    float(row.get("true_p0", FLAT_PRIOR)),
            })
    return rows


def group_by_student(rows: list[dict]) -> dict[str, list[dict]]:
    g = defaultdict(list)
    for r in rows:
        g[r["student_id"]].append(r)
    return dict(g)


def load_estimated_params(path: str = "data/estimated_params.json") -> dict:
    p = Path(path)
    if not p.exists():
        return {"ontologi": {}}
    with open(p, encoding="utf-8") as f:
        return json.load(f)


# ── Metrik Prediksi ───────────────────────────────────────────────────────────
def replay_bkt(student_rows: list[dict], G: nx.DiGraph,
               est_params: dict) -> list[dict]:
    """BKT+Ontologi: one-step-ahead prediction dengan update setiap langkah."""
    sid     = student_rows[0]["student_id"]
    student = init_student(sid, G, est_params)
    preds   = []
    for row in student_rows:
        kc_id = row["kc_id"]
        state = student.kc_states[kc_id]
        pL, pG, pS = state.p_know, state.p_guess, state.p_slip
        preds.append({
            "actual":    row["correct"],
            "predicted": pL * (1 - pS) + (1 - pL) * pG,
        })
        process_response(student, G, kc_id, bool(row["correct"]))
    return preds


def replay_sequential(student_rows: list[dict],
                      kc_mean: dict[str, float],
                      global_mean: float) -> list[dict]:
    """
    Sequential Baseline: prediksi = rata-rata akurasi KC dari training.
    Tidak ada update per siswa — sama untuk semua siswa.
    """
    return [
        {
            "actual":    row["correct"],
            "predicted": kc_mean.get(row["kc_id"], global_mean),
        }
        for row in student_rows
    ]


def compute_auc_roc(preds: list[dict]) -> float:
    actual    = [p["actual"]    for p in preds]
    predicted = [p["predicted"] for p in preds]
    n_pos = sum(actual); n_neg = len(actual) - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.5
    thresholds = sorted(set(predicted), reverse=True)
    tpr_list, fpr_list = [0.0], [0.0]
    for t in thresholds:
        tp = sum(1 for a, p in zip(actual, predicted) if p >= t and a == 1)
        fp = sum(1 for a, p in zip(actual, predicted) if p >= t and a == 0)
        tpr_list.append(tp / n_pos)
        fpr_list.append(fp / n_neg)
    tpr_list.append(1.0); fpr_list.append(1.0)
    return round(sum(
        (fpr_list[i]-fpr_list[i-1])*(tpr_list[i]+tpr_list[i-1])/2
        for i in range(1, len(tpr_list))
    ), 4)


def compute_rmse(preds: list[dict]) -> float:
    return round(math.sqrt(
        sum((p["predicted"] - p["actual"])**2 for p in preds) / len(preds)
    ), 4)


def compute_accuracy(preds: list[dict], threshold: float = 0.5) -> float:
    return round(
        sum(1 for p in preds if (p["predicted"] >= threshold) == bool(p["actual"]))
        / len(preds), 4
    )


# ── Param Recovery ────────────────────────────────────────────────────────────
def compute_param_recovery_bkt(by_student: dict, G: nx.DiGraph,
                                est_params: dict) -> float:
    """BKT+Onto: P(L₀) dari ontologi vs true P(L₀) dari data sintetis."""
    errors = []
    for student_rows in by_student.values():
        sid     = student_rows[0]["student_id"]
        student = init_student(sid, G, est_params)
        seen = set()
        for row in student_rows:
            kc_id = row["kc_id"]
            if kc_id not in seen:
                errors.append(
                    (student.kc_states[kc_id].p_know - row["true_p0"])**2
                )
                seen.add(kc_id)
            process_response(student, G, kc_id, bool(row["correct"]))
    return round(math.sqrt(sum(errors)/len(errors)), 4) if errors else 0.0


def compute_param_recovery_seq(by_student: dict) -> float:
    """Sequential: P(L₀) flat 0.35 vs true P(L₀). Tidak ada informasi ontologi."""
    errors = []
    for student_rows in by_student.values():
        seen = set()
        for row in student_rows:
            if row["kc_id"] not in seen:
                errors.append((FLAT_PRIOR - row["true_p0"])**2)
                seen.add(row["kc_id"])
    return round(math.sqrt(sum(errors)/len(errors)), 4) if errors else 0.0


# ── Path Validity ─────────────────────────────────────────────────────────────
def compute_path_validity_bkt(G: nx.DiGraph, est_params: dict,
                               n_sim: int, rng: random.Random) -> float:
    """Simulasi: berapa persen langkah BKT+Onto valid secara prasyarat."""
    question_bank = {
        kc: [1, 1, 0] for kc in G.nodes  # sederhana: 2 benar 1 salah
    }
    valid_steps = total_steps = 0

    for i in range(n_sim):
        student = init_student(f"sim_{i}", G, est_params)
        for _ in range(200):
            next_kc = select_next_kc(student, G)
            if next_kc is None:
                break
            prereqs = get_prerequisites(G, next_kc)
            mastered = {k for k, s in student.kc_states.items() if s.is_mastered}
            if all(p in mastered for p in prereqs):
                valid_steps += 1
            total_steps += 1
            correct = rng.choice(question_bank[next_kc])
            process_response(student, G, next_kc, bool(correct))

    return round(valid_steps / total_steps * 100, 1) if total_steps else 0.0


def compute_path_validity_seq(G: nx.DiGraph, n_sim: int,
                               rng: random.Random) -> float:
    """
    Sequential: urutan KC tetap. Hitung berapa persen langkah
    yang prasyaratnya sudah terpenuhi.
    """
    order = fixed_kc_order(G)
    valid_steps = total_steps = 0

    for _ in range(n_sim):
        mastered = set()
        for kc_id in order:
            prereqs = get_prerequisites(G, kc_id)
            if all(p in mastered for p in prereqs):
                valid_steps += 1
            total_steps += 1
            # Sequential: anggap siswa "menyelesaikan" KC ini
            # (berhasil mastery setelah N soal tetap)
            if rng.random() < 0.55:  # probabilitas mastery tiap KC
                mastered.add(kc_id)

    return round(valid_steps / total_steps * 100, 1) if total_steps else 0.0


# ── Full Evaluation ───────────────────────────────────────────────────────────
def evaluate(train_csv: str, test_csv: str, G: nx.DiGraph,
             rng: random.Random,
             estimated_params_path: str = "data/estimated_params.json",
             n_sim: int = 100) -> tuple[dict, dict]:

    rows_test  = load_dataset(test_csv)
    by_student = group_by_student(rows_test)
    all_est    = load_estimated_params(estimated_params_path)
    est_params = all_est.get("ontologi", {})

    kc_mean     = build_seq_predictor(train_csv)
    global_mean = sum(kc_mean.values()) / len(kc_mean) if kc_mean else 0.5

    # ── BKT+Ontologi ──
    print("  Menghitung BKT+Ontologi...")
    preds_bkt = []
    for student_rows in by_student.values():
        preds_bkt.extend(replay_bkt(student_rows, G, est_params))

    pr_bkt  = compute_param_recovery_bkt(by_student, G, est_params)
    pv_bkt  = compute_path_validity_bkt(G, est_params, n_sim, random.Random(rng.randint(0,99999)))

    bkt_results = {
        "auc_roc":             compute_auc_roc(preds_bkt),
        "rmse":                compute_rmse(preds_bkt),
        "accuracy":            compute_accuracy(preds_bkt),
        "param_recovery_rmse": pr_bkt,
        "path_validity_pct":   pv_bkt,
    }

    # ── Sequential Baseline ──
    print("  Menghitung Sequential Baseline...")
    preds_seq = []
    for student_rows in by_student.values():
        preds_seq.extend(replay_sequential(student_rows, kc_mean, global_mean))

    pr_seq  = compute_param_recovery_seq(by_student)
    pv_seq  = compute_path_validity_seq(G, n_sim, random.Random(rng.randint(0,99999)))

    seq_results = {
        "auc_roc":             compute_auc_roc(preds_seq),
        "rmse":                compute_rmse(preds_seq),
        "accuracy":            compute_accuracy(preds_seq),
        "param_recovery_rmse": pr_seq,
        "path_validity_pct":   pv_seq,
    }

    return bkt_results, seq_results


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    os.chdir(Path(__file__).parent)
    G         = build_ontology("data/math_grade1.json")
    train_csv = "data/matematika_grade1_train.csv"
    test_csv  = "data/matematika_grade1_test.csv"

    print("Menjalankan evaluasi (n_sim=100)...\n")
    bkt_r, seq_r = evaluate(train_csv, test_csv, G, random.Random(42), n_sim=100)

    METRICS = [
        ("AUC-ROC",                   "auc_roc",             "↑"),
        ("RMSE",                      "rmse",                "↓"),
        ("Akurasi",                   "accuracy",            "↑"),
        ("Param Recovery RMSE P(L₀)", "param_recovery_rmse", "↓"),
        ("Path Validity (%)",         "path_validity_pct",   "↑"),
    ]

    W = 28
    SEP = "─" * 70
    print(f"\n{SEP}")
    print(f"  {'Metrik':<{W}}  {'BKT+Ontologi':>14}  {'Seq Baseline':>12}  Better")
    print(SEP)
    for label, key, direction in METRICS:
        v1, v2 = bkt_r[key], seq_r[key]
        better = ("BKT+Onto" if (
            (direction == "↑" and v1 > v2) or
            (direction == "↓" and v1 < v2)
        ) else ("Baseline" if v1 != v2 else "tie"))
        print(f"  {label:<{W}}  {str(v1):>14}  {str(v2):>12}  {better}")
    print(SEP)
    print("\nInterpretasi:")
    print("  AUC-ROC, RMSE, Akurasi : kualitas prediksi P(benar) per langkah")
    print("  Param Recovery RMSE    : seberapa akurat sistem menginisialisasi P(L₀)")
    print("  Path Validity          : % langkah yang valid secara prasyarat kurikulum")
