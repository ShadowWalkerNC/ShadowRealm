"""
recipe_server.py

MCP server exposing RecipeOS tools to the ShadowRealm agent.
Talks to the RecipeOS Supabase backend (Android/Kotlin app).
Allows the agent to query, create, and manage recipes, categories,
and cooking steps.

Requires environment variables:
    RECIPEOS_SUPABASE_URL   — Supabase project URL
    RECIPEOS_SUPABASE_KEY   — Supabase anon/service key
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

server = Server("recipe")

_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    url = os.environ.get("RECIPEOS_SUPABASE_URL", "").strip()
    key = os.environ.get("RECIPEOS_SUPABASE_KEY", "").strip()
    if not url or not key:
        raise RuntimeError(
            "RecipeOS Supabase credentials not configured. "
            "Set RECIPEOS_SUPABASE_URL and RECIPEOS_SUPABASE_KEY in .env"
        )
    try:
        from supabase import create_client
        _client = create_client(url, key)
    except ImportError:
        raise RuntimeError("supabase-py not installed. Run: pip install supabase")
    return _client


def _text(text: str) -> list[TextContent]:
    return [TextContent(type="text", text=text)]


def _json(data: Any) -> list[TextContent]:
    return _text(json.dumps(data, indent=2, default=str))


def _safe_run(fn):
    try:
        result = fn()
        return result.data, None
    except Exception as exc:
        return None, str(exc)


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="recipe_list",
            description=(
                "List, search, or get details of recipes from RecipeOS (Android app). "
                "action=list returns all recipes; action=search finds by keyword; "
                "action=get fetches one recipe with full steps and ingredients by ID."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["list", "search", "get"],
                    },
                    "id": {"type": "string", "description": "Recipe UUID (get)"},
                    "query": {"type": "string", "description": "Search keyword (search)"},
                    "category": {"type": "string", "description": "Filter by category (list)"},
                    "limit": {"type": "integer", "description": "Max results (default 20)"},
                },
                "required": ["action"],
            },
        ),
        Tool(
            name="recipe_create",
            description=(
                "Create a new recipe in RecipeOS with name, description, category, "
                "prep/cook times, servings, and optional steps."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Recipe name (required)"},
                    "description": {"type": "string"},
                    "category": {"type": "string"},
                    "prep_time_minutes": {"type": "integer"},
                    "cook_time_minutes": {"type": "integer"},
                    "servings": {"type": "integer"},
                    "steps": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of cooking step instructions",
                    },
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="recipe_categories",
            description="List all recipe categories available in RecipeOS.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="recipe_stats",
            description=(
                "Get RecipeOS statistics: total recipes, breakdown by category, "
                "and recently added recipes."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        client = _get_client()
    except RuntimeError as exc:
        return _text(f"Error: {exc}")

    if name == "recipe_list":
        action = arguments.get("action", "")
        limit = int(arguments.get("limit", 20))

        if action == "list":
            category = arguments.get("category", "")
            q = client.table("recipes").select("*").limit(limit)
            if category:
                q = q.eq("category", category)
            data, err = _safe_run(lambda: q.execute())
            if err:
                return _text(f"Error listing recipes: {err}")
            return _json({"count": len(data), "recipes": data})

        elif action == "search":
            keyword = arguments.get("query", "")
            if not keyword:
                return _text("Error: query required for search")
            data, err = _safe_run(
                lambda: client.table("recipes").select("*").ilike("name", f"%{keyword}%").limit(limit).execute()
            )
            if err:
                return _text(f"Error searching recipes: {err}")
            return _json({"count": len(data), "recipes": data})

        elif action == "get":
            recipe_id = arguments.get("id", "")
            if not recipe_id:
                return _text("Error: id required for get")
            data, err = _safe_run(
                lambda: client.table("recipes").select("*, recipe_steps(*), recipe_ingredients(*, ingredients(*))").eq("id", recipe_id).single().execute()
            )
            if err:
                return _text(f"Error fetching recipe: {err}")
            return _json(data)

        else:
            return _text(f"Unknown action '{action}' for recipe_list")

    elif name == "recipe_create":
        recipe_name = arguments.get("name", "").strip()
        if not recipe_name:
            return _text("Error: name is required")
        payload = {
            k: v for k, v in {
                "name": recipe_name,
                "description": arguments.get("description", ""),
                "category": arguments.get("category", ""),
                "prep_time_minutes": arguments.get("prep_time_minutes"),
                "cook_time_minutes": arguments.get("cook_time_minutes"),
                "servings": arguments.get("servings"),
            }.items() if v is not None and v != ""
        }
        data, err = _safe_run(lambda: client.table("recipes").insert(payload).execute())
        if err:
            return _text(f"Error creating recipe: {err}")
        recipe_id = data[0]["id"] if data else None
        steps = arguments.get("steps", [])
        if recipe_id and steps:
            step_rows = [{"recipe_id": recipe_id, "step_number": i + 1, "instruction": s} for i, s in enumerate(steps)]
            _safe_run(lambda: client.table("recipe_steps").insert(step_rows).execute())
        return _text(f"Recipe '{recipe_name}' created (id: {recipe_id})" + (f" with {len(steps)} steps" if steps else ""))

    elif name == "recipe_categories":
        data, err = _safe_run(lambda: client.table("categories").select("*").order("name").execute())
        if err:
            return _text(f"Error fetching categories: {err}")
        return _json({"count": len(data), "categories": data})

    elif name == "recipe_stats":
        recipe_data, _ = _safe_run(lambda: client.table("recipes").select("id, category").execute())
        recent_data, _ = _safe_run(
            lambda: client.table("recipes").select("name, created_at").order("created_at", desc=True).limit(5).execute()
        )
        stats = {"total_recipes": len(recipe_data) if recipe_data else 0}
        if recipe_data:
            cat_counts = {}
            for r in recipe_data:
                cat = r.get("category") or "Uncategorized"
                cat_counts[cat] = cat_counts.get(cat, 0) + 1
            stats["by_category"] = dict(sorted(cat_counts.items(), key=lambda x: -x[1]))
        stats["recent_recipes"] = [{"name": r["name"], "created_at": r["created_at"]} for r in (recent_data or [])]
        return _json(stats)

    else:
        return _text(f"Unknown tool: {name}")


async def run():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(run())
