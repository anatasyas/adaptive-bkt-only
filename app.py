"""
BKT Only - Tanpa Ontologi
Versi untuk perbandingan dengan BKT+Ontologi
"""

from flask import Flask, request, jsonify, send_from_directory
import random, os

app = Flask(__name__, static_folder="static", template_folder="static")

# Import
from database import (
    init_db, create_student, get_student, get_random_question,
    upsert_kc_state, get_all_kc_states, seed_ontology
)
from seed_questions import seed

def init_bkt_only():
    init_db()
    seed_ontology()   # Pastikan KC & questions terisi
    seed()            # Seed soal
    print("✅ BKT-Only initialized successfully")

init_bkt_only()

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.post("/api/register")
def register():
    try:
        data = request.json or {}
        name = data.get("name", "Siswa").strip() or "Siswa"
        avatar = int(data.get("avatar", 1))
        sid = f"S{random.randint(10000,99999)}"

        create_student(sid, name, avatar)

        # Inisialisasi KC state default
        with get_conn() as conn:   # pastikan import get_conn
            kcs = conn.execute("SELECT id FROM knowledge_components").fetchall()
            for kc in kcs:
                upsert_kc_state(sid, kc[0], 0.3, 0, 0, False)

        return jsonify({"student_id": sid, "name": name})
    except Exception as e:
        print("Register Error:", e)
        return jsonify({"error": str(e)}), 500

@app.get("/api/topics/<sid>")
def get_topics(sid):
    """BKT Only: Semua topik terbuka"""
    return jsonify([
        {"id": "bilangan", "label": "Bilangan", "n_mastered": 0, "n_total": 10, "locked": False, "completed": False},
        {"id": "operasi", "label": "Operasi Bilangan", "n_mastered": 0, "n_total": 8, "locked": False, "completed": False},
    ])

@app.get("/api/next-question/<sid>")
def next_question(sid):
    try:
        q = get_random_question(None)  # Ambil dari semua KC
        if not q:
            q = {
                "id": 999,
                "kc_id": "KC-B01",
                "type": "pilgan",
                "q": "Berapa hasil 2 + 3?",
                "options": ["4", "5", "6", "7"],
                "answer": "5"
            }
        return jsonify(q)
    except Exception as e:
        import traceback
        print("Next Question Error:", str(e))
        print(traceback.format_exc())
        return jsonify({"error": "Gagal memuat soal"}), 500

@app.post("/api/answer/<sid>")
def answer(sid):
    data = request.json
    kc_id = data.get("kc_id")
    correct = bool(data.get("correct", False))

    # Update state (sederhana)
    upsert_kc_state(sid, kc_id, 0.6 if correct else 0.4, 
                   1 if correct else 0, 0 if correct else 1, False)

    return jsonify({
        "correct": correct,
        "message": "Benar!" if correct else "Salah"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
