"""
storage.py — ChromaDB + SQLite layer
Handles verbatim storage organized as Wing → Hall → Room hierarchy.
"""

import sqlite3
import chromadb
import uuid
from datetime import datetime
from pathlib import Path


DB_PATH = Path.home() / ".mnemo" / "mnemo.db"
CHROMA_PATH = Path.home() / ".mnemo" / "chroma"


def _get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _get_chroma():
    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(CHROMA_PATH))


def init_db():
    conn = _get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS nodes (
            id TEXT PRIMARY KEY,
            wing TEXT NOT NULL,
            hall TEXT NOT NULL,
            room TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            valid_from TEXT,
            ended TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_wing ON nodes(wing);
        CREATE INDEX IF NOT EXISTS idx_wing_hall ON nodes(wing, hall);
        CREATE INDEX IF NOT EXISTS idx_wing_hall_room ON nodes(wing, hall, room);
    """)
    conn.commit()
    conn.close()


def store(content: str, wing: str, hall: str, room: str,
          valid_from: str = None, ended: str = None) -> str:
    """Store a memory verbatim. Returns the memory ID."""
    memory_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    # SQLite: structured metadata
    conn = _get_db()
    conn.execute(
        "INSERT INTO nodes VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (memory_id, wing, hall, room, content, now, valid_from, ended)
    )
    conn.commit()
    conn.close()

    # ChromaDB: vector embedding
    client = _get_chroma()
    collection = client.get_or_create_collection("mnemo")
    collection.add(
        documents=[content],
        metadatas=[{"wing": wing, "hall": hall, "room": room, "created_at": now}],
        ids=[memory_id]
    )

    return memory_id


def delete(memory_id: str):
    conn = _get_db()
    conn.execute("DELETE FROM nodes WHERE id = ?", (memory_id,))
    conn.commit()
    conn.close()

    client = _get_chroma()
    collection = client.get_or_create_collection("mnemo")
    collection.delete(ids=[memory_id])


def list_wings() -> list[str]:
    conn = _get_db()
    rows = conn.execute("SELECT DISTINCT wing FROM nodes ORDER BY wing").fetchall()
    conn.close()
    return [r["wing"] for r in rows]


def list_rooms(wing: str, hall: str) -> list[str]:
    conn = _get_db()
    rows = conn.execute(
        "SELECT DISTINCT room FROM nodes WHERE wing=? AND hall=? ORDER BY room",
        (wing, hall)
    ).fetchall()
    conn.close()
    return [r["room"] for r in rows]


def get_by_id(memory_id: str) -> dict | None:
    conn = _get_db()
    row = conn.execute("SELECT * FROM nodes WHERE id=?", (memory_id,)).fetchone()
    conn.close()
    return dict(row) if row else None
