"""
mcp_server.py — MCP server exposing 12 memory tools.
Run with: python -m mnemo.mcp_server
"""

import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .storage import init_db, store, delete, list_wings, list_rooms, get_by_id
from .retrieval import search, recall_room, recall_wing, recall_at_time
from .memory_stack import build_context, count_tokens

app = Server("mnemo")
init_db()


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(name="mnemo_store", description="Store a memory verbatim.",
             inputSchema={"type": "object", "required": ["content", "wing", "hall", "room"],
                          "properties": {"content": {"type": "string"}, "wing": {"type": "string"},
                                         "hall": {"type": "string"}, "room": {"type": "string"},
                                         "valid_from": {"type": "string"}, "ended": {"type": "string"}}}),
        Tool(name="mnemo_search", description="Semantic search across memories with optional hierarchy filters.",
             inputSchema={"type": "object", "required": ["query"],
                          "properties": {"query": {"type": "string"}, "wing": {"type": "string"},
                                         "hall": {"type": "string"}, "room": {"type": "string"},
                                         "top_k": {"type": "integer", "default": 5}}}),
        Tool(name="mnemo_recall_room", description="Return all memories in a specific room.",
             inputSchema={"type": "object", "required": ["wing", "hall", "room"],
                          "properties": {"wing": {"type": "string"}, "hall": {"type": "string"},
                                         "room": {"type": "string"}}}),
        Tool(name="mnemo_recall_wing", description="Return recent memories across a wing.",
             inputSchema={"type": "object", "required": ["wing"],
                          "properties": {"wing": {"type": "string"}, "limit": {"type": "integer", "default": 20}}}),
        Tool(name="mnemo_recall_at_time", description="Return memories valid at a specific point in time.",
             inputSchema={"type": "object", "required": ["wing", "at_time"],
                          "properties": {"wing": {"type": "string"}, "at_time": {"type": "string"}}}),
        Tool(name="mnemo_build_context", description="Build the full memory context to inject at session start.",
             inputSchema={"type": "object", "required": ["wing"],
                          "properties": {"wing": {"type": "string"}, "query": {"type": "string"},
                                         "room": {"type": "string"}}}),
        Tool(name="mnemo_list_wings", description="List all wings (people/projects).",
             inputSchema={"type": "object", "properties": {}}),
        Tool(name="mnemo_list_rooms", description="List all rooms within a wing and hall.",
             inputSchema={"type": "object", "required": ["wing", "hall"],
                          "properties": {"wing": {"type": "string"}, "hall": {"type": "string"}}}),
        Tool(name="mnemo_get", description="Get a specific memory by ID.",
             inputSchema={"type": "object", "required": ["memory_id"],
                          "properties": {"memory_id": {"type": "string"}}}),
        Tool(name="mnemo_delete", description="Delete a memory by ID.",
             inputSchema={"type": "object", "required": ["memory_id"],
                          "properties": {"memory_id": {"type": "string"}}}),
        Tool(name="mnemo_count_tokens", description="Estimate token count of a text string.",
             inputSchema={"type": "object", "required": ["text"],
                          "properties": {"text": {"type": "string"}}}),
        Tool(name="mnemo_summarize_wing", description="Return a summary of all rooms and memory counts in a wing.",
             inputSchema={"type": "object", "required": ["wing"],
                          "properties": {"wing": {"type": "string"}}}),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "mnemo_store":
        memory_id = store(
            content=arguments["content"],
            wing=arguments["wing"],
            hall=arguments["hall"],
            room=arguments["room"],
            valid_from=arguments.get("valid_from"),
            ended=arguments.get("ended"),
        )
        return [TextContent(type="text", text=f"Stored. ID: {memory_id}")]

    elif name == "mnemo_search":
        results = search(
            query=arguments["query"],
            wing=arguments.get("wing"),
            hall=arguments.get("hall"),
            room=arguments.get("room"),
            top_k=arguments.get("top_k", 5),
        )
        return [TextContent(type="text", text=json.dumps(results, indent=2))]

    elif name == "mnemo_recall_room":
        results = recall_room(arguments["wing"], arguments["hall"], arguments["room"])
        return [TextContent(type="text", text=json.dumps(results, indent=2))]

    elif name == "mnemo_recall_wing":
        results = recall_wing(arguments["wing"], arguments.get("limit", 20))
        return [TextContent(type="text", text=json.dumps(results, indent=2))]

    elif name == "mnemo_recall_at_time":
        results = recall_at_time(arguments["wing"], arguments["at_time"])
        return [TextContent(type="text", text=json.dumps(results, indent=2))]

    elif name == "mnemo_build_context":
        context = build_context(
            wing=arguments["wing"],
            query=arguments.get("query"),
            room=arguments.get("room"),
        )
        tokens = count_tokens(context)
        return [TextContent(type="text", text=f"[{tokens} tokens]\n\n{context}")]

    elif name == "mnemo_list_wings":
        wings = list_wings()
        return [TextContent(type="text", text=json.dumps(wings))]

    elif name == "mnemo_list_rooms":
        rooms = list_rooms(arguments["wing"], arguments["hall"])
        return [TextContent(type="text", text=json.dumps(rooms))]

    elif name == "mnemo_get":
        memory = get_by_id(arguments["memory_id"])
        return [TextContent(type="text", text=json.dumps(memory, indent=2))]

    elif name == "mnemo_delete":
        delete(arguments["memory_id"])
        return [TextContent(type="text", text="Deleted.")]

    elif name == "mnemo_count_tokens":
        tokens = count_tokens(arguments["text"])
        return [TextContent(type="text", text=str(tokens))]

    elif name == "mnemo_summarize_wing":
        from .storage import _get_db
        conn = _get_db()
        rows = conn.execute(
            "SELECT hall, room, COUNT(*) as count FROM nodes WHERE wing=? GROUP BY hall, room ORDER BY hall, room",
            (arguments["wing"],)
        ).fetchall()
        conn.close()
        summary = {f"{r['hall']}/{r['room']}": r["count"] for r in rows}
        return [TextContent(type="text", text=json.dumps(summary, indent=2))]

    return [TextContent(type="text", text="Unknown tool")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
