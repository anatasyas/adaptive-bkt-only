"""
database.py — SQLite schema dan CRUD
Tabel: students, kc_states, interactions, questions
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager

import os as _os
_BASE = _os.path.dirname(_os.path.abspath(__file__))
DB_PATH = _os.path.join(_BASE, "data", "adaptive_learning.db")

@contextmanager


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def seed_ontology(json_path: str = None):
    """Seed tabel knowledge_components dan prerequisites dari JSON atau data default."""
    import json as _json, os as _os

    # Cek apakah sudah ada data
    with get_conn() as conn:
        n = conn.execute("SELECT COUNT(*) FROM knowledge_components").fetchone()[0]
    if n > 0:
        return  # sudah terisi

    # Load dari JSON jika ada
    if json_path is None:
        json_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                                   "data", "math_grade1.json")

    if not _os.path.exists(json_path):
        print(f"[seed_ontology] File tidak ditemukan: {json_path}")
        return

    with open(json_path, encoding="utf-8") as f:
        data = _json.load(f)

    with get_conn() as conn:
        for kc in data["knowledge_components"]:
            conn.execute(
                "INSERT OR IGNORE INTO knowledge_components "
                "(id, name, topic, difficulty, cp_ref, nctm_ref) VALUES (?,?,?,?,?,?)",
                (kc["id"], kc["name"], kc["topic"], kc.get("difficulty", 1),
                 kc.get("cp_ref", ""), kc.get("nctm_ref", ""))
            )
        for rel in data["prerequisites"]:
            conn.execute(
                "INSERT OR IGNORE INTO prerequisites (kc_from, kc_to) VALUES (?,?)",
                (rel[0], rel[1])
            )

    with get_conn() as conn:
        n_kc  = conn.execute("SELECT COUNT(*) FROM knowledge_components").fetchone()[0]
        n_rel = conn.execute("SELECT COUNT(*) FROM prerequisites").fetchone()[0]
    print(f"[seed_ontology] {n_kc} KC, {n_rel} relasi prasyarat ditambahkan ke DB.")


def init_db():
    Path(DB_PATH).parent.mkdir(exist_ok=True)
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS students (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            subject     TEXT NOT NULL DEFAULT 'matematika',
            grade       INTEGER NOT NULL DEFAULT 1,
            avatar      INTEGER NOT NULL DEFAULT 1,
            total_stars INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS kc_states (
            student_id  TEXT NOT NULL,
            kc_id       TEXT NOT NULL,
            p_know      REAL NOT NULL,
            n_correct   INTEGER NOT NULL DEFAULT 0,
            n_incorrect INTEGER NOT NULL DEFAULT 0,
            is_mastered INTEGER NOT NULL DEFAULT 0,
            updated_at  TEXT NOT NULL,
            PRIMARY KEY (student_id, kc_id),
            FOREIGN KEY (student_id) REFERENCES students(id)
        );

        CREATE TABLE IF NOT EXISTS interactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id  TEXT NOT NULL,
            kc_id       TEXT NOT NULL,
            correct     INTEGER NOT NULL,
            p_before    REAL NOT NULL,
            p_after     REAL NOT NULL,
            timestamp   TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students(id)
        );

        CREATE TABLE IF NOT EXISTS knowledge_components (
            id         TEXT PRIMARY KEY,
            name       TEXT NOT NULL,
            topic      TEXT NOT NULL,
            difficulty INTEGER NOT NULL DEFAULT 1,
            cp_ref     TEXT DEFAULT '',
            nctm_ref   TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS prerequisites (
            kc_from TEXT NOT NULL,
            kc_to   TEXT NOT NULL,
            PRIMARY KEY (kc_from, kc_to),
            FOREIGN KEY (kc_from) REFERENCES knowledge_components(id),
            FOREIGN KEY (kc_to)   REFERENCES knowledge_components(id)
        );

        CREATE TABLE IF NOT EXISTS questions (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            kc_id         TEXT NOT NULL,
            question_type TEXT NOT NULL DEFAULT 'pilgan',
            question      TEXT NOT NULL,
            opt_a         TEXT NOT NULL DEFAULT '',
            opt_b         TEXT NOT NULL DEFAULT '',
            opt_c         TEXT NOT NULL DEFAULT '',
            opt_d         TEXT NOT NULL DEFAULT '',
            answer        TEXT NOT NULL,
            difficulty    INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (kc_id) REFERENCES knowledge_components(id)
        );
        """)


# ── Students ──────────────────────────────────────────────────────────────────
def create_student(student_id, name, avatar=1):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO students (id,name,avatar,created_at) VALUES (?,?,?,?)",
            (student_id, name, avatar, datetime.now().isoformat())
        )
    return get_student(student_id)

def get_student(student_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()
    return dict(row) if row else None

def add_stars(student_id, stars):
    with get_conn() as conn:
        conn.execute("UPDATE students SET total_stars=total_stars+? WHERE id=?", (stars, student_id))


# ── KC States ─────────────────────────────────────────────────────────────────
def upsert_kc_state(student_id, kc_id, p_know, n_correct, n_incorrect, is_mastered):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO kc_states (student_id,kc_id,p_know,n_correct,n_incorrect,is_mastered,updated_at)
            VALUES (?,?,?,?,?,?,?)
            ON CONFLICT(student_id,kc_id) DO UPDATE SET
                p_know=excluded.p_know, n_correct=excluded.n_correct,
                n_incorrect=excluded.n_incorrect, is_mastered=excluded.is_mastered,
                updated_at=excluded.updated_at
        """, (student_id, kc_id, p_know, n_correct, n_incorrect,
              int(is_mastered), datetime.now().isoformat()))

def get_kc_state(student_id, kc_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM kc_states WHERE student_id=? AND kc_id=?",
                           (student_id, kc_id)).fetchone()
    return dict(row) if row else None

def get_all_kc_states(student_id):
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM kc_states WHERE student_id=?", (student_id,)).fetchall()
    return {r["kc_id"]: dict(r) for r in rows}

def get_mastered_kcs(student_id):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT kc_id FROM kc_states WHERE student_id=? AND is_mastered=1", (student_id,)
        ).fetchall()
    return {r["kc_id"] for r in rows}


# ── Interactions ──────────────────────────────────────────────────────────────
def log_interaction(student_id, kc_id, correct, p_before, p_after):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO interactions (student_id,kc_id,correct,p_before,p_after,timestamp) VALUES (?,?,?,?,?,?)",
            (student_id, kc_id, int(correct), p_before, p_after, datetime.now().isoformat())
        )

def get_interaction_count(student_id):
    with get_conn() as conn:
        r = conn.execute("SELECT COUNT(*) as n FROM interactions WHERE student_id=?", (student_id,)).fetchone()
    return r["n"]


# ── Questions ─────────────────────────────────────────────────────────────────
def insert_question(kc_id, question, opt_a, opt_b, opt_c, opt_d, answer,
                    difficulty=1, question_type='pilgan'):
    """
    question_type:
      'pilgan'     — 4 pilihan (a/b/c/d)
      'benar_salah'— 2 opsi: opt_a=teks pertanyaan, answer='benar'/'salah'
      'isian'      — jawab dengan mengetik angka, answer = angka benar (string)
    """
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO questions (kc_id,question_type,question,opt_a,opt_b,opt_c,opt_d,answer,difficulty) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (kc_id, question_type, question, opt_a, opt_b, opt_c, opt_d, str(answer).lower(), difficulty)
        )

def get_random_question(kc_id):
    """Ambil satu soal acak. Return dict siap pakai frontend."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM questions WHERE kc_id=? ORDER BY RANDOM() LIMIT 1", (kc_id,)
        ).fetchone()
    if not row:
        return None
    r = dict(row)
    qtype = r.get("question_type", "pilgan")

    base = {"id": r["id"], "kc_id": r["kc_id"], "type": qtype, "q": r["question"]}

    if qtype == "pilgan":
        opts = {"a": r["opt_a"], "b": r["opt_b"], "c": r["opt_c"], "d": r["opt_d"]}
        return {**base,
                "options": [r["opt_a"], r["opt_b"], r["opt_c"], r["opt_d"]],
                "answer":  opts[r["answer"]]}

    elif qtype == "isian":
        return {**base, "options": [], "answer": r["answer"]}

    elif qtype == "hitung":
        # opt_a=emoji, opt_b=jumlah
        return {**base, "emoji": r["opt_a"], "count": int(r["opt_b"]),
                "options": [], "answer": r["answer"]}

    elif qtype == "visual_pilgan":
        # opt_a=emoji, opt_b=jumlah, opt_c/d=opsi salah
        correct = str(r["answer"])
        wrongs  = [r["opt_c"], r["opt_d"]]
        opts    = list(dict.fromkeys([correct] + wrongs))[:4]
        import random; random.shuffle(opts)
        return {**base, "emoji": r["opt_a"], "count": int(r["opt_b"]),
                "options": opts, "answer": correct}

    elif qtype == "jodohkan":
        # opt_a=emoji, opt_b=jumlah benar, opt_c/d=angka salah
        correct = str(r["opt_b"])
        import random
        wrongs  = [r["opt_c"], r["opt_d"], str(int(r["opt_b"])+3)]
        opts    = list(dict.fromkeys([correct] + wrongs))[:4]
        random.shuffle(opts)
        return {**base, "emoji": r["opt_a"], "count": int(r["opt_b"]),
                "options": opts, "answer": correct}

    elif qtype == "hitung_warna":
        # opt_a=string emoji campur, opt_b=emoji target yang dihitung
        return {**base, "emoji_box": r["opt_a"], "target": r["opt_b"],
                "options": [], "answer": r["answer"]}

    elif qtype == "visual_tambah":
        # opt_a=emoji1, opt_b=jml1, opt_c=emoji2, opt_d=jml2, answer=total
        return {**base,
                "emoji1": r["opt_a"], "count1": int(r["opt_b"]),
                "emoji2": r["opt_c"], "count2": int(r["opt_d"]),
                "options": [], "answer": r["answer"]}

    return None
    r = dict(row)
    qtype = r.get("question_type", "pilgan")

    if qtype == "pilgan":
        opts = {"a": r["opt_a"], "b": r["opt_b"], "c": r["opt_c"], "d": r["opt_d"]}
        return {"id":r["id"],"kc_id":r["kc_id"],"type":"pilgan","q":r["question"],
                "options":[r["opt_a"],r["opt_b"],r["opt_c"],r["opt_d"]],"answer":opts[r["answer"]]}

    elif qtype == "isian":
        return {"id":r["id"],"kc_id":r["kc_id"],"type":"isian","q":r["question"],
                "options":[],"answer":r["answer"]}

    elif qtype == "hitung":
        return {"id":r["id"],"kc_id":r["kc_id"],"type":"hitung","q":r["question"],
                "emoji":r["opt_a"],"count":int(r["opt_b"]),"options":[],"answer":r["answer"]}

    elif qtype == "visual_pilgan":
        opts = [r["opt_c"], r["opt_d"], str(int(r["opt_b"])), str(int(r["opt_b"])+2)]
        random.shuffle(opts)
        return {"id":r["id"],"kc_id":r["kc_id"],"type":"visual_pilgan","q":r["question"],
                "emoji":r["opt_a"],"count":int(r["opt_b"]),"options":opts,"answer":r["answer"]}

    elif qtype == "jodohkan":
        correct = str(r["opt_b"])
        opts = list({correct, r["opt_c"], r["opt_d"], str(int(r["opt_b"])+3)})
        while len(opts) < 4: opts.append(str(int(correct)+len(opts)))
        random.shuffle(opts)
        return {"id":r["id"],"kc_id":r["kc_id"],"type":"jodohkan","q":r["question"],
                "emoji":r["opt_a"],"count":int(r["opt_b"]),"options":opts[:4],"answer":correct}

    elif qtype == "hitung_warna":
        return {"id":r["id"],"kc_id":r["kc_id"],"type":"hitung_warna","q":r["question"],
                "emojis":r["opt_a"],"target":r["opt_b"],"options":[],"answer":r["answer"]}

    elif qtype == "visual_tambah":
        return {"id":r["id"],"kc_id":r["kc_id"],"type":"visual_tambah","q":r["question"],
                "emoji1":r["opt_a"],"count1":int(r["opt_b"]),
                "emoji2":r["opt_c"],"count2":int(r["opt_d"]),"options":[],"answer":r["answer"]}

    return None

def count_questions(kc_id=None):
    with get_conn() as conn:
        if kc_id:
            r = conn.execute("SELECT COUNT(*) FROM questions WHERE kc_id=?", (kc_id,)).fetchone()
        else:
            r = conn.execute("SELECT COUNT(*) FROM questions").fetchone()
    return r[0]

def questions_seeded():
    return count_questions() > 0


if __name__ == "__main__":
    init_db()
    seed_ontology()
    print("DB ready:", DB_PATH)
