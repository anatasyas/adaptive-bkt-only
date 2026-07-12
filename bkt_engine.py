"""
BKT Engine — Bayesian Knowledge Tracing + Ontologi Integration
Referensi: Corbett & Anderson (1995)

Integrasi ontologi di 4 titik:
  1. P(L0) per KC dari ontologi (bukan flat default)
  2. P(T) per KC dari ontologi (integrasi baru)
  3. Mastery propagation: KC mastered -> boost prior KC dependennya
  4. Adaptive selection: learning-gain-aware KC selection
"""

from dataclasses import dataclass, field
from typing import Optional
import networkx as nx

from ontology import (
    get_ontology_informed_prior,
    get_ontology_informed_transit,
    get_prerequisites,
    get_available_kcs,
    get_kc_info,
    get_expected_learning_gain,
)

# ─── Default params (P(G) dan P(S) dari literatur) ────────────────────────────
DEFAULT_BKT_PARAMS = {
    "p_transit":         0.10,
    "p_guess":           0.25,
    "p_slip":            0.10,
    "mastery_threshold": 0.80,
}

# Override P(G)/P(S) per KC jika diperlukan
KC_PARAM_OVERRIDES: dict = {}


# ─── Data Structures ──────────────────────────────────────────────────────────
@dataclass
class KCState:
    kc_id: str
    p_know: float
    p_transit: float        # dari ontologi (integrasi 4)
    p_guess: float
    p_slip: float
    mastery_threshold: float
    n_correct: int = 0
    n_incorrect: int = 0

    @property
    def is_mastered(self) -> bool:
        return self.p_know >= self.mastery_threshold

    @property
    def n_attempts(self) -> int:
        return self.n_correct + self.n_incorrect


@dataclass
class StudentModel:
    student_id: str
    kc_states: dict[str, KCState] = field(default_factory=dict)
    history: list[dict] = field(default_factory=list)

    def mastered_set(self) -> set[str]:
        return {kc_id for kc_id, s in self.kc_states.items() if s.is_mastered}


# ─── BKT Core ─────────────────────────────────────────────────────────────────
def bkt_update(state: KCState, correct: bool) -> float:
    """
    Update P(L_n) berdasarkan satu respons.
    Formula Corbett & Anderson (1995).
    """
    pL, pT, pG, pS = state.p_know, state.p_transit, state.p_guess, state.p_slip

    if correct:
        p_obs    = pL * (1 - pS) + (1 - pL) * pG
        pL_given = (pL * (1 - pS)) / p_obs
    else:
        p_obs    = pL * pS + (1 - pL) * (1 - pG)
        pL_given = (pL * pS) / p_obs

    pL_new = pL_given + (1 - pL_given) * pT
    pL_new = max(0.001, min(0.999, pL_new))

    state.p_know = round(pL_new, 4)
    if correct:
        state.n_correct += 1
    else:
        state.n_incorrect += 1

    return state.p_know


# ─── Init Student ─────────────────────────────────────────────────────────────
def init_student(student_id: str, G: nx.DiGraph,
                 estimated_params: dict = None) -> StudentModel:
    """
    Inisialisasi StudentModel dari ontologi.

    Integrasi 1: P(L₀) dari get_ontology_informed_prior()
    Integrasi 4: P(T)  dari get_ontology_informed_transit()

    Jika estimated_params tersedia (dari grid search pada data latih),
    P(T) dari ontologi di-blend dengan P(T) hasil estimasi:
        P(T)_final = 0.6 * P(T)_estimasi + 0.4 * P(T)_ontologi
    Blending memastikan data informasi ontologi tetap berkontribusi
    bahkan setelah estimasi. Koefisien 0.6/0.4 mengacu pada
    pendekatan prior-informed estimation (Baker et al. 2008).
    """
    est = estimated_params or {}
    student = StudentModel(student_id=student_id)

    for kc_id in G.nodes:
        params = dict(DEFAULT_BKT_PARAMS)
        if kc_id in KC_PARAM_OVERRIDES:
            params.update(KC_PARAM_OVERRIDES[kc_id])

        # Integrasi 1: P(L₀) dari ontologi
        p0 = get_ontology_informed_prior(G, kc_id)

        # Integrasi 4: P(T) dari ontologi, di-blend dengan estimasi jika ada
        pt_onto = get_ontology_informed_transit(G, kc_id, base_pt=0.10)
        if kc_id in est:
            pt_est  = est[kc_id].get("p_transit", pt_onto)
            pt_final = round(0.6 * pt_est + 0.4 * pt_onto, 4)
        else:
            pt_final = pt_onto

        pG = est.get(kc_id, {}).get("p_guess", params["p_guess"])
        pS = est.get(kc_id, {}).get("p_slip",  params["p_slip"])

        student.kc_states[kc_id] = KCState(
            kc_id             = kc_id,
            p_know            = p0,
            p_transit         = pt_final,
            p_guess           = pG,
            p_slip            = pS,
            mastery_threshold = params["mastery_threshold"],
        )

    return student


# ─── Process Response ─────────────────────────────────────────────────────────
def process_response(student: StudentModel, G: nx.DiGraph,
                     kc_id: str, correct: bool) -> dict:
    state    = student.kc_states[kc_id]
    p_before = state.p_know
    p_after  = bkt_update(state, correct)

    # Integrasi 3: mastery propagation
    propagated = []
    if state.is_mastered:
        propagated = _propagate_mastery(student, G, kc_id)

    entry = {
        "student_id": student.student_id,
        "kc_id":      kc_id,
        "correct":    correct,
        "p_before":   p_before,
        "p_after":    p_after,
        "mastered":   state.is_mastered,
        "propagated": propagated,
    }
    student.history.append(entry)
    return entry


def _propagate_mastery(student: StudentModel, G: nx.DiGraph,
                        mastered_kc_id: str) -> list[str]:
    """
    Integrasi 3: KC A mastered → boost P(L) KC yang langsung bergantung pada A.

    Boost dikaitkan dengan ontologi: semakin besar kontribusi A terhadap
    KC dependent (diukur dari proporsi prasyarat yang terpenuhi),
    semakin besar boost yang diberikan.
    """
    boosted = []
    for dep_id in G.successors(mastered_kc_id):
        dep = student.kc_states[dep_id]
        if dep.is_mastered:
            continue

        prereqs = get_prerequisites(G, dep_id)
        n_total  = len(prereqs)
        n_done   = sum(1 for p in prereqs if student.kc_states[p].is_mastered)

        if n_done < n_total:
            continue  # belum semua prereq selesai

        # Boost proporsional: jika KC A adalah satu-satunya prereq → boost penuh
        # jika KC A adalah salah satu dari banyak prereq → boost lebih kecil
        boost = round(0.05 / max(n_total, 1), 4)
        dep.p_know = round(min(dep.p_know + boost, dep.mastery_threshold - 0.01), 4)
        boosted.append(dep_id)

    return boosted


# ─── Adaptive KC Selection (Integrasi 3 improved) ─────────────────────────────
def select_next_kc(student: StudentModel, G: nx.DiGraph) -> Optional[str]:
    """
    Pilih KC berikutnya menggunakan Expected Learning Gain (ELG).

    ELG = (1 - P(L)) × P(T) × (1 + n_dependents_transitif)

    Mengkombinasikan informasi dari BKT (P(L), P(T)) dengan
    informasi dari ontologi (n_dependents) dalam satu metrik.
    KC dengan ELG tertinggi diprioritaskan.

    Acuan: konsep serupa pada curriculum sequencing (Doroudi et al. 2019).
    """
    mastered  = student.mastered_set()
    available = get_available_kcs(G, mastered)

    if not available:
        return None

    return max(
        available,
        key=lambda kc_id: get_expected_learning_gain(
            G, kc_id,
            student.kc_states[kc_id].p_know,
            student.kc_states[kc_id].p_transit,
        )
    )


# ─── Summary ──────────────────────────────────────────────────────────────────
def get_student_summary(student: StudentModel, G: nx.DiGraph) -> dict:
    mastered  = student.mastered_set()
    per_topic = {}
    for kc_id, state in student.kc_states.items():
        topic = get_kc_info(G, kc_id)["topic"]
        if topic not in per_topic:
            per_topic[topic] = {"mastered": 0, "total": 0}
        per_topic[topic]["total"] += 1
        if state.is_mastered:
            per_topic[topic]["mastered"] += 1
    return {
        "student_id":     student.student_id,
        "total_kc":       G.number_of_nodes(),
        "mastered_kc":    len(mastered),
        "progress_pct":   round(len(mastered) / G.number_of_nodes() * 100, 1),
        "total_attempts": len(student.history),
        "per_topic":      per_topic,
    }


# ─── Smoke Test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from ontology import build_ontology
    import os as _os
    _base = _os.path.dirname(_os.path.abspath(__file__))
    G = build_ontology(_os.path.join(_base, "data", "math_grade1.json"))

    print("=== P(L₀) dan P(T) dari ontologi ===")
    for kc_id in list(G.nodes)[:6]:
        p0 = get_ontology_informed_prior(G, kc_id)
        pt = get_ontology_informed_transit(G, kc_id)
        name = get_kc_info(G, kc_id)["name"]
        print(f"  {kc_id}  P(L0)={p0:.3f}  P(T)={pt:.4f}  {name}")

    student = init_student("test_001", G)
    print("\n=== Simulasi KC-B1 ===")
    for i, correct in enumerate([True, False, True, True, True]):
        r = process_response(student, G, "KC-B1", correct)
        print(f"  {'✓' if correct else '✗'}  {r['p_before']:.4f} → {r['p_after']:.4f}"
              f"{'  MASTERED' if r['mastered'] else ''}"
              f"{'  propagated: '+str(r['propagated']) if r['propagated'] else ''}")

    print(f"\nNext KC (ELG-aware): {select_next_kc(student, G)}")
