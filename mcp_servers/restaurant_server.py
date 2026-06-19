"""
restaurant_server.py

MCP server exposing RestRevive-AI tools to the ShadowRealm agent.
Allows the agent to query and manage restaurant operations, staff,
orders, inventory, and analytics via the RestRevive-AI Supabase backend.

Requires environment variables:
    RESTAURANT_SUPABASE_URL   — Supabase project URL
    RESTAURANT_SUPABASE_KEY   — Supabase anon/service key
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

server = Server("restaurant")

_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    url = os.environ.get("RESTAURANT_SUPABASE_URL", "").strip()
    key = os.environ.get("RESTAURANT_SUPABASE_KEY", "").strip()
    if not url or not key:
        raise RuntimeError(
            "RestRevive-AI Supabase credentials not configured. "
            "Set RESTAURANT_SUPABASE_URL and RESTAURANT_SUPABASE_KEY in .env"
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
            name="restaurant_orders",
            description=(
                "Manage restaurant orders in RestRevive-AI. "
                "action=list returns recent orders; action=get fetches one by ID; "
                "action=create adds a new order; action=update_status changes order status."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["list", "get", "create", "update_status"],
                    },
                    "id": {"type": "string", "description": "Order UUID (get/update_status)"},
                    "status": {
                        "type": "string",
                        "enum": ["pending", "preparing", "ready", "delivered", "cancelled"],
                        "description": "New order status (update_status)",
                    },
                    "limit": {"type": "integer", "description": "Max results (list, default 20)"},
                    "data": {
                        "type": "object",
                        "description": "Order fields: table_number, items, total_amount, notes",
                    },
                },
                "required": ["action"],
            },
        ),
        Tool(
            name="restaurant_inventory",
            description=(
                "Manage restaurant inventory in RestRevive-AI. "
                "action=list returns all items; action=get fetches one by ID; "
                "action=low_stock returns items below threshold; "
                "action=update_quantity adjusts stock for an item."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["list", "get", "low_stock", "update_quantity"],
                    },
                    "id": {"type": "string", "description": "Inventory item UUID"},
                    "quantity": {"type": "number", "description": "New quantity (update_quantity)"},
                    "threshold": {"type": "number", "description": "Low stock threshold (low_stock, default 10)"},
                    "limit": {"type": "integer", "description": "Max results (default 50)"},
                },
                "required": ["action"],
            },
        ),
        Tool(
            name="restaurant_staff",
            description=(
                "Manage restaurant staff in RestRevive-AI. "
                "action=list returns all staff; action=get fetches one by ID; "
                "action=schedule returns upcoming shifts."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["list", "get", "schedule"],
                    },
                    "id": {"type": "string", "description": "Staff member UUID"},
                    "limit": {"type": "integer", "description": "Max results (default 20)"},
                },
                "required": ["action"],
            },
        ),
        Tool(
            name="restaurant_analytics",
            description=(
                "Get RestRevive-AI restaurant analytics: "
                "total orders, revenue, order status breakdown by time period."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "enum": ["today", "week", "month"],
                        "description": "Time period for analytics (default: today)",
                    },
                },
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

    if name == "restaurant_orders":
        action = arguments.get("action", "")
        limit = int(arguments.get("limit", 20))

        if action == "list":
            data, err = _safe_run(
                lambda: client.table("orders").select("*").order("created_at", desc=True).limit(limit).execute()
            )
            if err:
                return _text(f"Error listing orders: {err}")
            return _json({"count": len(data), "orders": data})

        elif action == "get":
            order_id = arguments.get("id", "")
            if not order_id:
                return _text("Error: id required for get")
            data, err = _safe_run(
                lambda: client.table("orders").select("*").eq("id", order_id).single().execute()
            )
            if err:
                return _text(f"Error fetching order: {err}")
            return _json(data)

        elif action == "create":
            payload = arguments.get("data", {})
            if not payload:
                return _text("Error: data required for create")
            data, err = _safe_run(
                lambda: client.table("orders").insert(payload).execute()
            )
            if err:
                return _text(f"Error creating order: {err}")
            return _text(f"Order created (id: {data[0]['id'] if data else 'unknown'})")

        elif action == "update_status":
            order_id = arguments.get("id", "")
            status = arguments.get("status", "")
            if not order_id or not status:
                return _text("Error: id and status required for update_status")
            data, err = _safe_run(
                lambda: client.table("orders").update({"status": status}).eq("id", order_id).execute()
            )
            if err:
                return _text(f"Error updating order status: {err}")
            return _text(f"Order {order_id} status updated to '{status}'")

        else:
            return _text(f"Unknown action '{action}' for restaurant_orders")

    elif name == "restaurant_inventory":
        action = arguments.get("action", "")
        limit = int(arguments.get("limit", 50))

        if action == "list":
            data, err = _safe_run(
                lambda: client.table("inventory").select("*").limit(limit).execute()
            )
            if err:
                return _text(f"Error listing inventory: {err}")
            return _json({"count": len(data), "inventory": data})

        elif action == "get":
            item_id = arguments.get("id", "")
            if not item_id:
                return _text("Error: id required for get")
            data, err = _safe_run(
                lambda: client.table("inventory").select("*").eq("id", item_id).single().execute()
            )
            if err:
                return _text(f"Error fetching inventory item: {err}")
            return _json(data)

        elif action == "low_stock":
            threshold = float(arguments.get("threshold", 10))
            data, err = _safe_run(
                lambda: client.table("inventory").select("*").lt("quantity", threshold).order("quantity").execute()
            )
            if err:
                return _text(f"Error fetching low stock: {err}")
            if not data:
                return _text(f"No items below threshold of {threshold}.")
            return _json({"count": len(data), "low_stock_items": data})

        elif action == "update_quantity":
            item_id = arguments.get("id", "")
            quantity = arguments.get("quantity")
            if not item_id or quantity is None:
                return _text("Error: id and quantity required for update_quantity")
            data, err = _safe_run(
                lambda: client.table("inventory").update({"quantity": quantity}).eq("id", item_id).execute()
            )
            if err:
                return _text(f"Error updating quantity: {err}")
            return _text(f"Inventory item {item_id} quantity updated to {quantity}")

        else:
            return _text(f"Unknown action '{action}' for restaurant_inventory")

    elif name == "restaurant_staff":
        action = arguments.get("action", "")
        limit = int(arguments.get("limit", 20))

        if action == "list":
            data, err = _safe_run(
                lambda: client.table("staff").select("*").limit(limit).execute()
            )
            if err:
                return _text(f"Error listing staff: {err}")
            return _json({"count": len(data), "staff": data})

        elif action == "get":
            staff_id = arguments.get("id", "")
            if not staff_id:
                return _text("Error: id required for get")
            data, err = _safe_run(
                lambda: client.table("staff").select("*").eq("id", staff_id).single().execute()
            )
            if err:
                return _text(f"Error fetching staff member: {err}")
            return _json(data)

        elif action == "schedule":
            data, err = _safe_run(
                lambda: client.table("shifts").select("*, staff(name, role)").gte("start_time", "now()").order("start_time").limit(limit).execute()
            )
            if err:
                return _text(f"Error fetching schedule: {err}")
            return _json({"count": len(data), "upcoming_shifts": data})

        else:
            return _text(f"Unknown action '{action}' for restaurant_staff")

    elif name == "restaurant_analytics":
        from datetime import datetime, timedelta
        period = arguments.get("period", "today")
        now = datetime.utcnow()
        if period == "today":
            since = now.replace(hour=0, minute=0, second=0).isoformat()
        elif period == "week":
            since = (now - timedelta(days=7)).isoformat()
        elif period == "month":
            since = (now - timedelta(days=30)).isoformat()
        else:
            since = now.replace(hour=0, minute=0, second=0).isoformat()

        orders_data, _ = _safe_run(
            lambda: client.table("orders").select("id, total_amount, status, created_at").gte("created_at", since).execute()
        )
        analytics = {"period": period, "since": since}
        if orders_data:
            analytics["total_orders"] = len(orders_data)
            analytics["total_revenue"] = sum(float(o.get("total_amount") or 0) for o in orders_data)
            status_counts = {}
            for o in orders_data:
                s = o.get("status", "unknown")
                status_counts[s] = status_counts.get(s, 0) + 1
            analytics["orders_by_status"] = status_counts
        else:
            analytics["total_orders"] = 0
            analytics["total_revenue"] = 0.0
        return _json(analytics)

    else:
        return _text(f"Unknown tool: {name}")


async def run():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(run())
