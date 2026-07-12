"""
BKT Parameter Estimator — Grid Search
Acuan: Corbett & Anderson (1995), Baker et al. (2008)

Estimasi P(T), P(G), P(S) per KC dari training data.
P(L0) tetap dari ontologi (BKT+Onto) atau flat (Baseline).

Hasil estimasi disimpan ke JSON dan di-load oleh evaluator.
"""

import csv
import json
import math
import itertools
from collections import defaultdict
from pathlib import Path


# ─── Grid Search Space ────────────────────────────────────────────────────────
# Range mengacu Baker et al. (2008) — typical BKT parameter space
GRID = {
    "p_transit": [0.05, 0.10, 0.15, 0.20, 0.30, 0.40],
    "p_guess":   [0.10, 0.15, 0.20, 0.25, 0.30, 0.35],
    "p_slip":    [0.05, 0.08, 0.10, 0.15, 0.20, 0.25],
}

# Constraint dari Baker et al. (2008):
# P(G) < 1 - P(S) — guess rate harus lebih rendah dari non-slip rate
# Jika dilanggar, model tidak identifiable
def _is_valid(pG: float, pS: float) -> bool:
    return pG < (1 - pS)


# ─── Forward Algorithm (BKT likelihood) ──────────────────────────────────────
def _compute_log_likelihood(
    responses: list[int],  # urutan 0/1 untuk satu siswa satu KC
    p0: float,
    pT: float,
    pG: float,
    pS: float,
) -> float:
    """
    Hitung log-likelihood sequence respons berdasarkan BKT forward pass.
    Digunakan sebagai objective function grid search.
    """
    pL  = p0
    ll  = 0.0

    for correct in responses:
        p_correct = pL * (1 - pS) + (1 - pL) * pG
        p_obs     = p_correct if correct else (1 - p_correct)

        # Guard log(0)
        if p_obs <= 0:
            return float("-inf")
        ll += math.log(p_obs)

        # Update
        if correct:
            pL_given = (pL * (1 - pS)) / p_correct
        else:
            pL_given = (pL * pS) / (1 - p_correct)

        pL = pL_given + (1 - pL_given) * pT
        pL = max(0.001, min(0.999, pL))

    return ll


# ─── Load & Group Training Data ───────────────────────────────────────────────
def _load_kc_sequences(train_csv: str) -> dict[str, dict[str, list[int]]]:
    """
    Returns: {kc_id: {student_id: [correct, correct, ...]}}
    """
    data = defaultdict(lambda: defaultdict(list))
    with open(train_csv, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            data[row["kc_id"]][row["student_id"]].append(int(row["correct"]))
    return data


# ─── Grid Search per KC ───────────────────────────────────────────────────────
def estimate_parameters(
    train_csv: str,
    p0_map: dict[str, float],   # {kc_id: p0} — dari ontologi atau flat
    verbose: bool = True,
) -> dict[str, dict]:
    """
    Grid search parameter estimation per KC.
    Objective: maximize total log-likelihood across semua siswa untuk KC tersebut.
    """
    kc_sequences = _load_kc_sequences(train_csv)
    best_params  = {}

    all_pT = GRID["p_transit"]
    all_pG = GRID["p_guess"]
    all_pS = GRID["p_slip"]

    for kc_id, student_seqs in kc_sequences.items():
        p0       = p0_map.get(kc_id, 0.35)
        best_ll  = float("-inf")
        best     = {"p_transit": 0.10, "p_guess": 0.25, "p_slip": 0.10}

        for pT, pG, pS in itertools.product(all_pT, all_pG, all_pS):
            if not _is_valid(pG, pS):
                continue

            total_ll = sum(
                _compute_log_likelihood(seq, p0, pT, pG, pS)
                for seq in student_seqs.values()
            )

            if total_ll > best_ll:
                best_ll = total_ll
                best    = {"p_transit": pT, "p_guess": pG, "p_slip": pS}

        best_params[kc_id] = best
        if verbose:
            print(f"  {kc_id}: pT={best['p_transit']} pG={best['p_guess']} "
                  f"pS={best['p_slip']}  (ll={best_ll:.2f})")

    return best_params


# ─── Run ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import os, sys
    os.chdir(Path(__file__).parent)
    sys.path.insert(0, ".")

    from ontology import build_ontology, get_ontology_informed_prior

    G      = build_ontology("data/math_grade1.json")
    p0_onto = {kc: get_ontology_informed_prior(G, kc) for kc in G.nodes}
    p0_flat = {kc: 0.35 for kc in G.nodes}

    train_csv = "data/matematika_grade1_train.csv"

    print("=== Estimasi parameter — BKT+Ontologi ===")
    params_onto = estimate_parameters(train_csv, p0_onto)

    print("\n=== Estimasi parameter — BKT Baseline ===")
    params_base = estimate_parameters(train_csv, p0_flat)

    # Simpan hasil
    out = {
        "ontologi": params_onto,
        "baseline": params_base,
    }
    with open("data/estimated_params.json", "w") as f:
        json.dump(out, f, indent=2)

    print("\nSaved: data/estimated_params.json")
    print("Jalankan evaluator.py setelah ini.")
