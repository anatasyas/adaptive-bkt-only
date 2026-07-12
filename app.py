"""
BKT Only - Tanpa Ontologi
Untuk perbandingan dengan versi BKT + Ontologi
"""

from flask import Flask, request, jsonify, send_from_directory
import random, os

app = Flask(__name__, static_folder="static", template_folder="static")

# Import tanpa ontologi
from bkt_engine import StudentModel, process_response, select_next_kc, DEFAULT_BKT_PARAMS
from database import (
    init_db, create_student, get_student, add_stars,
    get_random_question, upsert_kc_state, get_all_kc_states
)

# Load semua KC dari database (tanpa ontologi)
KC_IDS = []

def init_bkt_only():
    global KC_IDS
    init_db()
    from database import get_conn
    with get_conn() as conn:
        rows = conn.execute("SELECT id FROM knowledge_components").fetchall()
        KC_IDS = [r[0] for r in rows]
    print(f"✅ BKT-Only initialized with {len(KC_IDS)} KC")

init_bkt_only()

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.post("/api/register")
def register():
    data = request.json
    name = data.get("name", "Siswa").strip() or "Siswa"
    avatar = int(data.get("avatar", 1))
    sid = f"S{random.randint(10000,99999)}"

    create_student(sid, name, avatar)

    # Inisialisasi dengan p_know default
    for kc_id in KC_IDS:
        upsert_kc_state(sid, kc_id, 0.3, 0, 0, False)

    return jsonify({"student_id": sid, "name": name})

@app.get("/api/next-question/<sid>")
def next_question(sid):
    # Rebuild student model
    student = StudentModel(sid)
    db_states = get_all_kc_states(sid)
    # ... (rebuild logic)
    next_kc = random.choice(KC_IDS)  # atau pakai select_next_kc tanpa ontologi
    q = get_random_question(next_kc)
    if not q:
        q = {"q": "Soal tidak tersedia", "options": ["A","B","C","D"], "answer": "A"}
    return jsonify(q)

@app.post("/api/answer/<sid>")
def answer(sid):
    data = request.json
    kc_id = data["kc_id"]
    correct = bool(data["correct"])

    student = StudentModel(sid)
    result = process_response(student, None, kc_id, correct)  # None = tanpa G
    # sync to db
    return jsonify({
        "correct": correct,
        "p_know": round(result.get("p_after", 0), 3)
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
