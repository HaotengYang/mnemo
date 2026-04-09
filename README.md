# Mnemo

Persistent long-term memory for LLM agents. Gives Claude, Cursor, and ChatGPT cross-session memory using hierarchical storage over ChromaDB and SQLite — no cloud, no summarization loss, zero inference cost per recall.

## The problem

Every new conversation starts from zero. Six months of decisions, preferences, and context — gone. Existing solutions let the LLM summarize what to remember, which loses information. Mnemo stores everything verbatim and retrieves it with structure.

## How it works

Memories are organized in a three-level hierarchy:

```
Wing (person or project)
└── Hall (memory type: facts, preferences, decisions, events)
    └── Room (specific topic: auth, architecture, onboarding...)
```

Search narrows by structure before running vector similarity — this is why recall improves significantly over flat semantic search.

**4-layer memory stack:**

| Layer | Content | When loaded |
|-------|---------|-------------|
| L0 | Identity facts | Always (~50 tokens) |
| L1 | Critical facts | Always (~120 tokens) |
| L2 | Room memories | On topic detection |
| L3 | Deep search | On explicit query |

Total always-on overhead: under 200 tokens per session.

## Quickstart

```bash
git clone https://github.com/HaotengYang/mnemo
cd mnemo
python -m venv venv && source venv/bin/activate
pip install -e .
```

Store a memory:

```python
import mnemo
mnemo.init_db()

mnemo.store(
    content="Prefer async endpoints over sync for all new routes",
    wing="myproject",
    hall="decisions",
    room="architecture"
)
```

Search:

```python
results = mnemo.search("API design preference", wing="myproject")
print(results[0]["content"])
```

Build session context (inject at conversation start):

```python
context = mnemo.build_context(wing="myproject", query="architecture")
print(context)  # under 200 tokens for L0+L1, more on demand
```

## MCP Server

Mnemo exposes 12 tools via MCP, enabling zero-config integration with Claude Code and Cursor.

Add to your Claude Code config (`~/.claude/claude.json`):

```json
{
  "mcpServers": {
    "mnemo": {
      "command": "/path/to/mnemo/venv/bin/python",
      "args": ["-m", "mnemo.mcp_server"]
    }
  }
}
```

Available tools: `mnemo_store`, `mnemo_search`, `mnemo_recall_room`, `mnemo_recall_wing`, `mnemo_recall_at_time`, `mnemo_build_context`, `mnemo_list_wings`, `mnemo_list_rooms`, `mnemo_get`, `mnemo_delete`, `mnemo_count_tokens`, `mnemo_summarize_wing`

## Storage

All data stored locally at `~/.mnemo/`:
- `mnemo.db` — SQLite database with hierarchy metadata and temporal entity graph
- `chroma/` — ChromaDB vector embeddings

No API calls required for retrieval.

## Tech stack

- Python 3.9+
- ChromaDB — vector embeddings and semantic search
- SQLite — structured hierarchy and temporal queries
- MCP — integration protocol for Claude Code and Cursor
