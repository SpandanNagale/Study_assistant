"""
Spaced Repetition Store
-----------------------
Persistent flashcard decks, SM-2 review scheduling, and quiz history,
backed by a local SQLite file so progress survives app restarts.

Set STUDY_DB_PATH to change where the database lives (default: data/study.db).
"""

import csv
import io
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta

DB_PATH = os.getenv(
    "STUDY_DB_PATH",
    os.path.join(os.path.dirname(__file__), "..", "data", "study.db"),
)

# Review ratings (Anki-style buttons)
AGAIN, HARD, GOOD, EASY = 0, 1, 2, 3
RATING_LABELS = {AGAIN: "Again", HARD: "Hard", GOOD: "Good", EASY: "Easy"}

_SCHEMA = """
CREATE TABLE IF NOT EXISTS decks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    created_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cards (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    deck_id     INTEGER NOT NULL REFERENCES decks(id) ON DELETE CASCADE,
    front       TEXT NOT NULL,
    back        TEXT NOT NULL,
    ease        REAL NOT NULL DEFAULT 2.5,
    interval    REAL NOT NULL DEFAULT 0,
    reps        INTEGER NOT NULL DEFAULT 0,
    lapses      INTEGER NOT NULL DEFAULT 0,
    due         TEXT NOT NULL,
    created_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reviews (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id     INTEGER NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    rating      INTEGER NOT NULL,
    reviewed_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS quiz_results (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    topic       TEXT NOT NULL,
    score       INTEGER NOT NULL,
    total       INTEGER NOT NULL,
    taken_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cards_due ON cards(due);
"""


def _now():
    return datetime.now().replace(microsecond=0)


@contextmanager
def _connect():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(_SCHEMA)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Scheduling (SM-2 variant)
# ---------------------------------------------------------------------------
def schedule(ease, interval, reps, lapses, rating, now=None):
    """Compute the next review state for a card.

    Returns (ease, interval_days, reps, lapses, due_datetime).
    "Again" resets the card and brings it back in 10 minutes.
    """
    now = now or _now()

    if rating == AGAIN:
        ease = max(1.3, ease - 0.2)
        return ease, 0, 0, lapses + 1, now + timedelta(minutes=10)

    if reps == 0:
        interval = {HARD: 1, GOOD: 1, EASY: 4}[rating]
    elif reps == 1:
        interval = {HARD: 3, GOOD: 6, EASY: 8}[rating]
    else:
        multiplier = {HARD: 1.2, GOOD: ease, EASY: ease * 1.3}[rating]
        interval = max(interval + 1, interval * multiplier)

    ease += {HARD: -0.15, GOOD: 0.0, EASY: 0.15}[rating]
    ease = max(1.3, ease)
    interval = round(interval, 1)
    return ease, interval, reps + 1, lapses, now + timedelta(days=interval)


def describe_interval(card, rating):
    """Human-readable 'next review in' text for a button label."""
    _, interval, *_ = schedule(
        card["ease"], card["interval"], card["reps"], card["lapses"], rating
    )
    if interval == 0:
        return "10m"
    if interval < 30:
        return f"{interval:g}d"
    if interval < 365:
        return f"{interval / 30:.1f}mo"
    return f"{interval / 365:.1f}y"


# ---------------------------------------------------------------------------
# Decks & cards
# ---------------------------------------------------------------------------
def get_or_create_deck(name):
    name = name.strip() or "Untitled deck"
    with _connect() as conn:
        row = conn.execute("SELECT id FROM decks WHERE name = ?", (name,)).fetchone()
        if row:
            return row["id"]
        cur = conn.execute(
            "INSERT INTO decks (name, created_at) VALUES (?, ?)", (name, _now().isoformat())
        )
        return cur.lastrowid


def add_cards(deck_name, cards):
    """Add [{'front','back'}] cards to a deck (created if needed). Skips duplicates.

    Returns the number of cards actually inserted.
    """
    deck_id = get_or_create_deck(deck_name)
    now = _now().isoformat()
    added = 0
    with _connect() as conn:
        existing = {
            r["front"].strip().lower()
            for r in conn.execute("SELECT front FROM cards WHERE deck_id = ?", (deck_id,))
        }
        for card in cards:
            front, back = str(card["front"]).strip(), str(card["back"]).strip()
            if not front or front.lower() in existing:
                continue
            conn.execute(
                "INSERT INTO cards (deck_id, front, back, due, created_at) VALUES (?, ?, ?, ?, ?)",
                (deck_id, front, back, now, now),
            )
            existing.add(front.lower())
            added += 1
    return added


def list_decks():
    """All decks with total and due card counts."""
    now = _now().isoformat()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT d.id, d.name, d.created_at,
                   COUNT(c.id) AS total,
                   SUM(CASE WHEN c.due <= ? THEN 1 ELSE 0 END) AS due,
                   SUM(CASE WHEN c.reps = 0 THEN 1 ELSE 0 END) AS new
            FROM decks d LEFT JOIN cards c ON c.deck_id = d.id
            GROUP BY d.id ORDER BY d.created_at DESC
            """,
            (now,),
        ).fetchall()
    return [dict(r, due=r["due"] or 0, new=r["new"] or 0) for r in rows]


def delete_deck(deck_id):
    with _connect() as conn:
        conn.execute("DELETE FROM decks WHERE id = ?", (deck_id,))


def due_cards(deck_id=None, limit=50):
    """Cards due for review now, oldest due first."""
    sql = (
        "SELECT c.*, d.name AS deck_name FROM cards c JOIN decks d ON d.id = c.deck_id "
        "WHERE c.due <= ?"
    )
    params = [_now().isoformat()]
    if deck_id is not None:
        sql += " AND c.deck_id = ?"
        params.append(deck_id)
    sql += " ORDER BY c.due LIMIT ?"
    params.append(limit)
    with _connect() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def review_card(card_id, rating):
    """Apply a rating to a card and record the review."""
    with _connect() as conn:
        card = conn.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
        if card is None:
            return
        ease, interval, reps, lapses, due = schedule(
            card["ease"], card["interval"], card["reps"], card["lapses"], rating
        )
        conn.execute(
            "UPDATE cards SET ease = ?, interval = ?, reps = ?, lapses = ?, due = ? WHERE id = ?",
            (ease, interval, reps, lapses, due.isoformat(), card_id),
        )
        conn.execute(
            "INSERT INTO reviews (card_id, rating, reviewed_at) VALUES (?, ?, ?)",
            (card_id, rating, _now().isoformat()),
        )


def export_deck_csv(deck_id):
    """Export a deck as front,back CSV (importable into Anki/Quizlet)."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT front, back FROM cards WHERE deck_id = ? ORDER BY id", (deck_id,)
        ).fetchall()
    buf = io.StringIO()
    writer = csv.writer(buf)
    for r in rows:
        writer.writerow([r["front"], r["back"]])
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Quiz history & stats
# ---------------------------------------------------------------------------
def record_quiz(topic, score, total):
    with _connect() as conn:
        conn.execute(
            "INSERT INTO quiz_results (topic, score, total, taken_at) VALUES (?, ?, ?, ?)",
            (topic.strip() or "Untitled quiz", score, total, _now().isoformat()),
        )


def recent_quizzes(limit=10):
    with _connect() as conn:
        return [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM quiz_results ORDER BY taken_at DESC LIMIT ?", (limit,)
            ).fetchall()
        ]


def study_stats():
    """Dashboard numbers: cards, due today, reviews today, day streak."""
    now = _now()
    end_of_today = now.replace(hour=23, minute=59, second=59).isoformat()
    today = now.date().isoformat()
    with _connect() as conn:
        total = conn.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
        due_today = conn.execute(
            "SELECT COUNT(*) FROM cards WHERE due <= ?", (end_of_today,)
        ).fetchone()[0]
        reviewed_today = conn.execute(
            "SELECT COUNT(*) FROM reviews WHERE substr(reviewed_at, 1, 10) = ?", (today,)
        ).fetchone()[0]
        days = {
            r[0]
            for r in conn.execute(
                "SELECT DISTINCT substr(reviewed_at, 1, 10) FROM reviews "
                "UNION SELECT DISTINCT substr(taken_at, 1, 10) FROM quiz_results"
            )
        }

    # Streak counts back from today (or yesterday, so it isn't lost before today's session).
    streak, day = 0, now.date()
    if day.isoformat() not in days:
        day -= timedelta(days=1)
    while day.isoformat() in days:
        streak += 1
        day -= timedelta(days=1)

    return {
        "total_cards": total,
        "due_today": due_today,
        "reviewed_today": reviewed_today,
        "streak": streak,
    }
