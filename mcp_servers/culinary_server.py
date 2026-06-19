"""
culinary_server.py

MCP server exposing CulinaryOS tools to the ShadowRealm agent.
Allows the agent to query, create, update, and manage recipes, ingredients,
menus, and kitchen operations via the CulinaryOS Supabase backend.

Requires environment variables:
    CULINARY_SUPABASE_URL      — Supabase project URL
    CULINARY_SUPABASE_KEY      — Supabase anon/service key
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

server = Server("culinary")

# ── Lazy Supabase client ─────────────────────────────────────────────────────

_client = None


def _get_client():
    """Lazy-init Supabase client on first use."""
    global _client
    if _client is not None:
        return _client

    url = os.environ.get("CULINARY_SUPABASE_URL", "").strip()
    key = os.environ.get("CULINARY_SUPABASE_KEY", "").strip()

    if not url or not key:
        raise RuntimeError(
            "CulinaryOS Supabase credentials not configured. "
            "Set CULINARY_SUPABASE_URL and CULINARY_SUPABASE_KEY in .env"
        )

    try:
        from supabase import create_client
        _client = create_client(url, key)
    except ImportError:
        raise RuntimeError(
            "supabase-py not installed. Run: pip install supabase"
        )

    return _client


# ── Helpers ──────────────────────────────────────────────────────────────────


def _text(text: str) -> list[TextContent]:
    return [TextContent(type="text", text=text)]


def _json(data: Any) -> list[TextContent]:
    return _text(json.dumps(data, indent=2, default=str))


def _safe_run(fn):
    """Run a Supabase call and return (data, error_string_or_None)."""
    try:
        result = fn()
        return result.data, None
    except Exception as exc:
        return None, str(exc)


# ── Tool definitions ──────────────────────────────────────────────────────────


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        # ── Recipes ────────────────────────────────────────────────────────
        Tool(
            name="culinary_recipes",
            description=(
                "Search, retrieve, create, or update recipes in CulinaryOS. "
                "Use action=list to browse, action=get to fetch one by ID, "
                "action=search to find by keyword, action=create to add a new recipe, "
                "or action=update to modify an existing recipe."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["list", "get", "search", "create", "update"],
                        "description": "Operation to perform",
                    },
                    "id": {"type": "string", "description": "Recipe UUID (get/update)"},
                    "query": {"type": "string", "description": "Search keyword (search)"},
                    "limit": {"type": "integer", "description": "Max results (list/search, default 20)"},
                    "data": {
                        "type": "object",
                        "description": (
                            "Recipe fields for create/update. "
                            "Keys: name, description, instructions, prep_time_minutes, "
                            "cook_time_minutes, servings, category, cuisine, is_public"
                        ),
                    },
                },
                "required": ["action"],
            },
        ),
        # ── Ingredients ────────────────────────────────────────────────────
        Tool(
            name="culinary_ingredients",
            description=(
                "Manage ingredients in CulinaryOS. "
                "action=list returns all ingredients; action=get fetches one by ID; "
                "action=search finds by name; action=create adds a new ingredient."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["list", "get", "search", "create"],
                        "description": "Operation to perform",
                    },
                    "id": {"type": "string", "description": "Ingredient UUID (get)"},
                    "query": {"type": "string", "description": "Name filter (search)"},
                    "limit": {"type": "integer", "description": "Max results (default 50)"},
                    "data": {
                        "type": "object",
                        "description": "Ingredient fields: name, unit, calories_per_unit, category",
                    },
                },
                "required": ["action"],
            },
        ),
        # ── Menus ──────────────────────────────────────────────────────────
        Tool(
            name="culinary_menus",
            description=(
                "Manage kitchen menus in CulinaryOS. "
                "action=list returns all menus; action=get fetches one by ID; "
                "action=create adds a new menu; action=add_recipe adds a recipe to a menu."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["list", "get", "create", "add_recipe"],
                        "description": "Operation to perform",
                    },
                    "id": {"type": "string", "description": "Menu UUID (get/add_recipe)"},
                    "recipe_id": {"type": "string", "description": "Recipe UUID to add to menu (add_recipe)"},
                    "data": {
                        "type": "object",
                        "description": "Menu fields: name, description, date, meal_type",
                    },
                },
                "required": ["action"],
            },
        ),
        # ── Kitchen Stats ──────────────────────────────────────────────────
        Tool(
            name="culinary_stats",
            description=(
                "Get CulinaryOS kitchen statistics and summaries: "
                "total recipes, ingredients, menus, recent activity, and top categories."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
    ]


# ── Tool handler ──────────────────────────────────────────────────────────────


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        client = _get_client()
    except RuntimeError as exc:
        return _text(f"Error: {exc}")

    # ── culinary_recipes ────────────────────────────────────────────────────
    if name == "culinary_recipes":
        action = arguments.get("action", "")
        limit = int(arguments.get("limit", 20))

        if action == "list":
            data, err = _safe_run(
                lambda: client.table("recipes").select("*").limit(limit).execute()
            )
            if err:
                return _text(f"Error listing recipes: {err}")
            return _json({"count": len(data), "recipes": data})

        elif action == "get":
            recipe_id = arguments.get("id", "")
            if not recipe_id:
                return _text("Error: id required for get")
            data, err = _safe_run(
                lambda: client.table("recipes").select("*").eq("id", recipe_id).single().execute()
            )
            if err:
                return _text(f"Error fetching recipe: {err}")
            return _json(data)

        elif action == "search":
            query = arguments.get("query", "")
            if not query:
                return _text("Error: query required for search")
            data, err = _safe_run(
                lambda: client.table("recipes")
                .select("*")
                .ilike("name", f"%{query}%")
                .limit(limit)
                .execute()
            )
            if err:
                return _text(f"Error searching recipes: {err}")
            return _json({"count": len(data), "recipes": data})

        elif action == "create":
            payload = arguments.get("data", {})
            if not payload.get("name"):
                return _text("Error: data.name is required for create")
            data, err = _safe_run(
                lambda: client.table("recipes").insert(payload).execute()
            )
            if err:
                return _text(f"Error creating recipe: {err}")
            return _text(f"Recipe created: {payload['name']} (id: {data[0]['id'] if data else 'unknown'})")

        elif action == "update":
            recipe_id = arguments.get("id", "")
            payload = arguments.get("data", {})
            if not recipe_id:
                return _text("Error: id required for update")
            if not payload:
                return _text("Error: data required for update")
            data, err = _safe_run(
                lambda: client.table("recipes").update(payload).eq("id", recipe_id).execute()
            )
            if err:
                return _text(f"Error updating recipe: {err}")
            return _text(f"Recipe {recipe_id} updated successfully")

        else:
            return _text(f"Unknown action '{action}' for culinary_recipes")

    # ── culinary_ingredients ────────────────────────────────────────────────
    elif name == "culinary_ingredients":
        action = arguments.get("action", "")
        limit = int(arguments.get("limit", 50))

        if action == "list":
            data, err = _safe_run(
                lambda: client.table("ingredients").select("*").limit(limit).execute()
            )
            if err:
                return _text(f"Error listing ingredients: {err}")
            return _json({"count": len(data), "ingredients": data})

        elif action == "get":
            ingredient_id = arguments.get("id", "")
            if not ingredient_id:
                return _text("Error: id required for get")
            data, err = _safe_run(
                lambda: client.table("ingredients").select("*").eq("id", ingredient_id).single().execute()
            )
            if err:
                return _text(f"Error fetching ingredient: {err}")
            return _json(data)

        elif action == "search":
            query = arguments.get("query", "")
            if not query:
                return _text("Error: query required for search")
            data, err = _safe_run(
                lambda: client.table("ingredients")
                .select("*")
                .ilike("name", f"%{query}%")
                .limit(limit)
                .execute()
            )
            if err:
                return _text(f"Error searching ingredients: {err}")
            return _json({"count": len(data), "ingredients": data})

        elif action == "create":
            payload = arguments.get("data", {})
            if not payload.get("name"):
                return _text("Error: data.name is required for create")
            data, err = _safe_run(
                lambda: client.table("ingredients").insert(payload).execute()
            )
            if err:
                return _text(f"Error creating ingredient: {err}")
            return _text(f"Ingredient created: {payload['name']}")

        else:
            return _text(f"Unknown action '{action}' for culinary_ingredients")

    # ── culinary_menus ──────────────────────────────────────────────────────
    elif name == "culinary_menus":
        action = arguments.get("action", "")

        if action == "list":
            data, err = _safe_run(
                lambda: client.table("menus").select("*").order("created_at", desc=True).limit(20).execute()
            )
            if err:
                return _text(f"Error listing menus: {err}")
            return _json({"count": len(data), "menus": data})

        elif action == "get":
            menu_id = arguments.get("id", "")
            if not menu_id:
                return _text("Error: id required for get")
            data, err = _safe_run(
                lambda: client.table("menus").select("*, menu_recipes(*, recipes(*))").eq("id", menu_id).single().execute()
            )
            if err:
                return _text(f"Error fetching menu: {err}")
            return _json(data)

        elif action == "create":
            payload = arguments.get("data", {})
            if not payload.get("name"):
                return _text("Error: data.name is required for create")
            data, err = _safe_run(
                lambda: client.table("menus").insert(payload).execute()
            )
            if err:
                return _text(f"Error creating menu: {err}")
            return _text(f"Menu created: {payload['name']} (id: {data[0]['id'] if data else 'unknown'})")

        elif action == "add_recipe":
            menu_id = arguments.get("id", "")
            recipe_id = arguments.get("recipe_id", "")
            if not menu_id or not recipe_id:
                return _text("Error: id and recipe_id required for add_recipe")
            data, err = _safe_run(
                lambda: client.table("menu_recipes").insert({"menu_id": menu_id, "recipe_id": recipe_id}).execute()
            )
            if err:
                return _text(f"Error adding recipe to menu: {err}")
            return _text(f"Recipe {recipe_id} added to menu {menu_id}")

        else:
            return _text(f"Unknown action '{action}' for culinary_menus")

    # ── culinary_stats ──────────────────────────────────────────────────────
    elif name == "culinary_stats":
        stats = {}

        recipe_data, _ = _safe_run(lambda: client.table("recipes").select("id", count="exact").execute())
        ingredient_data, _ = _safe_run(lambda: client.table("ingredients").select("id", count="exact").execute())
        menu_data, _ = _safe_run(lambda: client.table("menus").select("id", count="exact").execute())
        recent_data, _ = _safe_run(
            lambda: client.table("recipes")
            .select("name, created_at")
            .order("created_at", desc=True)
            .limit(5)
            .execute()
        )

        stats["total_recipes"] = len(recipe_data) if recipe_data else 0
        stats["total_ingredients"] = len(ingredient_data) if ingredient_data else 0
        stats["total_menus"] = len(menu_data) if menu_data else 0
        stats["recent_recipes"] = [
            {"name": r["name"], "created_at": r["created_at"]}
            for r in (recent_data or [])
        ]

        return _json(stats)

    else:
        return _text(f"Unknown tool: {name}")


# ── Entry point ───────────────────────────────────────────────────────────────


async def run():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(run())
