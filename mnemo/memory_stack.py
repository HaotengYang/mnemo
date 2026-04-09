"""
memory_stack.py — 4-layer memory stack.

L0 (~50 tokens):  Identity — who the user is, always loaded
L1 (~120 tokens): Critical facts — always loaded
L2 (on-demand):   Room recall — loaded when topic is detected
L3 (on-demand):   Deep search — explicit semantic query

Total always-on overhead: ~170 tokens regardless of memory size.
"""

import sqlite3
from .storage import _get_db
from .retrieval import search, recall_room


# Hall names — standardized memory types
HALL_FACTS = "facts"
HALL_PREFERENCES = "preferences"
HALL_DECISIONS = "decisions"
HALL_EVENTS = "events"


def load_l0(wing: str) -> str:
    """L0: Identity layer — core facts about this wing (person/project)."""
    conn = _get_db()
    rows = conn.execute(
        "SELECT content FROM nodes WHERE wing=? AND hall=? AND room='identity' ORDER BY created_at DESC LIMIT 3",
        (wing, HALL_FACTS)
    ).fetchall()
    conn.close()
    if not rows:
        return ""
    return "[Identity]\n" + "\n".join(r["content"] for r in rows)


def load_l1(wing: str) -> str:
    """L1: Critical facts — always-loaded layer, ~120 tokens."""
    conn = _get_db()
    rows = conn.execute(
        "SELECT content FROM nodes WHERE wing=? AND hall=? ORDER BY created_at DESC LIMIT 5",
        (wing, HALL_FACTS)
    ).fetchall()
    conn.close()
    if not rows:
        return ""
    return "[Critical Facts]\n" + "\n".join(r["content"] for r in rows)


def load_l2(wing: str, room: str) -> str:
    """L2: Room recall — loaded when a topic is detected in conversation."""
    memories = recall_room(wing, HALL_DECISIONS, room)
    if not memories:
        return ""
    return f"[Room: {room}]\n" + "\n".join(m["content"] for m in memories[:5])


def load_l3(wing: str, query: str) -> str:
    """L3: Deep semantic search — explicit on-demand query."""
    memories = search(query, wing=wing, top_k=5)
    if not memories:
        return ""
    return f"[Search: {query}]\n" + "\n".join(m["content"] for m in memories)


def build_context(wing: str, query: str = None, room: str = None) -> str:
    """
    Assemble the memory context to inject at session start.
    Always loads L0 + L1. Adds L2/L3 on demand.
    """
    parts = []

    l0 = load_l0(wing)
    if l0:
        parts.append(l0)

    l1 = load_l1(wing)
    if l1:
        parts.append(l1)

    if room:
        l2 = load_l2(wing, room)
        if l2:
            parts.append(l2)

    if query:
        l3 = load_l3(wing, query)
        if l3:
            parts.append(l3)

    return "\n\n".join(parts)


def count_tokens(text: str) -> int:
    """Rough token estimate: 1 token ≈ 4 characters."""
    return len(text) // 4
