"""
Synthetic Data Generator — BKT Generative Process

Generated data by Hidden Markov Model
"""

import json
import random
import csv
import math
from pathlib import Path
from dataclasses import dataclass, field

from ontology import build_ontology, get_available_kcs, get_kc_info


# ─── 1. Student Profiles ──────────────────────────────────────────────────────
# Tiga profil dengan parameter berbeda, mengacu pada Baker et al. (2008)
# Proporsi: slow 25%, average 50%, fast 25% — distribusi realistis kelas SD
STUDENT_PROFILES = {
    "slow": {
        "ratio":      0.25,
        "p_transit_scale": 0.5,   # P(T) lebih rendah → belajar lebih lambat
        "p_slip_scale":    1.8,   # P(S) lebih tinggi → sering slip
        "p_guess_scale":   0.85,
        "p0_scale":        0.6,   # prior lebih rendah — slow learner mulai jauh lebih rendah
    },
    "average": {
        "ratio":      0.50,
        "p_transit_scale": 1.0,
        "p_slip_scale":    1.0,
        "p_guess_scale":   1.0,
        "p0_scale":        1.0,
    },
    "fast": {
        "ratio":      0.25,
        "p_transit_scale": 1.8,   # P(T) lebih tinggi → belajar lebih cepat
        "p_slip_scale":    0.6,
        "p_guess_scale":   1.1,
        "p0_scale":        1.4,   # prior lebih tinggi — fast learner mulai lebih tinggi
    },
}

# BKT parameter defaults per KC — range dari Corbett & Anderson (1995)
# P(L0) akan di-override oleh ontologi, tapi P(T)/P(G)/P(S) pakai ini
DEFAULT_PARAMS = {
    "p_transit": 0.10,
    "p_guess":   0.25,
    "p_slip":    0.10,
}

KC_PARAM_OVERRIDES = {
    "KC-O07": {"p_transit": 0.07},
    "KC-B07": {"p_transit": 0.08},
    "KC-B08": {"p_transit": 0.07},
}

MAX_OPPORTUNITIES  = 30   # maks soal per KC per siswa
MASTERY_THRESHOLD  = 0.95 # sama dengan BKT engine


# ─── 2. BKT Generative Process ────────────────────────────────────────────────
def _get_true_params(kc_id: str, profile: dict, p0_from_ontology: float) -> dict:
    """
    Hitung parameter 'true' untuk generate data.
    P(L0) dari ontologi, sisanya dari profile + override.
    """
    base = dict(DEFAULT_PARAMS)
    if kc_id in KC_PARAM_OVERRIDES:
        base.update(KC_PARAM_OVERRIDES[kc_id])

    p0 = min(0.60, p0_from_ontology * profile["p0_scale"])
    pT = min(0.50, base["p_transit"] * profile["p_transit_scale"])
    pG = min(0.40, base["p_guess"]   * profile["p_guess_scale"])
    pS = min(0.35, base["p_slip"]    * profile["p_slip_scale"])

    return {"p0": round(p0, 4), "pT": round(pT, 4),
            "pG": round(pG, 4), "pS": round(pS, 4)}


def _simulate_kc_responses(
    kc_id: str,
    params: dict,
    rng: random.Random,
    until_mastered: bool = True,
) -> list[dict]:
    """
    Generate respons satu siswa untuk satu KC.
    Menggunakan BKT generative process (HMM).
    
    Returns list of {opportunity, correct, true_knowledge_state}
    """
    p0, pT, pG, pS = params["p0"], params["pT"], params["pG"], params["pS"]

    # Sample initial knowledge state
    L = 1 if rng.random() < p0 else 0

    records = []
    p_know_est = p0  # track estimated P(L) untuk deteksi mastery

    for opp in range(1, MAX_OPPORTUNITIES + 1):
        # Transition: jika belum tahu, mungkin belajar
        if L == 0 and rng.random() < pT:
            L = 1

        # Generate response berdasarkan hidden state
        if L == 1:
            correct = 1 if rng.random() < (1 - pS) else 0
        else:
            correct = 1 if rng.random() < pG else 0

        records.append({
            "opportunity":          opp,
            "correct":              correct,
            "true_knowledge_state": L,
        })

        # Update estimated P(L) — sama persis dengan BKT engine
        # (untuk deteksi kapan harus berhenti)
        if correct:
            p_obs    = p_know_est * (1 - pS) + (1 - p_know_est) * pG
            p_given  = (p_know_est * (1 - pS)) / p_obs
        else:
            p_obs    = p_know_est * pS + (1 - p_know_est) * (1 - pG)
            p_given  = (p_know_est * pS) / p_obs
        p_know_est = p_given + (1 - p_given) * pT
        p_know_est = max(0.001, min(0.999, p_know_est))

        # Berhenti jika estimasi sudah mastered
        if until_mastered and p_know_est >= MASTERY_THRESHOLD:
            break

    return records


# ─── 3. Simulate One Student ──────────────────────────────────────────────────
def _simulate_student(
    student_id: str,
    profile_name: str,
    profile: dict,
    G,
    p0_map: dict,
    rng: random.Random,
) -> list[dict]:
    """
    Simulate satu siswa dari awal sampai semua KC mastered (atau max attempts).
    Urutan KC mengikuti ontologi — valid secara kurikulum.
    """
    mastered  = set()
    all_rows  = []

    # Simulasi hingga tidak ada KC tersisa
    max_rounds = 200  # guard infinite loop
    rounds = 0

    while rounds < max_rounds:
        available = get_available_kcs(G, mastered)
        if not available:
            break  # semua KC selesai

        # Pilih KC dengan P(L0) terendah di antara yang available
        kc_id  = min(available, key=lambda k: p0_map[k])
        params = _get_true_params(kc_id, profile, p0_map[kc_id])
        responses = _simulate_kc_responses(kc_id, params, rng)

        for r in responses:
            all_rows.append({
                "student_id":          student_id,
                "profile":             profile_name,
                "kc_id":               kc_id,
                "opportunity":         r["opportunity"],
                "correct":             r["correct"],
                "true_knowledge_state":r["true_knowledge_state"],
                "true_p0":             params["p0"],
                "true_pT":             params["pT"],
                "true_pG":             params["pG"],
                "true_pS":             params["pS"],
            })

        # Cek apakah KC ini sudah mastered (pakai BKT forward pass cepat)
        if _is_mastered_after(responses, params):
            mastered.add(kc_id)

        rounds += 1

    return all_rows


def _is_mastered_after(responses: list[dict], params: dict) -> bool:
    """Re-run BKT estimasi untuk cek apakah siswa mastered di akhir sesi."""
    pL = params["p0"]
    pT, pG, pS = params["pT"], params["pG"], params["pS"]
    for r in responses:
        correct = r["correct"]
        if correct:
            p_obs = pL*(1-pS) + (1-pL)*pG
            pL    = (pL*(1-pS)) / p_obs
        else:
            p_obs = pL*pS + (1-pL)*(1-pG)
            pL    = (pL*pS) / p_obs
        pL = pL + (1-pL)*pT
        pL = max(0.001, min(0.999, pL))
    return pL >= MASTERY_THRESHOLD


# ─── 4. Main Generator ────────────────────────────────────────────────────────
def generate_dataset(
    data_path: str,
    n_students: int = 200,
    seed: int = 42,
    output_dir: str = "data",
) -> tuple[str, str]:
    """
    Generate dataset sintetis, split train/test by student (80/20).
    Returns: (train_path, test_path)
    """
    rng = random.Random(seed)
    G   = build_ontology(data_path)
    meta = G.graph["metadata"]

    # P(L0) dari ontologi untuk setiap KC
    from ontology import get_ontology_informed_prior
    p0_map = {kc_id: get_ontology_informed_prior(G, kc_id) for kc_id in G.nodes}

    # Tentukan profil setiap siswa sesuai rasio
    profiles = []
    for name, prof in STUDENT_PROFILES.items():
        count = round(n_students * prof["ratio"])
        profiles.extend([(name, prof)] * count)
    # Pastikan total = n_students
    while len(profiles) < n_students:
        profiles.append(("average", STUDENT_PROFILES["average"]))
    profiles = profiles[:n_students]
    rng.shuffle(profiles)

    # Generate semua siswa
    all_rows = []
    for i, (prof_name, prof) in enumerate(profiles):
        student_id = f"S{i+1:04d}"
        rows = _simulate_student(student_id, prof_name, prof, G, p0_map, rng)
        all_rows.extend(rows)
        if (i + 1) % 20 == 0:
            print(f"  Generated {i+1}/{n_students} students...")

    # Train/test split by student — bukan by interaction
    # Acuan: Yudelson et al. (2013)
    student_ids = list({r["student_id"] for r in all_rows})
    rng.shuffle(student_ids)
    split_idx   = int(len(student_ids) * 0.8)
    train_ids   = set(student_ids[:split_idx])
    test_ids    = set(student_ids[split_idx:])

    train_rows  = [r for r in all_rows if r["student_id"] in train_ids]
    test_rows   = [r for r in all_rows if r["student_id"] in test_ids]

    # Simpan ke CSV
    out = Path(output_dir)
    out.mkdir(exist_ok=True)

    subj  = meta["subject"].lower().replace(" ", "_")
    grade = meta["grade"]
    train_path = str(out / f"{subj}_grade{grade}_train.csv")
    test_path  = str(out / f"{subj}_grade{grade}_test.csv")

    fields = ["student_id","profile","kc_id","opportunity","correct",
              "true_knowledge_state","true_p0","true_pT","true_pG","true_pS"]

    for path, rows in [(train_path, train_rows), (test_path, test_rows)]:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    return train_path, test_path


# ─── 5. Validation: Learning Curve Check ─────────────────────────────────────
def validate_learning_curves(csv_path: str, sample_kcs: list[str] = None):
    """
    Validasi bahwa data punya pola belajar:
    akurasi rata-rata harus meningkat seiring opportunity.
    Ini bukti data tidak 'asal'.
    """
    from collections import defaultdict

    opp_correct = defaultdict(lambda: [0, 0])  # {opp: [correct, total]}

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if sample_kcs and row["kc_id"] not in sample_kcs:
                continue
            opp = int(row["opportunity"])
            opp_correct[opp][1] += 1
            opp_correct[opp][0] += int(row["correct"])

    print(f"\nLearning curve — {Path(csv_path).name}:")
    print(f"  {'Opp':>4}  {'Accuracy':>8}  {'N':>5}")
    for opp in sorted(opp_correct)[:10]:
        correct, total = opp_correct[opp]
        acc = correct / total if total > 0 else 0
        bar = "█" * int(acc * 20)
        print(f"  {opp:>4}  {acc:.3f}  {bar}  (n={total})")


# ─── Run ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).parent)

    print("Generating synthetic dataset (n=200 students)...")
    train_path, test_path = generate_dataset(
        data_path  = "data/math_grade1.json",
        n_students = 200,
        seed       = 42,
        output_dir = "data",
    )

    # Summary
    def count_rows(path):
        with open(path) as f:
            return sum(1 for _ in f) - 1

    train_n = count_rows(train_path)
    test_n  = count_rows(test_path)
    print(f"\nDataset:")
    print(f"  Train : {train_path}  ({train_n:,} interactions)")
    print(f"  Test  : {test_path}  ({test_n:,} interactions)")

    # Validasi learning curve
    validate_learning_curves(train_path, sample_kcs=["KC-O02", "KC-B01"])
